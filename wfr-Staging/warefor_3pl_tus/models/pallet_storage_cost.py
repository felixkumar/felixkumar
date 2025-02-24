# -*- coding: utf-8 -*-

import calendar
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class PalletStorageCost(models.Model):
    _name = 'pallet.storage.cost'
    _description = 'Pallet Storage Cost'

    name = fields.Char(_("Name"))
    unit_of_measure = fields.Selection(string="Unit Of Measure",
                                       selection=[('per_pallet', 'Per Pallet Per Day'),
                                                  ('per_pallet_per_month', 'Per Pallet Per Month'),
                                                  ('per_cubic_feet_per_month', 'Per Cubic Feet Per Month'),
                                                  ('each', 'Each'),
                                                  ('per_day', 'Per Day')],
                                       default='per_pallet')
    unit_price = fields.Float(string="Unit Price")
    total_cost = fields.Float(string="Total Price")
    total_pallet = fields.Float(string="Total Pallet", default=1.0)
    total_cubic_feet = fields.Float(string="Total Cubic Feet")
    pallet_id = fields.Many2one(comodel_name="pallet.batch.tus", string="Pallet")
    unit_price_day = fields.Float(string="Unit Price Per Day", help="Unit Price Per Day",
                                  compute='_compute_unit_price_day')
    product_tmp_id = fields.Many2one(comodel_name="product.template", string="Product")
    pallet_cost_config_id = fields.Many2one(comodel_name="pallet.cost.config", string="Pallet Costs")
    transit_app_id = fields.Many2one(comodel_name="freight.freight", string=_("Transit App"))
    product_id = fields.Many2one(comodel_name="product.product", string="Product")

    @api.depends('unit_of_measure', 'total_cost')
    def _compute_unit_price_day(self):
        for rec in self:
            rec.unit_price_day = 1.0
            if rec.unit_of_measure in ('per_pallet_per_month', 'per_cubic_feet_per_month') and rec.pallet_id.start_date:
                sdate_m_days = calendar.monthrange(rec.pallet_id.start_date.year, rec.pallet_id.start_date.month)[1]
                rec.unit_price_day = rec.total_cost / sdate_m_days

    @api.onchange('unit_price', 'total_pallet', 'total_cubic_feet')
    def _onchange_total_cost(self):
        for record in self:
            if record.total_pallet:
                record.total_cost = record.unit_price * record.total_pallet
            else:
                record.total_cost = record.unit_price * record.total_cubic_feet
