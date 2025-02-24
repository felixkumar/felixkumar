# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class PalletProductLine(models.Model):
    _name = "pallet.product.line"
    _description = "Pallet Product Line"
    _rec_name = "product_id"

    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    pallet_id = fields.Many2one(comodel_name="pallet.batch.tus", string="Pallet")
    product_qty = fields.Float(string="Product Quantity", default=0)
    sold_qty = fields.Float(string="Sold Quantity", default=0)
    remaining_qty = fields.Float(string="Remaining Quantity", compute="_compute_product_qty")

    @api.depends('product_qty')
    def _compute_product_qty(self):
        """
        """
        for record in self:
            record.remaining_qty = record.product_qty - record.sold_qty
