from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    list_price = fields.Float(
        compute="_compute_list_price",)
    list_price2 = fields.Float(
        string="Precio de Venta LP2",
        compute="_compute_list_price2",
        digits=dp.get_precision('Product Price'))
    taxed_lst_price2 = fields.Float(
        string='Precio de venta Neto LP2',
        compute='_compute_taxed_lst_price2',
        digits=dp.get_precision('Product Price'),
    )
    base_imponible1 = fields.Float(
        string="Base Imponible LP1",
        compute="_compute_baseimponible1",
        digits=dp.get_precision('Product Price'),
    )
    base_imponible2 = fields.Float(
        string="Base Imponible LP2",
        compute="_compute_baseimponible2",
        digits=dp.get_precision('Product Price'),
    )
    base_imponible_costo = fields.Float(
        string="Base Imponible Costo",
        compute="_compute_base_costo",
        digits=dp.get_precision('Product Price'),
    )
    profit_margin = fields.Float("Margen LP1 (%/$)")
    profit_margin_computed_amount = fields.Float("Monto Margen", compute="_compute_margin_amount")
    profit_margin2 = fields.Float("Margen LP2 (%/$)")
    profit_margin_computed_amount2 = fields.Float("Monto Margen", compute="_compute_margin_amount2")

    @api.depends('profit_margin', 'standard_price')
    def _compute_list_price(self):
        for product in self:
            product.list_price = product.standard_price * (product.profit_margin / 100 + 1)

    @api.depends('profit_margin2', 'standard_price')
    def _compute_list_price2(self):
        for product in self:
            product.list_price2 = product.standard_price * (product.profit_margin2 / 100 + 1)

    @api.depends('taxes_id', 'list_price2')
    def _compute_taxed_lst_price2(self):
        """ compute it from list_price and not for lst_price for performance
        (avoid using dummy related field)
        """
        company_id = self._context.get(
            'company_id', self.env.user.company_id.id)
        for product in self:
            product.taxed_lst_price2 = product.taxes_id.filtered(
                lambda x: x.company_id.id == company_id).compute_all(
                    product.list_price2,
                    self.env.user.company_id.currency_id,
                    product=product)['total_included']

    @api.depends('list_price', 'taxes_id')
    def _compute_baseimponible1(self):
        for product in self:
            if product.taxes_id:
                product.base_imponible1 = product.list_price / (product.taxes_id.mapped('amount')[0] / 100 + 1)
            else:
                product.base_imponible1 = product.list_price

    @api.depends('list_price2', 'taxes_id')
    def _compute_baseimponible2(self):
        for product in self:
            if product.taxes_id:
                product.base_imponible2 = product.list_price2 / (product.taxes_id.mapped('amount')[0] / 100 + 1)
            else:
                product.base_imponible2 = product.list_price2

    @api.depends('standard_price', 'taxes_id')
    def _compute_base_costo(self):
        for product in self:
            if product.taxes_id:
                product.base_imponible_costo = product.standard_price / (product.taxes_id.mapped('amount')[0] / 100 + 1)
            else:
                product.base_imponible_costo = product.standard_price

    @api.depends('profit_margin', 'standard_price')
    def _compute_margin_amount(self):
        for product in self:
            product.profit_margin_computed_amount = product.standard_price * (product.profit_margin / 100)

    @api.depends('profit_margin2', 'standard_price')
    def _compute_margin_amount2(self):
        for product in self:
            product.profit_margin_computed_amount2 = product.standard_price * (product.profit_margin2 / 100)


class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    lst_price2 = fields.Float(
        string="Precio de Venta LP2",
        compute="_compute_list_price2",
        digits=dp.get_precision('Product Price'))
    taxed_lst_price2 = fields.Float(
        string='Precio de venta Neto LP2',
        compute='_compute_taxed_lst_price2',
        digits=dp.get_precision('Product Price'),
    )
    profit_margin = fields.Float("Margen LP1 (%/$)")
    profit_margin2 = fields.Float("Margen LP2 (%/$)")

    @api.multi
    @api.depends('fix_price', 'profit_margin')
    def _compute_lst_price(self):
        uom_model = self.env['uom.uom']
        for product in self:
            price = product.fix_price or product.list_price
            if 'uom' in self.env.context:
                price = product.uom_id._compute_price(
                    price, uom_model.browse(self.env.context['uom']))
            product.lst_price = price * (product.profit_margin / 100 + 1)

    @api.multi
    @api.depends('fix_price', 'profit_margin2')
    def _compute_list_price2(self):
        uom_model = self.env['uom.uom']
        for product in self:
            price = product.fix_price or product.list_price2
            if 'uom' in self.env.context:
                price = product.uom_id._compute_price(
                    price, uom_model.browse(self.env.context['uom']))
            product.list_price2 = price * (product.profit_margin2 / 100 + 1)

    @api.multi
    def _compute_list_price(self):
        uom_model = self.env['uom.uom']
        for product in self:
            price = product.fix_price or product.product_tmpl_id.list_price
            if 'uom' in self.env.context:
                price = product.uom_id._compute_price(
                    price, uom_model.browse(self.env.context['uom']))
            product.list_price = price * (product.profit_margin / 100 + 1)

    @api.multi
    def _inverse_product_lst_price(self):
        uom_model = self.env['uom.uom']
        for product in self:
            vals = {}
            if 'uom' in self.env.context:
                vals['fix_price'] = product.uom_id._compute_price(
                    product.lst_price,
                    uom_model.browse(self.env.context['uom']))
            else:
                vals['fix_price'] = product.lst_price
            if product.product_variant_count == 1:
                product.product_tmpl_id.list_price = vals['fix_price'] * (product.profit_margin / 100 + 1)
            else:
                fix_prices = product.product_tmpl_id.mapped(
                    'product_variant_ids.fix_price')
                # for consistency with price shown in the shop
                product.product_tmpl_id.with_context(
                    skip_update_fix_price=True).list_price = min(fix_prices) * (product.profit_margin / 100 + 1)
            product.write(vals)

    @api.depends('taxes_id', 'lst_price2')
    def _compute_taxed_lst_price2(self):
        """ if taxes_included lst_price already has taxes included
        """
        company_id = self._context.get(
            'company_id', self.env.user.company_id.id)
        for product in self:
            product.taxed_lst_price = product.taxes_id.filtered(
                lambda x: x.company_id.id == company_id).compute_all(
                product.lst_price,
                self.env.user.company_id.currency_id,
                product=product)['total_included']