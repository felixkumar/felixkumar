from odoo import api, fields, models


class MPTiktokProductAttribute(models.Model):
    _name = 'mp.tiktok.product.attribute'
    _inherit = 'mp.base'
    _description = 'Marketplace Tiktok Attribute'

    name = fields.Char(string='Attribute Name')
    value_ids = fields.One2many('mp.tiktok.product.attribute.values', 'attribute_id', string='Values')
    mp_product_id = fields.Many2one('mp.product', string='Product ID', ondelete='cascade')


class MPTiktokProductAttributeValues(models.Model):
    _name = 'mp.tiktok.product.attribute.values'
    _description = 'Marketplace Tiktok Attribute Values'

    name = fields.Char(string='Attribute Value')
    value_id = fields.Char(string='Attribute Value ID')
    attribute_id = fields.Many2one('mp.tiktok.product.attribute', string='Product ID', ondelete='cascade')