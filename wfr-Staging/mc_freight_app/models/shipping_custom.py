# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ShippingCustom(models.Model):
    _name = 'shipping.custom'
    _description = 'shipping custom for custom activity'
    _rec_name = 'freight_id'

    freight_id = fields.Many2one('freight.freight', string="Freight Opration")
    date = fields.Date(string="Date")
    agent_id = fields.Many2one('res.partner', string="Agent")
    need_document = fields.Boolean(string="Need a Document")
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirm'),
                              ('done', 'Done')], string="State")
    shipping_document_ids = fields.One2many('shipping.document', 'shipping_custom_id', string="Document")

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'


class ShippingDocument(models.Model):
    _name = 'shipping.document'
    _description = 'Document for shipping'

    name = fields.Char(string="Name")
    type = fields.Char(string="Type")
    file_content = fields.Binary(string="File Content")
    file_name = fields.Char(string="File Name")
    shipping_custom_id = fields.Many2one('shipping.custom', string="Custom Shipping")
