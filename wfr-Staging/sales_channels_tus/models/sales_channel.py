from odoo import api, fields, models, _


class SalesChannel(models.Model):
    _name = "sales.channel"

    name = fields.Char(string='Channel Name')
