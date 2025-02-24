# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PalletConfigIbl(models.Model):
    _name = 'pallet.config.ibl'
    _rec_name = "partner_id"
    _description = 'Pallet Fees And Cost Configuration'

    partner_id = fields.Many2one(comodel_name='res.partner', string="Customer")
    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', string="Warehouse")
    product_ids = fields.Many2many(comodel_name="product.product", string="Products")
    service_fee = fields.Many2one(comodel_name="product.product", string='Service Fee')
    service_uom = fields.Many2one(comodel_name="uom.uom", string="Service UOM")
    received_date = fields.Selection([('day_1_to_15', 'Day 1 to 15'), ('day_16_to_31', 'Day 16 to 31')], string='Received Date')
    cost = fields.Float(string='Cost')
    is_storage_fee = fields.Boolean(string="Is Storage Fee?")

    @api.onchange('service_fee')
    def _onchange_service_fee_cost(self):
        if self.service_fee:
            self.cost = self.service_fee.lst_price


class PalletConfigObl(models.Model):
    _name = 'pallet.config.obl'
    _rec_name = "partner_id"
    _description = 'Pallet Fees And Cost Configuration'

    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', string='Warehouse')
    product_ids = fields.Many2many(comodel_name="product.product", string="Products")
    cost = fields.Float(string='Cost')
    partner_id = fields.Many2one(comodel_name='res.partner', string="Customer")
    service_fee = fields.Many2one(comodel_name="product.product", string='Service Fee')
    service_uom = fields.Many2one(comodel_name="uom.uom", string="Service UOM")
    is_cbft = fields.Boolean(string="Is Cb Ft. Fee?")
    is_carton = fields.Boolean(string="Is Carton Fee?")
    is_volume = fields.Boolean(string="Is Volume Fee?")
    is_weight = fields.Boolean(string="Is Weight Fee?")
    is_pallet = fields.Boolean(string="Is Pallet Fee?")
    is_load = fields.Boolean(string="Is Load Fee?")
    is_edi_rule = fields.Boolean(string="Is EDI Fee?")
    edi_store_id = fields.Many2one("edi.customer.store", string="EDI Store ID")

    @api.onchange('service_fee')
    def _onchange_service_fee_cost(self):
        if self.service_fee:
            self.cost = self.service_fee.lst_price
