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

class FacebookFields(models.Model):
    _name = 'fb.facebook.fields'
    _description = "Facebook fields"

    name = fields.Char(string="Field",required=True)
    required = fields.Boolean(string="Required")
    g_beg = fields.Boolean(string="Begins With \'g:\'")
