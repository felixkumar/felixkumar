from odoo import api, fields, models


class SaleOrderLineInherit(models.Model):
    _inherit = "sale.order.line"

    price_list_type = fields.Selection([('LP1', 'LP1'), ('LP2', 'LP2')], default='LP1', string="LP")

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLineInherit, self).product_id_change()
        self.onchange_price_list_type()
        return res

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        res = super(SaleOrderLineInherit, self).product_uom_change()
        self.onchange_price_list_type()
        return res

    @api.multi
    @api.onchange('price_list_type')
    def onchange_price_list_type(self):
        if self.price_list_type == 'LP2':
            self.price_unit = self.product_id.base_imponible2
        else:
            self.price_unit = self.product_id.base_imponible1
