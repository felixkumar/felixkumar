# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    temp_quantity = fields.Float('Temporary Quantity',
                                 help="Temporary hand quantity which hasn't been actual quantity on a product, "
                                      "it's used on script for managing shipstation orders",
                                 digits='Product Unit of Measure')
