# -*- coding: utf-8 -*-
################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
################################################################################
from odoo import models,fields,api
import logging
_logger = logging.getLogger(__name__)
from odoo.addons.http_routing.models.ir_http import slug

class ProductInherit(models.Model):
    _inherit = 'product.template'

    google_categ_id = fields.Many2one(string="Google Category",comodel_name="google.category")
    brand = fields.Char(string="Facebook Brand")
    gtin = fields.Char(string="Gtin")
    mpn = fields.Char(string="Mpn No.")
