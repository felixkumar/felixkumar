# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _cart_update_order_line(self, product_id, quantity, order_line, **kwargs):
        """ Update the SO's recurrence when adding or removing
            a subscription product"""

        # order_line_exist is used to check if SOL existed before
        # super() (in case of quantity <= 0, SOL is unlinked)
        order_line_exist = bool(order_line)
        order_line = super()._cart_update_order_line(product_id, quantity, order_line, **kwargs)

        def get_default_recurrence_id(p):
            pricelist = self.env['website'].get_current_website().get_current_pricelist()
            pricing = self.env['product.pricing']._get_first_suitable_pricing(p, pricelist)
            return pricing.recurrence_id

        # Take the product from order line (in case new variant created),
        # otherwise use the default product_id
        product_id = order_line.product_id.id or product_id
        product = self.env['product.product'].browse(product_id)
        if product.recurring_invoice:
            if order_line_exist and quantity <= 0:
                sols = self.order_line.filtered(lambda sol: sol.product_id.recurring_invoice)
                self.recurrence_id = sols and get_default_recurrence_id(sols[0].product_id) or False
            elif not order_line_exist and quantity >= 0:
                self.recurrence_id = get_default_recurrence_id(product)
        return order_line
