# -*- coding: utf-8 -*-

from odoo import models, fields, api

class resCompany(models.Model):
    _inherit = 'res.company'

    header = fields.Binary("Header", help="PNG image 21x4 CM at most")
    footer = fields.Binary("Footer", help="PNG image 21x4 CM at most")
