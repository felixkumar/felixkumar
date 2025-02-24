# -*- coding: utf-8 -*-

from odoo import fields, models


class custom_appointment_product_field(models.Model):
    """
    Overwrite to introduce appointment product fields
    """
    _name = "custom.appointment.product.field"
    _inherit = ["custom.extra.field"]
    _description = "Custom Service Field"
    _field_code = "bacap"
    _linked_model = "appointment.product"
    _type_field = "dummy_type_id"
    _type_field_model = "custom.dummy.type"
    _backend_views = ["business_appointment_custom_fields.appointment_product_view_form"]

    types_ids = fields.Many2many(
        "custom.dummy.type",
        "ba_dummy_type_custom_field_product_reltable",
        "ba_dummy_type_product_rel_id",
        "custom_bap_field_rel_id",
        string="Types",
        help="Leave it empty, if this field should appear for all resources disregarding type"
    )
    placement = fields.Selection(
        selection_add=[
            ("left_panel_group", "Left Column"),
            ("right_panel_group", "Rigth Column"),
            ("settings_tab_group", "Settings"),
            ("after_description_group", "After Description"),
        ],
    )
    sel_options_ids = fields.One2many(context={"default_model": "custom.appointment.product.field"},)
