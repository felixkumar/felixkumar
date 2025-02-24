# -*- coding: utf-8 -*-

from odoo import fields, models


class custom_business_resource_field(models.Model):
    """
    Overwrite to introduce resource fields
    """
    _name = "custom.business.resource.field"
    _inherit = ["custom.extra.field"]
    _description = "Custom Business Resource Field"
    _field_code = "cba"
    _linked_model = "business.resource"
    _type_field = "resource_type_id"
    _type_field_model = "business.resource.type"
    _backend_views = ["business_appointment_custom_fields.business_resource_view_form"]

    types_ids = fields.Many2many(
        "business.resource.type",
        "ba_type_custom_field_reltable",
        "ba_type_rel_id",
        "custom_ba_field_rel_id",
        string="Types",
        help="Leave it empty, if this field should appear for all resources disregarding type"
    )
    placement = fields.Selection(
        selection_add=[
            ("left_panel_group", "Left Column"),
            ("right_panel_group", "Rigth Column"),
            ("after_description_group", "After Description"),
        ],
    )
    sel_options_ids = fields.One2many(context={"default_model": "custom.business.resource.field"},)
