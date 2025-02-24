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

class FacebookAttachment(models.Model):
    _name = 'fb.attachment.mapping'
    _order = 'id desc'
    _description = "Facebook Attachments"

    fb_shop = fields.Many2one(string="Facebook Shop",comodel_name='fb.facebook.shop',required=True)
    attachment_id = fields.Many2one(string="Attachment",comodel_name='ir.attachment',required=True)
    latest = fields.Boolean(string="Latest",default=True)
    updated = fields.Boolean(string="Updated",default=False)
