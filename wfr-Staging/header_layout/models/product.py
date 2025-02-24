# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    web_product_title = fields.Char(string="Product Title")
    website_product_image = fields.Image(string="Product Image")
    website_product_description = fields.Char(string="Website Product Description")


class Product(models.Model):
    _inherit = 'product.product'

    def _get_images(self):
        self.ensure_one()
        if self._context.get('website_id'):
            website_id = self.env['website'].browse(self._context.get('website_id'))
            if website_id and website_id.company_id.is_oxford:
                variant_images = list(self.product_variant_image_ids)
                return variant_images + self.product_tmpl_id._get_images()[1:9]
        return super(Product, self)._get_images()


class ProductAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    attribute_value_description = fields.Html(string="Description")


# class ProductTemplateAttributeLine(models.Model):
#     _inherit = "product.template.attribute.line"
#     _order = 'sequence, attribute_id,id'
#
#     sequence = fields.Integer('Sequence', help="Determine the display order", index=True)
