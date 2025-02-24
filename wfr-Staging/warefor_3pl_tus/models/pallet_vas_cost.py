# -*- coding: utf-8 -*-

import logging
import calendar

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class PalletVASCost(models.Model):
    _name = 'pallet.vas.cost'
    _description = 'Pallet VAS Cost'

    name = fields.Char(_("Name"))
    unit_of_measure = fields.Selection(string="Unit Of Measure",
                                       selection=[('per_pallet', 'Per Pallet'),
                                                  ('per_label', 'Per Label'),
                                                  ('per_kit', 'Per Kit'),
                                                  ('per_case', 'Per Case'),
                                                  ('per_month', 'Per Month'),
                                                  ('per_report', 'Per Report'),
                                                  ('per_photo', 'Per Photo'),
                                                  ('per_shipment', 'Per Shipment'),
                                                  ('per_order', 'Per Order'),
                                                  ('per_unit', 'Per Unit'),
                                                  ('per_load', 'Per Load'),
                                                  ('per_manhour', 'Per ManHour')], default='per_pallet')
    total_cost = fields.Float(string="Total Price", compute="_compute_total_cost")
    pallet_id = fields.Many2one(comodel_name="pallet.batch.tus", string="Pallet")
    unit_price_day = fields.Float(string="Unit Price Per Day", help="Unit Price Per Day",
                                  compute='_compute_unit_price_day')
    product_tmp_id = fields.Many2one(comodel_name="product.template", string="Product")
    pallet_cost_config_id = fields.Many2one(comodel_name="pallet.cost.config", string="Pallet Costs")
    transit_app_id = fields.Many2one(comodel_name="freight.freight", string=_("Transit App"))
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    total_unit = fields.Float(string="Quantity")
    unit_price = fields.Float(string="Unit Price")

    product_uom = fields.Many2one(comodel_name='uom.uom', string="UOM")

    @api.depends('total_unit', 'unit_price', 'product_id')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = 0
            rec.total_cost = rec.total_unit * rec.unit_price

    @api.depends('unit_of_measure', 'total_cost')
    def _compute_unit_price_day(self):
        for rec in self:
            rec.unit_price_day = 1.0
            if rec.unit_of_measure == 'per_month' and rec.pallet_id.start_date:
                sdate_m_days = calendar.monthrange(rec.pallet_id.start_date.year, rec.pallet_id.start_date.month)[1]
                rec.unit_price_day = rec.total_cost / sdate_m_days

    # @api.onchange('total_unit', 'unit_price')
    # def onchange_total_cost(self):
    #     """
    #     Total Price calculating from total unit and unit price while measurement is per unit
    #     :return:
    #     """
    #     for rec in self:
    #         rec.total_cost = rec.total_unit * rec.unit_price

    @api.onchange('product_id')
    def onchange_product_id(self):
        """
        Add product price in VAS cost
        :return:
        """
        for rec in self:
            rec.unit_price = rec.product_id.lst_price
