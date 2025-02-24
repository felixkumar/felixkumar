# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)


class PalletImportCost(models.Model):
    _name = 'pallet.import.cost'
    _description = 'Pallet Cost'

    name = fields.Char(_("Name"))
    actual_cost = fields.Float(string="Actual Cost")
    processing_fee_per = fields.Float(string="Processing Fees %", help="Enter the processing fee in percentage",
                                      default=10.0)
    processing_fee_amt = fields.Float(string="Processing Fees $", compute="_compute_processing_fee_amt",
                                      help="Calculate total processing amount based on the "
                                           "actual cost and processing fee percentage")

    pallet_id = fields.Many2one(comodel_name="pallet.batch.tus", string="Pallet")
    product_tmp_id = fields.Many2one(comodel_name="product.template", string="Product")
    pallet_cost_config_id = fields.Many2one(comodel_name="pallet.cost.config", string=_("Pallet Costs"))
    transit_app_id = fields.Many2one(comodel_name="freight.freight", string=_("Transit App"))
    total_cost = fields.Float(string="Total Price $")
    product_id = fields.Many2one(comodel_name="product.product", string="Product")

    @api.depends('actual_cost', 'processing_fee_per')
    def _compute_processing_fee_amt(self):
        """
        Calculate processing fee cost based on the added percentage
        :return:
        """
        for record in self:
            record.processing_fee_amt = record.transit_app_id.markup_import_cost
            # if record.transit_app_id.markup_import_cost and not record.processing_fee_per:
            #     record.processing_fee_per = record.transit_app_id.markup_import_cost
            if record.processing_fee_per and record.actual_cost:
                record.processing_fee_amt = record.actual_cost * (record.processing_fee_per / 100)
                record.total_cost = record.actual_cost + record.processing_fee_amt
            elif record.actual_cost:
                record.total_cost = record.actual_cost
