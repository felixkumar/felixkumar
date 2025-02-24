
from odoo import models, fields, api
from odoo.osv import expression

class ProductLabel(models.Model):
    _name = "product.label"
    _description = "Product Label"


class ProductLabelLine(models.Model):
    _name = "product.label.line"
    _description = 'Product Template Label Line'

    product_tmpl_id = fields.Many2one('product.template', string='Product Template Id', required=True)
    _sql_constraints = [('unique_product_tmpl_id', 'unique (product_tmpl_id)',
                         'Duplicate records in label line for same product is not allowed !')]
