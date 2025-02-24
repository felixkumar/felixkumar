# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.website_sale.controllers.main import WebsiteSale

class WebsiteSaleDeliveryAvatax(WebsiteSale):

    def _update_website_sale_delivery_return(self, order, **post):
        if order and order.fiscal_position_id.is_avatax:
            order.button_update_avatax()
        return super()._update_website_sale_delivery_return(order, **post)
