# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class Partner(models.Model):
    _inherit = 'res.partner'

    send_edi_inv = fields.Boolean(string='Send 810 Invoice', help='Whether the contact sends outbound 810 Invoices to the EDI.')
    state_code = fields.Char(string='State Code', related='state_id.code')
