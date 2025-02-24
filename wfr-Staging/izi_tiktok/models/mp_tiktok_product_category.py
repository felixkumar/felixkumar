from odoo import api, fields, models


class MPProductCategory(models.Model):
    _name = 'mp.tiktok.product.category'
    _inherit = 'mp.base'
    _description = 'Marketplace Tiktok Category'
    # _rec_name = 'product_category'

    category_id = fields.Char(string="Category ID", readonly=True)
    parent_id = fields.Char(string="Parent ID", readonly=True)
    local_display_name = fields.Char(string="Display Name", readonly=True)
    is_leaf = fields.Boolean(string="Is Leaf", readonly=True)
