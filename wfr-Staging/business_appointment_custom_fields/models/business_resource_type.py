#coding: utf-8

from odoo import fields, models


class business_resource_type(models.Model):
    """
    Overwrite to add type
    """
    _inherit = "business.resource.type"

    dummy_type_id = fields.Many2one("custom.dummy.type")
