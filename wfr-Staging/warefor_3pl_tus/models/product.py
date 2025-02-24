# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

BLOCK_USER = [1580]


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_height = fields.Float(_('Height'))
    product_width = fields.Float(_('Width'))
    product_length = fields.Float(_('Length'))
    packaging_qty = fields.Float(_('Packaging Quantity'), default=48.0, help="Pallet package should be W=3, D=4, H=4")

    import_cost_ids = fields.One2many(comodel_name="pallet.import.cost", inverse_name="product_tmp_id",
                                      string=_("Import Cost"))
    storage_cost_ids = fields.One2many(comodel_name="pallet.storage.cost", inverse_name="product_tmp_id",
                                       string=_("Storage Fees"))
    vas_cost_ids = fields.One2many(comodel_name="pallet.vas.cost", inverse_name="product_tmp_id",
                                   string=_("Value Added Service"))
    is_packaging_product = fields.Boolean(string="Is Packaging Product?")
    packaging_id = fields.Many2one(comodel_name="product.packaging", string="Product Packages", required=False, help="Gives the different ways to package the same product.", tracking=True)

    product_per_pallet = fields.Float("Product Per Pallet", tracking=True)

    product_pallet = fields.Binary(string="Product Pallet", tracking=True)
    warehouse_pallet = fields.Binary(string="Warehouse Pallet", tracking=True)
    mis_file = fields.Binary(string="MIS", tracking=True)
    weight = fields.Float('Weight', compute='_compute_weight', digits='Stock Weight', inverse='_set_weight', store=True, tracking=True)

    cartons_per_container = fields.Text(string="Cartons per Container")
    cartons_per_pallet = fields.Text(string="Cartons per Pallet")
    cases_per_carton = fields.Text(string="Cases per Carton")
    units_per_case = fields.Text(string="Units per Case")
    pallet_stacking = fields.Text(string="Pallet Stacking")
    warehouse_stacking = fields.Text(string="Warehouse Stacking")
    is_fba = fields.Boolean('Is FBA?', copy=False)
    is_prime = fields.Boolean('Is Prime?', copy=False)

    # Pallet Measurements
    pallet_height = fields.Float(string="Height")
    pallet_width = fields.Float(string="Width")
    pallet_length = fields.Float(string="Length")

    pallet_volume = fields.Float(
        'Pallet Volume', compute='_compute_pallet_volume', inverse='_set_pallet_volume', digits='Volume', store=True)

    @api.depends('product_variant_ids', 'product_variant_ids.pallet_volume')
    def _compute_pallet_volume(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.pallet_volume = template.product_variant_ids.pallet_volume
        for template in (self - unique_variants):
            template.pallet_volume = 0.0

    def _set_pallet_volume(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.pallet_volume = template.pallet_volume

    @api.model
    def _get_length_uom_id_from_ir_config_parameter(self):
        res = super(ProductTemplate, self)._get_length_uom_id_from_ir_config_parameter()
        product_length_in_inch_param = self.env['ir.config_parameter'].sudo().get_param('product.volume_in_cubic_inch')
        if product_length_in_inch_param == '1':
            return self.env.ref('uom.product_uom_inch')
        return res

    @api.model
    def get_views(self, views, options=None):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            options['toolbar'] = False
        res = super().get_views(views, options)
        # if self.env.user.id in BLOCK_USER and res.get('views'):
        #     if res.get('views', {}).get('list', {}).get('arch', "") and 'tree' in res.get('views', {}).get('list',
        #                                                                                                    {}).get(
        #             'arch', ""):
        #         data = res['views']['list']['arch']
        #         data = data.replace("tree", 'tree create="false"', 1)
        #         res['views']['list']['arch'] = data
        #     if res.get('views', {}).get('form', {}).get('arch', "") and 'form' in res.get('views', {}).get('form',
        #                                                                                                    {}).get(
        #             'arch', ""):
        #         data = res['views']['form']['arch']
        #         data = data.replace("form", 'form create="false"', 1)
        #         res['views']['form']['arch'] = data
        #     if res.get('views', {}).get('kanban', {}).get('arch', "") and 'kanban' in res.get('views', {}).get('kanban',
        #                                                                                                        {}).get(
        #             'arch', ""):
        #         data = res['views']['kanban']['arch']
        #         data = data.replace("kanban", 'kanban create="false"', 1)
        #         res['views']['kanban']['arch'] = data
        return res

    # def write(self, vals):
    #     if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
    #         raise UserError(_("You don't have enough access, Please contact your system administrator."))
    #     res = super(ProductTemplate, self).write(vals)
    #     return res
