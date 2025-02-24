from odoo import api, fields, models


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    country_code = fields.Char(string='Country Code', related='country_id.code', store=True)
