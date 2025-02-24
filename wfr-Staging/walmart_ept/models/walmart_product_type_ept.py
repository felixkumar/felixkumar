from odoo import models, fields

class WalmartProductType(models.Model):
    _name = 'walmart.product.type.ept'
    _description = 'Walmart Product Type'

    name = fields.Char(string='Product Type', help='Product Type')
