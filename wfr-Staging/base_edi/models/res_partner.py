# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Partner(models.Model):

    _inherit = 'res.partner'

    trading_partnerid = fields.Char(string='Trading Partner ID', help='Unique internal identifier defined by EDI Vendors which identifies the relationship')
