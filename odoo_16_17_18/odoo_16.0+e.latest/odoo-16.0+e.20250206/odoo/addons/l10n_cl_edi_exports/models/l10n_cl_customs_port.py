# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class CustomsPort(models.Model):
    _name = 'l10n_cl.customs_port'
    _description = 'Chilean customs ports and codes.'

    name = fields.Char(required=True)
    code = fields.Integer(required=True)
    country_id = fields.Many2one(comodel_name='res.country', required=True)

    def name_get(self):
        res = []
        for port in self:
            name = '(%s) %s' % (port.code, port.name)
            res.append((port.id, name))
        return res
