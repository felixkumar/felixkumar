# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _

class ChargeAllowance(models.Model):
    _name = 'charge.allowance'
    _description = 'Charges/Allowances'

    indicator = fields.Char()
    code = fields.Char()
    amount = fields.Float()
    percent_qualifier = fields.Char('Percent Qualifier')
    percent = fields.Float()
    handling_code = fields.Char('Handling Code')

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, _('[%s] %s: %.2f') % (record.indicator, record.code, record.amount)))
        return res
