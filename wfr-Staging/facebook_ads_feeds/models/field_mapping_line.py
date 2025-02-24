# -*- coding: utf-8 -*-
################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
################################################################################
from odoo import models,fields,api
import logging
_logger = logging.getLogger(__name__)

class FieldMapping(models.Model):
    _name = 'fb.field.mappning.line'
    _description = "Fields mapping Line"

    facebook_field_id = fields.Many2one(comodel_name='fb.facebook.fields', string="Facebook Fields",help="Select the facebook field name that you want to map with Odoo field")
    fixed = fields.Boolean(string="Fixed",default=False,help="Select wether you want to send the fixed data or the field data")
    model_field_id = fields.Many2one(comodel_name='ir.model.fields',domain="[('model', '=', 'product.template')]")
    field_mapping_id = fields.Many2one(comodel_name='fb.field.mappning',help="Field with which you want to map")
    fixed_text = fields.Char(string="Text",help="Fixed data that you want to send")
    default = fields.Char(string="Default",help="The data enter here will be send when there is no data in the field")
