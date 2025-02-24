from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    application_identification = fields.Char(string="Application Identification")
    extension_digit = fields.Char(string="Extension Digit")
    gs1_company_prefix = fields.Char(string="GS1 Company Prefix")
    gs1_prefix = fields.Char(string="Serial")
    check_digit = fields.Char(string="Check Digit")
