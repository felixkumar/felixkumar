from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    identical_sku = fields.Char("Identical SKU", copy=False)
    is_locked = fields.Boolean('Is Locked', copy=False)

    def is_get_locked_product(self):
        """
        It will lock and unlock the product
        """
        for rec in self:
            rec.is_locked = not rec.is_locked


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def is_get_locked_product(self):
        """
        It will lock and unlock the product
        """
        for rec in self:
            rec.is_locked = not rec.is_locked
