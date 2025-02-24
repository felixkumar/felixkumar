# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HourTypes(models.Model):
    _name = 'hour.types'
    _description = 'Hour Types'

    name = fields.Char('Hour Type', required=True)
    description = fields.Char('Description')
    multiplier = fields.Float('Multiplier')
