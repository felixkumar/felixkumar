# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CustomRevision(models.Model):
    _name = 'custom.revision'
    _description = 'custom revision for custom activity'
    _rec_name = 'shipping_custom_id'

    freight_id = fields.Many2one('freight.freight', string="Order")
    shipping_custom_id = fields.Many2one('shipping.custom', string="Custom Clearance Order")
    reason = fields.Text(string="Reason for Revision")
    revision_date = fields.Date(string="Revision Date")