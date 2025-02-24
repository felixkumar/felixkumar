# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _, api


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    height = fields.Float(string="Height", default=0.0)
    width = fields.Float(string="Width", default=0.0)
    packaging_length = fields.Float(string="Length", default=0.0)

    package_per_pallet = fields.Float("Package Per Pallet")
