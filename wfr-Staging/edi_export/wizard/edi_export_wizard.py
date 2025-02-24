import logging

from odoo import api, fields, models

from lxml import etree as ET

from odoo.tools import formatLang
from odoo.tools.convert import safe_eval

_logger = logging.getLogger(__name__)


class EdiExportWizard(models.TransientModel):
    _name = 'edi.export.wizard'
    _description = 'Export Wizard'

    mapping_id = fields.Many2one(comodel_name='edi.mapping')

    def action_do_export(self, record):
        self.ensure_one()
        root = self.mapping_id.get_root_line()
        ET.register_namespace('xmlns', 'http://www.spscommerce.com/RSX')
        xml = ET.Element(root.tag)
        self._handle_children(xml, root, record)
        return ET.tostring(xml, pretty_print=True)

    @api.model
    def _handle_children(self, node, line, record):
        for child in line.child_ids:
            child_node = ET.SubElement(node, child.tag)
            if child_node.tag == "PackLevelType":
                debug_test = "TEMP"
            if child.odoo_field_id:
                if child.x_to_many:
                    domain = safe_eval(child.export_domain or '[]')
                    for child_record in record.mapped(child.odoo_field_id.name).filtered_domain(domain):
                        self._handle_children(child_node, child, child_record)
                        child_node = ET.SubElement(node, child.tag)
                else:
                    field = record[child.odoo_field_id.name]
                    if not isinstance(field, models.BaseModel):
                        if child.odoo_field_id.ttype != 'monetary' and (field or child.odoo_field_id.ttype == 'boolean'):
                            child_node.text = str(field)
                        elif field:
                            currency_field_name = self.env[child.odoo_model_id.model].fields_get()[child.odoo_field_id.name]['currency_field']
                            currency = record[currency_field_name]
                            child_node.text = formatLang(self.env, field, digits=currency.decimal_places)
                    elif field and child.is_search_field and child.odoo_search_field_id:
                        try:
                            text_data = field[child.odoo_search_field_id.name]
                        except Exception as e:
                            text_data = ""
                        child_node.text = text_data
            elif child.export_server_action_id:
                action = child.export_server_action_id.with_context(active_model=child.odoo_model_id.model, active_id=record.id, active_ids=[], is_edi_export=True)
                value = action.run()
                child_node.text = str(value)
            elif child.export_map_to_multiple:
                self._handle_map_to_multiple(node, child, record)
            elif child.export_static_value:
                child_node.text = child.export_static_value
            elif child.export_relative_date:
                child_node.text = child._get_formatted_date()
            else:
                self._handle_children(child_node, child, record)

            if len(child_node) == 0 and not child_node.text:
                node.remove(child_node)

    @api.model
    def _handle_map_to_multiple(self, node, line, record):
        for map_field in line.export_map_to_multiple_ids:
            child_node = ET.SubElement(node, line.tag)
            field = record[map_field.odoo_field_id.name]
            self._handle_children(child_node, line, field)
            sentinel_parent = child_node
            if line != line.export_map_to_multiple_sentinel_tag.parent_id:
                path = line.get_path(line.export_map_to_multiple_sentinel_tag.parent_id)
                sentinel_parent = child_node.find(path)
            sentinel = ET.SubElement(sentinel_parent, line.export_map_to_multiple_sentinel_tag.tag)
            sentinel.text = map_field.value
            _logger.info('%s: %s' % (sentinel.tag, sentinel.text))
