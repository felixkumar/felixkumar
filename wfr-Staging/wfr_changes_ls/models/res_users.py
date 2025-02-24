from odoo import fields, models


class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    allowed_product_category_ids = fields.Many2many(comodel_name="product.category", string="Allowed Product Categories")
