# -*- coding: utf-8 -*-

import calendar
from odoo import models, fields, api, _


class OutboundSign(models.TransientModel):
    _name = 'outbound.sign.wizard'
    _description = 'Outbound Signature'

    name = fields.Char("Sign")
    freight_id = fields.Many2one('freight.freight', string='Freight')

    def mark_sign(self):
        if self.freight_id:
            self.freight_id.truck_driver_name = self.name
            self.freight_id.signature = ''
