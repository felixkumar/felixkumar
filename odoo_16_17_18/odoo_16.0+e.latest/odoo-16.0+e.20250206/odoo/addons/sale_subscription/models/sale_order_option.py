# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models

class SaleOrderOption(models.Model):
    _inherit = 'sale.order.option'

    @api.depends('order_id.recurrence_id')
    def _compute_price_unit(self):
        super()._compute_price_unit()

    @api.depends('order_id.recurrence_id')
    def _compute_discount(self):
        super()._compute_discount()
