# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class Partner(models.Model):
    _inherit = 'res.partner'

    send_edi_order_ack = fields.Boolean(string='Send 855 Order Acknowledgement', help='Whether the contact sends outbound 855 Purchase Order Acknowledement to the EDI.')
