import json
from datetime import date, datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EdiMapping(models.Model):
    _inherit = 'edi.mapping'

    def _configure_export_from_json(self, fname):
        with open(fname, 'r') as file:
            config = json.load(file)
            mapping = self._get_mapping_to_configure(config)
            mapping._configure_export_from_dict(config)
        return self

    def _configure_export_from_dict(self, config):
        self.ensure_one()
        Models = self.env['ir.model']
        Fields = self.env['ir.model.fields']
        root = self.get_root_line()
        for config_line in config.get('config', []):
            path = config_line.get('path')
            element = root
            for tag in path.split('/')[1:]:
                element = element.child_ids.filtered_domain([('tag', '=', tag)])
            if not element:
                raise ValidationError(_('Could not find element at path %s' % path))
            if 'model' in config_line:
                element.odoo_model_id = Models.search([('model', '=', config_line['model'])])

            if 'field' in config_line:
                field = Fields.search([('model_id', '=', element.odoo_model_id.id), ('name', '=', config_line['field'])])
                if field:
                    element.odoo_field_id = field
                    element.export_domain = config_line.get('domain')
                else:
                    raise ValidationError(_('Could not find field %s on model %s' % (config_line['field'], element.odoo_model_id.model)))

                if 'search_field' in config_line:
                    element.is_search_field = True
                    element.odoo_search_field_id = Fields.search([('model_id', '=', element.odoo_search_model_id.id), ('name', '=', config_line['search_field'])])
            elif 'multimap' in config_line:
                multimap_config = config_line['multimap']
                element.export_map_to_multiple = True
                element.export_map_to_multiple_ids.unlink()
                element.export_map_to_multiple_sentinel_tag = element._follow_path(multimap_config['determining_tag'])
                element.export_map_to_multiple_odoo_model_id = Models.search([('model', '=', multimap_config['model'])])
                map_to_multiples = []
                for map_config_line in multimap_config.get('values', []):
                    field = Fields.search([('model_id', '=', element.odoo_model_id.id), ('name', '=', map_config_line['field'])])
                    if not field:  
                        field = Fields.search([('model_id', '=', element.export_map_to_multiple_odoo_model_id.id), ('name', '=', map_config_line['field'])])
                    
                    if field:
                        map_to_multiples.append({
                            'parent_id': element.id,
                            'value': map_config_line['value'],
                            'odoo_field_id': field.id
                        })
                    else:
                        raise ValidationError(_('Could not find field %s on model %s' % (map_config_line['field'], element.odoo_model_id.model)))
                self.env['edi.mapping.line.export.multifield'].create(map_to_multiples)

            if 'action' in config_line:
                element.export_call_server_action = True
                action = self.env.ref(config_line['action'])
                if action:
                    element.export_server_action_id = action
                else:
                    raise ValidationError(_('Could not find action with external id %s' % config_line['action']))

            element.export_static_value = config_line.get('static')
            element.export_float_zero = config_line.get('export_zero')

            element.export_relative_date = config_line.get('export_days_from_today') is not None
            element.export_relative_date_delta = config_line.get('export_days_from_today')
            element.export_relative_date_with_time = config_line.get('export_time')
            element.export_relative_date_is_document_id = config_line.get('export_date_format_document_id')

        
class EdiMappingLine(models.Model):
    _inherit = 'edi.mapping.line'

    export_map_to_multiple = fields.Boolean(string='Export should map to multiple fields')
    export_map_to_multiple_sentinel_tag = fields.Many2one(string='Tag Indicating the Type of the Field', comodel_name='edi.mapping.line')
    export_map_to_multiple_odoo_model_id = fields.Many2one(string='Model Of Subfields', comodel_name='ir.model')
    export_map_to_multiple_ids = fields.One2many(string='Field Map', comodel_name='edi.mapping.line.export.multifield', inverse_name='parent_id')

    export_domain = fields.Char(string='Domain on X2M Fields')

    export_call_server_action = fields.Boolean(string='Should Call Server Action to Get Value')
    export_server_action_id = fields.Many2one(string='Server Action to Call', comodel_name='ir.actions.server')

    export_static_value = fields.Char(string='Constant Value')

    export_float_zero = fields.Boolean(string='Export Zero Float Values')

    export_relative_date = fields.Boolean('Export Date Relative to Today')
    export_relative_date_delta = fields.Integer(string='Export Days From Today')
    export_relative_date_with_time = fields.Boolean(string='Include Time')
    export_relative_date_is_document_id = fields.Boolean(string='Date Export DocumentID Format')

    def unlink(self):
        self.export_map_to_multiple_ids.unlink()
        return super().unlink()

    def get_path(self, to):
        self.ensure_one()
        if self.is_ancestor_of(to):
            res = ''
            node = self
            while node != to:
                node = node.child_ids.filtered(lambda child: child.is_ancestor_of(to) or child == to)
                res += '/%s' % node.tag if res else node.tag
        else:
            res = '..'
            parent = self.parent_id
            while not parent.is_ancestor_of(to):
                res += '/..'
                parent = parent.parent_id
            res += '/%s' % parent.get_path(to)
        return res

    def _compute_odoo_model_id(self):
        for line in self:
            if line.parent_id.export_map_to_multiple_odoo_model_id:
                line.odoo_model_id = line.parent_id.export_map_to_multiple_odoo_model_id
            else:
                super(EdiMappingLine, line)._compute_odoo_model_id()

    def _get_formatted_date(self):
        self.ensure_one()
        if self.export_relative_date_with_time:
            relative_date = datetime.now() + timedelta(days=self.export_relative_date_delta)
            date_format = '%Y%m%d%H%M%S'
        else:
            relative_date = date.today() + timedelta(days=self.export_relative_date_delta)
            date_format = '%Y%m%d'
        if not self.export_relative_date_is_document_id:
            return relative_date.isoformat()
        else:
            return relative_date.strftime(date_format)

class EdiMappingLineExportMultifield(models.Model):
    _name = 'edi.mapping.line.export.multifield'
    _description = 'Multifield Configuration'
    
    parent_id = fields.Many2one(string='Parent Id', comodel_name='edi.mapping.line')
    value = fields.Char(string='Value')
    odoo_field_id = fields.Many2one(string='Field Providing the value', comodel_name='ir.model.fields')
