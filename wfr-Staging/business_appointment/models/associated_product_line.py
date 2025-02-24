#coding: utf-8

from odoo import fields, models


class associated_product_line(models.Model):
    """
    The model to keep information about added products
    """
    _name = "associated.product.line"
    _description = "Associated Product"
    _rec_name = "product_id"

    product_id = fields.Many2one("product.product", string="Product", required=True)
    product_uom_qty = fields.Integer(string="Quantity", default=1)
    appointment_id = fields.Many2one("business.appointment", string="Appointment")
    appointment_core_id = fields.Many2one("business.appointment.core", string="Reservation")
