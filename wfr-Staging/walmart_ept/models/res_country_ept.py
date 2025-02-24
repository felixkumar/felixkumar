from odoo import models, fields

class ResCountryEPT(models.Model):
    _inherit = "res.country"

    walmart_marketplace_code = fields.Char()
