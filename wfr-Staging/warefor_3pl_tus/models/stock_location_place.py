# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _


class PalletBoxLine(models.Model):
    _name = "stock.location.pallet"
    _description = "Pallet Stock Location"

    pallet_batch_id = fields.Many2one(comodel_name="pallet.batch.tus", string="Pallet")
    type = fields.Selection(selection=[('row', 'Row'), ('rack', 'Rack'), ('bin', 'Bin')], string="Type", default='row')
    code = fields.Char(string="Code")
    stock_location_id = fields.Many2one('stock.location', string="Stock Location")