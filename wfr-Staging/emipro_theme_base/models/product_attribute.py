from odoo import fields, models


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    icon = fields.Image(string='Icon')


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    icon_style = fields.Selection(selection=[('round', "Round"), ('square', "Square"), ], string="Icon Style",
                                  default='round', help="Here, Icon size is 40*40")
    is_swatches = fields.Boolean('Use Swatch Image', help="It will show the icon column to set the swatches")
    website_ids = fields.Many2many('website', help="You can set the filter in particular website.")
