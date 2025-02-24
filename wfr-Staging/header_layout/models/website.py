# -*- coding: utf-8 -*-

from odoo import fields, models


class Website(models.Model):
    _inherit = ['website', 'mail.thread', 'rating.mixin']
    _name = 'website'

    product_page_image_layout_mobile = fields.Selection([
        ('carousel', 'Carousel'),
        ('grid', 'Grid'),
    ], default='carousel', required=True, string="Image Layout for mobile"
    )
