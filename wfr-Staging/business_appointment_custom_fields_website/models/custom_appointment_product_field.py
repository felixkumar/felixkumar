# -*- coding: utf-8 -*-

from odoo import fields, models


class custom_appointment_product_field(models.Model):
    _inherit = 'custom.appointment.product.field'
    _portal_object_name = "main_object"
    _portal_views = ["business_appointment_custom_fields_website.ba_products_full"]

    portal_placement = fields.Selection(
        selection_add=[("left_panel_group", "Left Column"),("right_panel_group", "Right Column"),],
        string="Full Details Page Placement",
    )
