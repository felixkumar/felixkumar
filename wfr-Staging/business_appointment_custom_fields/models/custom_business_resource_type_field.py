# -*- coding: utf-8 -*-

from odoo import fields, models


class custom_business_resource_type_field(models.Model):
    """
    Overwrite to introduce resource type fields
    """
    _name = "custom.business.resource.type.field"
    _inherit = ["custom.extra.field"]
    _description = "Custom Business Resource Type Field"
    _field_code = "cbra"
    _linked_model = "business.resource.type"
    _type_field = "dummy_type_id"
    _type_field_model = "custom.dummy.type"
    _backend_views = ["business_appointment_custom_fields.business_resource_type_view_form"]

    types_ids = fields.Many2many(
        "custom.dummy.type",
        "ba_dummy_type_custom_field_reltable",
        "ba_dummy_type_rel_id",
        "custom_brt_field_rel_id",
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
    sel_options_ids = fields.One2many(context={"default_model": "custom.business.resource.type.field"},)
