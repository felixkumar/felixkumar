from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class ProductProductInherit(models.Model):  
    _inherit = 'product.product'   
    lst_price = fields.Float(
        'Sales Price', default=1.0,
        digits=dp.get_precision('Product Price'),
        compute="_compute_list_price",
        help="Price at which the product is sold to customers.")
    profit_margin = fields.Float("Margen (%)")

    @api.depends('profit_margin', 'standard_price')
    def _compute_list_price(self):
        for product in self:
            product.list_price = product.standard_price * (product.profit_margin / 100 + 1)           