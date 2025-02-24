import json

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EdiMapping(models.Model):
    _inherit = 'edi.mapping'

    def _configure_import_from_json_file(self, fname):
        with open(fname, 'r') as file:
            config = json.load(file)
            mapping = self._get_mapping_to_configure(config)
            mapping._configure_import_from_dict(config)
        return self

    def _configure_import_from_dict(self, config):
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
            if config_line.get('clear', False):
                element.odoo_field_id = False
                element.odoo_model_id = False
                element.is_search_field = False
                element.odoo_search_field_id = False
                element.use_for_creation = False
                element.log_subfields = False
                element.import_log_sub_fields_field_id = False
                element.is_import_logged_field = False
                element.import_logged_field_label = False
                element.import_logged_field_mappings.unlink()
                element.skip_if_matches_existing_record = False
                element.skip_if_matches_skip_override_line_ids.unlink()
                element.is_custom_method = False
                element.custom_method_name = False
                element.custom_method_returns_dict = False
                element.custom_method_field_ids.unlink()
                element.creation_is_search = False
                element.creation_search_model_id = False
                element.creation_search_field_id = False
                element.creation_field_has_search_dependency = False
                element.post_process_method_name = False
                element.default = False

            element.can_create_values = config_line.get('create', False)
            if 'model' in config_line:
                element.odoo_model_id = Models.search([('model', '=', config_line['model'])])

            if 'field' in config_line:
                element.odoo_field_id = Fields.search([('model_id', '=', element.odoo_model_id.id), ('name', '=', config_line['field'])])
                if 'search_field' in config_line:
                    element.is_search_field = True
                    element.odoo_search_field_id = Fields.search([('model_id', '=', element.odoo_search_model_id.id), ('name', '=', config_line['search_field'])])
                if element.can_be_used_in_creation:
                    element.use_for_creation = 'exclude_from_creation' not in config_line
            else:
                element.odoo_field_id = False
                if 'multifield' in config_line:
                    element._configure_multifield(config_line['multifield'])

            if 'search' in config_line:
                element.is_search_field = True
                element.odoo_search_field_id = element.odoo_field_id
            elif 'search_field' not in config_line:
                element.is_search_field = False
                element.odoo_search_field_id = False

            if 'log_subfields' in config_line:
                element.log_subfields = True
                element.import_log_sub_fields_field_id = Fields.search([('model_id', '=', element.odoo_model_id.id), ('name', '=', config_line['log_subfields'])])
            else:
                element.log_subfields = False
                element.import_log_sub_fields_field_id = False

            if 'log' in config_line:
                element.is_import_logged_field = True
                element.import_logged_field_label = config_line.get('label', element.tag)
                element.import_logged_field_mappings.unlink()
                log_maps = []
                for log_map in config_line.get('log_map', []):
                    log_maps.append({
                        'parent_id': element.id,
                        'xml_value': log_map[0],
                        'output_value': log_map[1]
                    })
                self.env['edi.mapping.line.import.log.mapping'].create(log_maps)

            if 'skip' in config_line:
                element.skip_if_matches_existing_record = True
                element.skip_if_matches_skip_override_line_ids.unlink()
                overrides = []
                for skip_override in config_line.get('skip_overrides', []):
                    overrides.append({
                        'parent_id': element.id,
                        'child_id': element._follow_path(skip_override['path']).id,
                        'comparison_type': skip_override.get('comparison', '='),
                        'skip_if_value': skip_override['value']
                    })
                self.env['edi.mapping.line.import.skip.override'].create(overrides)

            if 'custom_method' in config_line:
                element.is_custom_method = True
                element.custom_method_name = config_line['custom_method']
                element.custom_method_returns_dict = config_line.get('custom_method_returns_dict', False)
                element.custom_method_field_ids = self.env['edi.mapping.line']
                for additional_arg in config_line.get('custom_method_args', []):
                    element.custom_method_field_ids |= element._follow_path(additional_arg)
                if element.can_be_used_in_creation:
                    element.use_for_creation = 'exclude_from_creation' not in config_line
            else:
                element.is_custom_method = False
                element.custom_method_name = ''
                element.custom_method_field_ids = self.env['edi.mapping.line']

            if 'allowed_values' in config_line:
                allowed_values = []
                for val in config_line['allowed_values']:
                    allowed_values.append({
                        'parent_id': element.id,
                        'value': val
                    })
                self.env['edi.mapping.line.import.allowed.value'].create(allowed_values)

            if 'create_search_field' in config_line:
                element.creation_is_search = True
                element.creation_search_model_id = self.env['ir.model'].search([('model', '=', config_line.get('create_search_model'))]) or element.odoo_field_id.relation
                element.creation_search_field_id = self.env['ir.model.fields'].search([('model_id', '=', element.creation_search_model_id.id), ('name', '=', config_line['create_search_field'])])
                element.creation_field_has_search_dependency = 'create_search_dependencies' in config_line
                dependencies = []
                for dependency in config_line.get('create_search_dependencies', []):
                    dependencies.append({
                        'parent_id': element.id,
                        'odoo_field_id': self.env['ir.model.fields'].search([('model_id', '=', element.creation_search_model_id.id), ('name', '=', dependency['field'])]).id,
                        'child_id': element._follow_path(dependency['value_tag']).id
                    })
                self.env['edi.mapping.line.import.create.dependency'].create(dependencies)

            element.post_process_method_name = config_line.get('post_process')
            element.default = config_line.get('default')

        return self


