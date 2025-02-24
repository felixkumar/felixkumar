#coding: utf-8

from odoo import fields, models


class appointment_product(models.Model):
    """
    Overwrite to add type
    """
    _inherit = "appointment.product"

    dummy_type_id = fields.Many2one("custom.dummy.type")
