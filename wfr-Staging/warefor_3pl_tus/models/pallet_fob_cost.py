# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)


class PalletFobCost(models.Model):
    _name = 'pallet.fob.cost'
    _description = 'Calculated against FOB'
    _rec_name = 'product_id'

    pallet_id = fields.Many2one(comodel_name="pallet.batch.tus", string="Pallet")
    pallet_cost_config_id = fields.Many2one(comodel_name="pallet.cost.config", string=_("Pallet Costs"))
    transit_app_id = fields.Many2one(comodel_name="freight.freight", string=_("Transit App"))
    total_cost = fields.Float(string="Total Price $", compute='_compute_total_cost')
    fob_per = fields.Float(string="FOB %")
    product_id = fields.Many2one(comodel_name="product.product", string="Product")

    @api.depends('fob_per')
    def _compute_total_cost(self):
        """
        Calculated against FOB from the FOB standard price
        :return:
        """
        for record in self:
            standard_price = 0
            transit_app_id = record.transit_app_id
            if transit_app_id:
                standard_price = sum(transit_app_id.freight_order_line_ids.mapped('value'))
            elif record.pallet_id:
                standard_price = sum(record.pallet_id.transit_app_id.freight_order_line_ids.mapped('base_cost'))
                # standard_price = sum(record.pallet_id.mapped('product_ids.product_id.standard_price'))
                total_qty = sum(record.pallet_id.mapped('product_ids.product_qty'))
                standard_price *= total_qty

            fob_per = record.fob_per / 100
            record.total_cost = standard_price * fob_per