class EdiMappingLine(models.Model):
    _inherit = 'edi.mapping.line'

    can_create_values = fields.Boolean(string='Create New Records')
    store_trading_partner_field_id = fields.Many2one(string='Store Trading Partner in Odoo Field', comodel_name='ir.model.fields')

    skip_if_matches_existing_record = fields.Boolean(string='Skip Record If an Existing Record Matches')
    skip_if_matches_skip_override_line_ids = fields.One2many(string='Override Skip Configuration', comodel_name='edi.mapping.line.import.skip.override', inverse_name='parent_id',
                                                             help='Override skip check if any of the conditions are true')

    log_subfields = fields.Boolean(string='Should Log Subfields')
    import_log_sub_fields_field_id = fields.Many2one(string='Store List of Values in Text Field', comodel_name='ir.model.fields', help='If set, log all matches in a text field')
    can_log_field = fields.Boolean(string='Can Log Field', related='parent_id.log_subfields')
    is_import_logged_field = fields.Boolean(string='Subfield Should Be Logged')
    import_logged_field_label = fields.Char(string='Subfield Label')
    import_logged_field_mappings = fields.One2many(string='Log Value Mappings', comodel_name='edi.mapping.line.import.log.mapping', inverse_name='parent_id',
                                                   help='Mappings from edi values to human readable strings, leave XML Value blank to provide a default')

    is_search_field = fields.Boolean(string='Is Search Field')
    odoo_search_model_id = fields.Many2one(string='Search Model', comodel_name='ir.model', compute='_compute_odoo_search_model')
    odoo_search_field_id = fields.Many2one(string='Search Field', comodel_name='ir.model.fields')

    is_map_to_multiple_fields = fields.Boolean(string='Change Odoo Field Based on Subelement')
    odoo_sentinel_model_id = fields.Many2one(string='Odoo Model of Records for Subelement', comodel_name='ir.model')
    sentinel_search_all = fields.Boolean(string='Search For Existing Records on All Fields')
    sentinel_can_create_all = fields.Boolean(string='Can Create Records for All Instances')
    sentinel_child_id = fields.Many2one(string='Element To Determine Odoo Field', comodel_name='edi.mapping.line')
    sentinel_value_ids = fields.One2many(string='Odoo Field Configurations', comodel_name='edi.mapping.line.import.sentinel', inverse_name='parent_id', copy=True)

    can_be_used_in_creation = fields.Boolean(string='Is Possible Field of Odoo Model for Creation')
    use_for_creation = fields.Boolean(string='Provides a value for creation')
    creation_is_search = fields.Boolean(string='Search for Existing Database Record')
    creation_search_model_id = fields.Many2one(string='Search on Model', comodel_name='ir.model', compute='_compute_creation_search_model_id')
    creation_search_field_id = fields.Many2one(string='Search on Field', comodel_name='ir.model.fields')
    creation_field_has_search_dependency = fields.Boolean(string='Field has Search Dependency on Another Field')
    creation_search_dependency_ids = fields.One2many(string='Search Dependencies', comodel_name='edi.mapping.line.import.create.dependency', inverse_name='parent_id', copy=True)

    is_custom_method = fields.Boolean(string='Call Custom Method to Determine Value')
    custom_method_returns_dict = fields.Boolean(string='Custom Method Returns a Dictionary of Values')
    custom_method_name = fields.Char(string='Custom Method')
    custom_method_field_ids = fields.Many2many(string='Additional Fields to Pass Into Custom Method', comodel_name='edi.mapping.line',
                                              relation='custom_method_fields_relation', column1='parent_id', column2='child_id')

    post_process_method_name = fields.Char(string='Post Process Method')
    allowed_value_ids = fields.One2many(string='Allowed Values', comodel_name='edi.mapping.line.import.allowed.value', inverse_name='parent_id')
    default = fields.Char(string="Default Value", help="If a value is provided, it will be used in place of missing values, being parsed according to the field type")

    @api.constrains('sentinel_child_id')
    def _check_sentinel_child_id_is_child(self):
        for line in self:
            if line.sentinel_child_id.parent_id and line.sentinel_child_id.parent_id != line:
                raise ValidationError(_('Element determining odoo field must be a child of this element'))

    @api.depends('is_search_field', 'odoo_field_id')
    def _compute_odoo_search_model(self):
        for line in self:
            if line.parent_id.odoo_sentinel_model_id:
                model = line.parent_id.odoo_sentinel_model_id
            elif line.is_search_field and line.odoo_field_id:
                model_name = line.odoo_field_id.relation
                model = self.env['ir.model'].search([('model', '=', model_name)])
            else:
                model = False
            line.odoo_search_model_id = model

    @api.depends('parent_id.is_map_to_multiple_fields', 'parent_id.odoo_sentinel_model_id')
    def _compute_odoo_model_id(self):
        super()._compute_odoo_model_id()
        for line in self.filtered('parent_id.is_map_to_multiple_fields'):
            line.odoo_model_id = line.parent_id.odoo_sentinel_model_id

    @api.depends('odoo_field_id.relation')
    def _compute_creation_search_model_id(self):
        for line in self:
            line.creation_search_model_id = self.env['ir.model'].search([('model', '=', line.odoo_field_id.relation)])

    def write(self, vals):
        res = super().write(vals)
        if 'can_create_values' in vals:
            self._set_children_can_be_used_in_creation()
        return res

    def unlink(self):
        self.skip_if_matches_skip_override_line_ids.unlink()
        self.sentinel_value_ids.unlink()
        self.import_logged_field_mappings.unlink()
        self.creation_search_dependency_ids.unlink()
        self.allowed_value_ids.unlink()
        return super().unlink()

    def _set_children_can_be_used_in_creation(self):
        self.get_all_descendants().write({
            'can_be_used_in_creation': True
        })

    def copy(self, default=None):
        res = super().copy(default=default)
        default = {
            'parent_id': res.id,
        }
        for sentinel in self.sentinel_value_ids:
            sentinel.copy(default=default)
        for dependency in self.creation_search_dependency_ids:
            dependency.copy(default=default)
        return res

    def parse(self, value):
        self.ensure_one()
        type = self.odoo_field_id.ttype
        if type in ['float', 'monetary']:
            try:
                return float(value)
            except Exception as e:
                data_error = e
        if type == 'integer':
            return int(value)
        return value

    def _configure_multifield(self, multifield_config):
        self.ensure_one()
        self.sentinel_value_ids.unlink()
        determining_line = self.child_ids.filtered_domain([('tag', '=', multifield_config['determining_tag'])])
        values = multifield_config['values']
        self.is_map_to_multiple_fields = True
        if 'model' in multifield_config:
            self.odoo_sentinel_model_id = self.env['ir.model'].search([('model', '=', multifield_config['model'])])
        self.sentinel_child_id = determining_line
        self.sentinel_search_all = multifield_config.get('search', False)
        self.sentinel_can_create_all = multifield_config.get('create', False)
        sentinel_values = []
        for sentinel_value in values:
            field = sentinel_value['field']
            value = sentinel_value['value']
            can_create = self.sentinel_can_create_all or sentinel_value.get('create', False)
            search = self.sentinel_search_all or sentinel_value.get('search', False)
            sentinel_values.append({
                'parent_id': self.id,
                'expected_value': value,
                'odoo_field_id': self.env['ir.model.fields'].search([('model_id', '=', self.odoo_model_id.id), ('name', '=', field)]).id,
                'search_record': search,
                'can_create_record': can_create,
            })
        self.env['edi.mapping.line.import.sentinel'].create(sentinel_values)

    def get_creation_lines(self):
        def parent_is_odoo_field(line):
            return not line.parent_id.odoo_field_id

        self.ensure_one()
        return self.get_all_descendants(parent_is_odoo_field).filtered_domain([('use_for_creation', '=', True)])

