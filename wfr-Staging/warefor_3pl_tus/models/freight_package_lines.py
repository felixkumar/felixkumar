# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class FreightPackageLine(models.Model):
    _name = "freight.package.line"
    _description = "Freight Package Lines"
    _rec_name = "freight_id"

    freight_id = fields.Many2one(comodel_name="freight.freight", string="Freight")
    package_id = fields.Many2one(comodel_name="product.packaging", string="Package")
    product_qty = fields.Float(string="Product Quantity", default=0, help="Maximum qty stored in per package")
    package_qty = fields.Float(string="Package Quantity", default=0, help="Required packages for product qty")
    require_pallets = fields.Float(string="Require Pallets", default=0, help="Pallets are required for packages")
    package_per_pallet = fields.Float(string="Package Per Pallet", default=0)
