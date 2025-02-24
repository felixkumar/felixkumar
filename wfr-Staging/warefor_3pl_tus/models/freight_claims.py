from odoo import fields, models

class FreightClaims(models.Model):
    _name = "freight.claims"

    name = fields.Char(string="Name")