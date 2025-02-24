from odoo import fields, models, api

class Pricelist(models.Model):
    _inherit = "product.pricelist"

    display_product_price = fields.Selection([('system_setting', 'As per Setting in Website/Configuration'),
                                              ('tax_excluded', 'Tax Excluded'),
                                              ('tax_included', 'Tax Included')],
                                             string="Display Product Prices on Website",
                                             help='Display Product Prices on Website',
                                             default='system_setting')


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    offer_msg = fields.Text(string="Offer Message", translate=True, help="To set the message in the product offer timer.", size=35)
    is_display_timer = fields.Boolean(string='Show Offer Timer', help="It shows the offer timer on the product page.")