class EdiMappingLineImportSkipOverride(models.Model):
    _name = 'edi.mapping.line.import.skip.override'
    _description = 'Override Skip Configuration'

    parent_id = fields.Many2one(string='Parent Mapping Line', comodel_name='edi.mapping.line')
    child_id = fields.Many2one(string='Sentinel Mapping Line', comodel_name='edi.mapping.line')
    comparison_type = fields.Selection(string='Comparison Type', selection=[('=', 'Equals'), ('!=', 'Does Not Equal')])
    skip_if_value = fields.Char(string='Override Check If Value Is')


class EdiMappingLineImportLogMapping(models.Model):
    _name = 'edi.mapping.line.import.log.mapping'
    _description = 'Map From a Short Hand Value Provided By the XML to A Human Readable Value'

    parent_id = fields.Many2one(string='Parent Mapping Line', comodel_name='edi.mapping.line')
    xml_value = fields.Char(string='Value in XML')
    output_value = fields.Char(string='Value to Use in Logging')

class EdiMappingLineImportSentinelValue(models.Model):
    _name = 'edi.mapping.line.import.sentinel'

    parent_id = fields.Many2one(string='Parent Mapping Line', comodel_name='edi.mapping.line')
    child_id = fields.Many2one(string='Sentinel Mapping Line', comodel_name='edi.mapping.line', related='parent_id.sentinel_child_id')
    expected_value = fields.Char(string='Expected Value')
    odoo_model_id = fields.Many2one(string='Odoo Model', comodel_name='ir.model', related='parent_id.odoo_sentinel_model_id')
    odoo_field_id = fields.Many2one(string='Field to Set', comodel_name='ir.model.fields')
    search_record = fields.Boolean(string='Search For Existing Records', compute='_compute_search_record', store=True)
    can_create_record = fields.Boolean(string='Can Create Record', compute='_compute_can_create_record', store=True)

    @api.constrains('odoo_field_id')
    def _check_odoo_field_id_is_of_model(self):
        for value in self:
            if value.odoo_model_id and not value.odoo_field_id.model_id != value.odoo_model_id:
                raise ValidationError(_('Field Must Belong to Odoo Model'))

    @api.depends('parent_id.sentinel_search_all')
    def _compute_search_record(self):
        for sentinel in self:
            sentinel.search_record = sentinel.parent_id.sentinel_search_all or sentinel.search_record

    @api.depends('parent_id.sentinel_can_create_all')
    def _compute_can_create_record(self):
        for sentinel in self:
            sentinel.can_create_record = sentinel.parent_id.sentinel_can_create_all or sentinel.can_create_record


class EdiMappingLineImportDependency(models.Model):
    _name = 'edi.mapping.line.import.create.dependency'
    _description = 'Additional Search Config For Search During Creation'

    parent_id = fields.Many2one(string='Field Being Searched', comodel_name='edi.mapping.line')
    odoo_field_id = fields.Many2one(string='Odoo Field of to Search On', comodel_name='ir.model.fields')
    child_id = fields.Many2one(string='Line to Use Value To Search', comodel_name='edi.mapping.line')


class EdiMappingLineAllowedValue(models.Model):
    _name = 'edi.mapping.line.import.allowed.value'
    _description = 'Allowed Value for an EDI Line'

    parent_id = fields.Many2one(string='Parent', comodel_name='edi.mapping.line')
    value = fields.Char(string='Allowed Value')
