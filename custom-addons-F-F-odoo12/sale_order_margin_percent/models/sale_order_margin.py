# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    percent = fields.Float(
        string='Margin(%)',
        compute='_compute_percent',
        digits=(16, 2),
        )

    @api.depends('amount_total', 'margin')
    def _compute_percent(self):
        for order in self:
            if order.amount_total and order.margin:
                # Assuming margin is already calculated as Total Sale - Total Cost
                cost = order.amount_total - order.margin
                order.percent = round((1 - cost / order.amount_total) * 100, 2)
            else:
                order.percent = 0.0

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    margin_percent = fields.Float(
        string='Margin(%)',
        compute='_compute_margin_percent',
        digits=(16, 2),
    )

    @api.depends('price_subtotal', 'purchase_price')
    def _compute_margin_percent(self):
        for line in self:
            if line.price_subtotal and line.margin:
                line.margin_percent = round((line.price_subtotal - line.margin) / line.price_subtotal, 2)
                # Alternative calculation
                # line.margin_percent = line.purchase_price / line.price_subtotal * 100
            else:
                line.margin_percent = 0.0
