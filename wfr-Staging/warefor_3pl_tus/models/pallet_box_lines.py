# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class PalletBoxLine(models.Model):
    _name = "pallet.box.line"
    _description = "Pallet Box Line"
    _rec_name = "box_id"

    box_id = fields.Many2one(comodel_name="product.packaging", string="Box")
    pallet_id = fields.Many2one(comodel_name="pallet.batch.tus", string="Pallet")
    box_qty = fields.Float(string="Quantity", default=0)
