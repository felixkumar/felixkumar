from odoo import api, fields, models


class EdiMapping(models.Model):
    _name = 'edi.mapping'
    _description = 'EDI Mapping'

    sync_action_id = fields.Many2one(string='Sync Action', comodel_name='edi.sync.action')
    sync_action_type = fields.Selection(string='Sync Action Type', related="sync_action_id.op_type")
    sync_action_doc_type = fields.Selection(string='Doc Code', related="sync_action_id.doc_type_id.doc_code")
    xsd_id = fields.Many2one(comodel_name='xml.xsd', string='XSD')

    partner_id = fields.Many2one(string='Trading Partner', comodel_name='res.partner',
                                 help='The partner this mapping is associated with, leave empty for the default')
    trading_partnerid = fields.Char(string="Trading Partner ID", related='partner_id.trading_partnerid', inverse='_set_trading_partnerid')
    mapping_line_ids = fields.One2many(comodel_name='edi.mapping.line', inverse_name='mapping_id')

    # _sql_constraints = [
    #     ('action_partner_unique', 'check UNIQUE(sync_action_id, partner_id)', 'There already exists a mapping for this trading partner for this sync action')
    # ]

    @api.onchange('sync_action_id')
    def _onchange_sync_action_id(self):
        for mapping in self:
            mapping.xsd_id = mapping.sync_action_id.doc_type_id.xsd_id

    def _set_trading_partnerid(self):
        for mapping in self:
            trading_partnerid = mapping.trading_partnerid
            new_partner = self.env['res.partner'].search([('trading_partnerid', '=', trading_partnerid)])
            if not new_partner:
                new_partner = self.env['res.partner'].create({
                    'name': trading_partnerid,
                    'trading_partnerid': trading_partnerid,
                })
            mapping.partner_id = new_partner

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if not self._context.get('is_copy'):
            res.action_create_lines_from_xsd()
        return res

    def copy(self, default=None):
        res = super(EdiMapping, self.with_context(is_copy=True)).copy(default=default)
        for line in self.mapping_line_ids:
            line.copy(default={
                'mapping_id': res.id,
            })
        return res

    def unlink(self):
        self.mapping_line_ids.unlink()
        return super().unlink()

    def action_create_lines_from_xsd(self):
        self.mapping_line_ids.unlink()
        mapping_lines_to_autocreate = []
        for mapping in self:
            for xsd_line in mapping.xsd_id.xsd_line_ids:
                mapping_lines_to_autocreate.append({
                    'mapping_id': mapping.id,
                    'xsd_line_id': xsd_line.id,
                })
        self.env['edi.mapping.line'].create(mapping_lines_to_autocreate)

    def configure(self):
        return self

    def name_get(self):
        names = []
        for mapping in self:
            if mapping.partner_id:
                names.append((mapping.id, 'Mapping %s for partner %s' % (mapping.xsd_id.name, mapping.partner_id.name)))
            else:
                names.append((mapping.id, 'Default Mapping %s' % mapping.xsd_id.name))
        return names

    def get_root_line(self):
        self.ensure_one()
        return self.mapping_line_ids.filtered_domain([('parent_id', '=', False)])

    def _get_mapping_to_configure(self, config):
        mapping = self
        if 'partner' in config:
            mapping = self.search(
                [('sync_action_id', '=', self.sync_action_id.id), ('trading_partnerid', '=', config['partner'])])
            if not mapping:
                mapping = self.copy({'trading_partnerid': config['partner']})
        return mapping


class EdiMappingLine(models.Model):
    _name = 'edi.mapping.line'
    _description = 'EDI Mapping Line'

    mapping_id = fields.Many2one(comodel_name='edi.mapping', required=True)
    odoo_model_id = fields.Many2one(string='Model', comodel_name='ir.model', compute='_compute_odoo_model_id', store=True, recursive=True, readonly=False)
    odoo_field_id = fields.Many2one(string='Field', comodel_name='ir.model.fields')
    xsd_line_id = fields.Many2one(string='XSD Definition Element', comodel_name='xml.xsd.line')
    tag = fields.Char(string='Tag Name', compute='_compute_tag', store=True, readonly=False)
    x_to_many = fields.Boolean(string='Is X2many', compute='_compute_x_to_many')
    sync_action_doc_type = fields.Selection(string='Doc Code', related="mapping_id.sync_action_type")

    parent_id = fields.Many2one(comodel_name='edi.mapping.line', string='Parent Line', compute='_compute_parent_id', store=True)
    depth = fields.Integer(compute='_compute_depth', recursive=True)
    child_ids = fields.One2many(comodel_name='edi.mapping.line', string='mapping line', inverse_name='parent_id')
    has_children = fields.Boolean(string="Has Children", compute='_compute_has_children')

    @api.depends('parent_id.x_to_many', 'parent_id.odoo_field_id.relation', 'parent_id.odoo_model_id')
    def _compute_odoo_model_id(self):
        for line in self:
            model = line.odoo_model_id
            if line.parent_id and line.parent_id.x_to_many and line.parent_id.odoo_field_id:
                model_name = line.parent_id.odoo_field_id.relation
                model = self.env['ir.model'].search([('model', '=', model_name)])
            elif line.parent_id and line.parent_id.odoo_model_id:
                model = line.parent_id.odoo_model_id
            line.odoo_model_id = model

    @api.depends('xsd_line_id.path')
    def _compute_tag(self):
        for line in self.with_context(compute_tag=True):
            line.tag = line.xsd_line_id.path if line.xsd_line_id else line.tag

    @api.depends('odoo_field_id.ttype')
    def _compute_x_to_many(self):
        for line in self:
            line.x_to_many = line.odoo_field_id.ttype in ['one2many', 'many2many']

    @api.depends('xsd_line_id.parent_id')
    def _compute_parent_id(self):
        for line in self:
            xsd_parent = line.xsd_line_id.parent_id
            line.parent_id = line.mapping_id.mapping_line_ids.filtered_domain([('xsd_line_id', '=', xsd_parent.id)])

    @api.depends('parent_id.depth')
    def _compute_depth(self):
        for line in self:
            line.depth = line.parent_id.depth + 1 if line.parent_id else 0

    @api.depends('child_ids')
    def _compute_has_children(self):
        for line in self:
            line.has_children = bool(line.child_ids)

    def write(self, vals):
        if 'tag' in vals and not self._context.get('compute_tag'):
            vals.update(xsd_line_id=False)
        return super().write(vals)

    def name_get(self):
        return self.mapped(lambda line: (line.id, line.tag))

    def get_all_descendants(self, filter_func=lambda line: line):
        res = self.env['edi.mapping.line']
        children = self.child_ids
        res |= children
        while children:
            next_children = children.child_ids.filtered(filter_func)
            res |= next_children
            children = next_children
        return res

    def is_ancestor_of(self, potential_child):
        self.ensure_one()
        return potential_child in self.get_all_descendants()

    def _follow_path(self, path):
        self.ensure_one()
        current = self
        for step in path.split('/'):
            if step == '..':
                current = current.parent_id
            else:
                current = current.child_ids.filtered_domain([('tag', '=', step)])
        return current
