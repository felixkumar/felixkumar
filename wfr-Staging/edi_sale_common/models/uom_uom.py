# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class UoM(models.Model):
    _inherit = 'uom.uom'

    edi_code = fields.Char(string='EDI Code',
                             help='Code that symbolizes the Unit of Measure when a file is transferred through EDI. It is generally made up of two uppercase letters.')
