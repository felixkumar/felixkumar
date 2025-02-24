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

class GoogleCategory(models.Model):
    _name = 'google.category'
    _description = "Google Cateegories"

    name = fields.Char(string="Google Category Name",required=True)
    google_categ_id = fields.Integer(string="Categ ID")
