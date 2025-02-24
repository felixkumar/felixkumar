import logging

from odoo import fields, models, _, Command

from lxml import etree as ET

from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)

PARTNER_TYPE = {'ST': 'delivery', 'BT': 'invoice'}


class DuplicateXmlRecord(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.duplicate_value = kwargs.get('value')


class EdiImport(models.TransientModel):
    _name = 'edi.import'
    _description = 'Import Wizard'

    xml_doc = fields.Char(string='Xml Doc')
    mapping_id = fields.Many2one(string='EDI Mapping', comodel_name='edi.mapping')
    trading_partnerid = fields.Char(string='Trading Partner ID')

    def action_import(self):
        self.ensure_one()
        root_line = self.mapping_id.mapping_line_ids.filtered_domain([('parent_id', '=', False)])
        xml_records = ET.fromstring(bytes(self.xml_doc, 'utf-8'))
        nsmap = xml_records.nsmap
        if not root_line.odoo_model_id:
            root_line = root_line.child_ids[:1]
            if xml_records.tag != root_line.tag:
                xml_records = xml_records.findall(root_line.tag, namespaces=nsmap)
            else:
                xml_records = [xml_records]
        record_vals = []
        for xml_record in xml_records:
            try:
                record_vals.append(self._parse_xml_record(xml_record, root_line, xml_record, nsmap=nsmap))
            except DuplicateXmlRecord as dup:
                self.env['edi.log.message'].log(self.mapping_id.sync_action_id, 'info', 'duplicate record found, with value %s' % dup.duplicate_value)
                return True
            except Exception as exception:
                self.env['edi.log.message'].log(self.mapping_id.sync_action_id, 'error', str(exception))
                raise exception
        if root_line.odoo_model_id.model and hasattr(self.env[root_line.odoo_model_id.model], 'company_id'):
            for rec in record_vals:
                rec.update({'company_id': self.mapping_id.sync_action_id.config_id.company_id.id})
        self.env[root_line.odoo_model_id.model].with_context(is_edi=True).with_company(self.mapping_id.sync_action_id.config_id.company_id.id).create(record_vals)
        return True

    def _parse_xml_record(self, xml_record, line, root, nsmap=None):
        res = {}
        unmapped_fields = []
        if xml_record is not None:
            for child in line.child_ids:
                if child.skip_if_matches_existing_record:
                    skip_check = False
                    for override in child.skip_if_matches_skip_override_line_ids:
                        comparison_value = self._get_value_from_closest_match(xml_record, child, override.child_id)
                        if override.comparison_type == '=':
                            skip_check |= override.skip_if_value == comparison_value
                        else:
                            skip_check |= override.skip_if_value != comparison_value
                    xml_value = xml_record.find(child.tag)
                    if not skip_check and xml_value and self.env[child.odoo_model_id.model].search([(child.odoo_field_id.name, '=', xml_value.text)]):
                        raise DuplicateXmlRecord(value=xml_value.text)
                if child.log_subfields:
                    cur_val = res.get(child.import_log_sub_fields_field_id.name, '')
                    new_vals = '\n'.join(self._log_node(node, child, nsmap=nsmap) for node in xml_record.findall(child.tag, namespaces=nsmap))
                    res[child.import_log_sub_fields_field_id.name] = '%s\n%s' % (cur_val, new_vals) if cur_val else new_vals
                if child.odoo_field_id:
                    child_tag_elements = xml_record.findall(child.tag, namespaces=nsmap)
                    if child_tag_elements:
                        res[child.odoo_field_id.name] = self._handle_single_field(child_tag_elements, child, root, nsmap=nsmap)

                    else:
                        unmapped_fields.append({
                            'description': f"Missing expected fields in: {child.tag}",
                            'edi_data': str(xml_record)
                        })
                elif child.is_map_to_multiple_fields:
                    mapped_res = self._handle_map_to_multiple(xml_record.findall(child.tag, namespaces=nsmap), child,root, nsmap=nsmap)
                    # res.update(self._handle_map_to_multiple(xml_record.findall(child.tag, namespaces=nsmap), child, root, nsmap=nsmap))
                    if mapped_res:
                        res.update(mapped_res)
                    else:
                        unmapped_fields.append({
                            'description': f"Missing expected fields in: {child.tag}",
                            'edi_data': str(xml_record)
                        })

                elif child.custom_method_name and child.custom_method_returns_dict:
                    mapped_res = self._handle_custom_method(xml_record.find(child.tag, namespaces=nsmap), child, root,nsmap=nsmap)
                    # res.update(self._handle_custom_method(xml_record.find(child.tag, namespaces=nsmap), child, root, nsmap=nsmap))
                    if mapped_res:
                        res.update(mapped_res)
                    else:
                        unmapped_fields.append({
                            'description': f"Missing expected fields in: {child.tag}",
                            'edi_data': str(xml_record)
                        })
                else:
                    # res.update(self._parse_xml_record(xml_record.find(child.tag, namespaces=nsmap), child, root, nsmap=nsmap))
                    mapped_res = self._parse_xml_record(xml_record.find(child.tag, namespaces=nsmap), child, root,nsmap=nsmap)
                    if mapped_res:
                        res.update(mapped_res)
                    else:
                        unmapped_fields.append({
                            'description': f"Missing expected fields in: {child.tag}",
                            'edi_data': str(xml_record)
                        })
        elif line.xsd_line_id.required:
            raise ValidationError(_('Required tag %s not found' % line.tag))
        if unmapped_fields:
            for unmapped in unmapped_fields:
                self.env['edi.error.log'].create({
                    'type':'unmapped_fields',
                    'timestamp': fields.Datetime.now(),
                    'description': unmapped['description'],
                    'edi_data': unmapped['edi_data']
                })
        if line.post_process_method_name:
            res = getattr(self.env[line.odoo_field_id.relation], line.post_process_method_name)(res, nsmap=nsmap)
        return res

    def _handle_single_field(self, nodes, line, root, nsmap=None):
        if line.x_to_many:
            res = [self._handle_x_to_many_record(xml_record, line, nsmap=nsmap) for xml_record in nodes]
        else:
            if len(nodes) != 1:
                raise ValidationError(_('expected one instance of tag, got %d' % len(nodes)))
            node = nodes[0]
            res = None
            if line.is_search_field:
                res = self._search_record(node, line, nsmap=nsmap).id
            if line.can_create_values and not res:
                new_record = self._create_record(node, line, root, nsmap=nsmap)
                res = new_record.id if new_record else None
            if line.is_custom_method and not res:
                    res = self._handle_custom_method(node, line, root, nsmap=nsmap)
            if not res:
                res = line.parse(node.text)
        if line.allowed_value_ids and not res in line.allowed_value_ids.mapped('value'):
            if line.default:
                res = line.parse(line.default)
            else:
                raise ValidationError(_('Value %s found, but not allowed' % res))
        return res

    def _handle_custom_method(self, node, line, root, nsmap=None):
        search_root = node if node is not None else root
        additional_fields = {field.tag: self._get_value_from_closest_match(search_root, line, field) for field in line.custom_method_field_ids}
        model = line.odoo_field_id.relation if line.odoo_field_id.relation else line.odoo_model_id.model
        return getattr(self.env[model], line.custom_method_name)(node, additional_fields, nsmap=nsmap)

    def _handle_x_to_many_record(self, record, line, nsmap=None):
        found_record = None
        if line.is_search_field:
            found_record = self._search_record(record, line, nsmap=nsmap)
        if found_record:
            return Command.link(found_record.id)
        else:
            new_root = record
            res = self._get_create_vals(record, line, new_root, nsmap=nsmap)
            return Command.create(res)

    def _handle_map_to_multiple(self, nodes, line, root, nsmap=None):
        res = {}
        mappings = {
            mapping.expected_value: mapping.odoo_field_id.name for mapping in line.sentinel_value_ids
        }
        for child in nodes:
            mapping_value = child.find(line.sentinel_child_id.tag, namespaces=nsmap)
            if line.custom_method_name:
                model = line.odoo_field_id.relation or line.odoo_model_id.model
                additional_fields = {field.tag: self._get_value_from_closest_match(child, line, field) for field in line.custom_method_field_ids}
                value = getattr(self.env[model], line.custom_method_name)(child, additional_fields, nsmap=nsmap)
            elif line.odoo_sentinel_model_id:
                value = self._search_record(child, line, nsmap=nsmap)
                if not value and line.can_create_values:
                    value = self._create_record(child, line, root, nsmap=nsmap)
            else:
                value = line.parse(child.text)
            if mapping_value.text in mappings and value:
                res[mappings[mapping_value.text]] = value.id if isinstance(value, models.BaseModel) else value
        return res

    def _search_record(self, node, line, nsmap=None):
        domain = []
        search_lines = line.child_ids.filtered('is_search_field') or line
        for search_line in search_lines:
            domain_node = node if line == search_line else node.find(search_line.tag, namespaces=nsmap)
            value = search_line.parse(domain_node.text) if domain_node is not None else False
            domain.append((search_line.odoo_search_field_id.name, '=', value))
        if line.use_for_creation and line.creation_field_has_search_dependency:
            for other_field_line in line.creation_search_dependency_ids:
                field = other_field_line.odoo_field_id
                other_line = other_field_line.child_id
                value = self._get_value_from_closest_match(node, line, other_line, nsmap=nsmap)
                if value:
                    domain.append((field.name, '=', value))
        model = line.odoo_search_model_id or line.odoo_sentinel_model_id

        result = self.env[model.model].search(domain)
        if not result and line.default:
            result = self.env[model.model].search([(line.odoo_search_field_id.name, '=', search_lines.parse(node.text))])
        return result

    def _create_record(self, node, line, root, nsmap=None):
        vals = self._get_create_vals(node, line, root, nsmap=nsmap)
        if line.odoo_model_id.model == 'res.partner':
            vals.update({'outbound_edi_asn': True})
        return self.env[line.odoo_model_id.model].create(vals)

    def _get_create_vals(self, record, line, root, nsmap=None):
        values = {}
        create_lines = line.get_creation_lines() or line
        for create_line in create_lines:
            field_val = record.find('.//%s' % create_line.tag, namespaces=nsmap)
            if field_val is None:
                field_val = record if record.tag == create_line.tag else None
            # if field_val is None:
            #     field_val = record
            if field_val is not None and not create_line.is_custom_method:
                val = create_line.parse(field_val.text)
                if create_line.creation_is_search:
                    domain = [(create_line.creation_search_field_id.name, '=', val)]
                    for dependency in create_line.creation_search_dependency_ids:
                        ancestor_node = self._get_value_from_closest_match(record, line, dependency.child_id, nsmap=nsmap)
                        domain.append((dependency.odoo_field_id.name, '=', ancestor_node.text))
                    val = self.env[create_line.creation_search_model_id.model].search(domain).id
                if create_line.post_process_method_name:
                    val = getattr(self.env[line.odoo_field_id.relation], create_line.post_process_method_name)(val, xml_val=field_val, nsmap=nsmap)
                if create_line.odoo_field_id.name == 'type' and val in PARTNER_TYPE.keys():
                    val = PARTNER_TYPE.get(val)
                values[create_line.odoo_field_id.name] = val
            elif create_line.is_custom_method:
                custom_method_res = self._handle_custom_method(field_val, create_line, root, nsmap=nsmap)
                if create_line.custom_method_returns_dict:
                    values.update(custom_method_res)
                else:
                    values[create_line.odoo_field_id.name] = custom_method_res
            elif create_line.post_process_method_name:
                values[create_line.odoo_field_id.name] = getattr(self.env[line.odoo_field_id.relation], create_line.post_process_method_name)(field_val, xml_val=field_val, nsmap=nsmap)
            elif create_line.xsd_line_id.required:
                # raise ValidationError(_('Required Tag %s Not Found' % create_line.tag))
                raise ValidationError('Required Tag Not Found')
        if line.store_trading_partner_field_id:
            values[line.store_trading_partner_field_id.name] = self.trading_partnerid
        return values

    def _get_value_from_closest_match(self, node, line, target, nsmap=None):
        ancestor_node = node
        ancestor_line = line
        while ancestor_line and not ancestor_line.is_ancestor_of(target):
            ancestor_line = ancestor_line.parent_id
            ancestor_node = ancestor_node.find('..')
        if ancestor_node is not None:
            return target.parse(ancestor_node.find('.//%s' % target.tag, namespaces=nsmap))
        else:
            raise ValidationError(_('could not find common ancestor'))

    def _log_node(self, node, line, nsmap=None):
        log_line_vals = []
        log_lines = line.child_ids.filtered('is_import_logged_field') or line
        for log_line in log_lines:
            log_node = node.find(log_line.tag, namespaces=nsmap)
            if log_node is not None:
                value = log_line.parse(log_node.text)
                if log_line.import_logged_field_mappings:
                    mapping_line = log_line.import_logged_field_mappings.filtered_domain([('xml_value', '=', value)]) or \
                                   log_line.import_logged_field_mappings.filtered_domain([('xml_value', '=', '')])
                    if mapping_line:
                        value = mapping_line.output_value
                log_line_vals.append('%s: %s' % (log_line.import_logged_field_label, value))
        return ', '.join(log_line_vals)
