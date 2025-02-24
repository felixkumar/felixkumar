# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _website_show_quick_add(self):
        self.ensure_one()
        res = super()._website_show_quick_add()
        if not self.rent_ok or not res:
            return res

        # If it is a rented product, it is necessary to verify
        # that we know how to define the rental period (via the 'parent' product)
        known_period = False
        current_sale_order = self.env['website'].get_current_website().sale_get_order()
        rented_order_line = current_sale_order.order_line.filtered(
            lambda line: line.is_product_rentable
                and self in line.product_id.accessory_product_ids
        )[:1]
        if (
            rented_order_line
            and rented_order_line.start_date
            and rented_order_line.return_date
        ):
            # The line that triggered the addition of the accessory product has a period
            known_period = True
        return known_period

    def _is_add_to_cart_allowed(self):
        self.ensure_one()
        return super()._is_add_to_cart_allowed() or (self.active and self.rent_ok and self.website_published)
