# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ShippingWizard(models.TransientModel):
    _name = 'shipping.wizard'
    _description = "Wizard for set shipping date"

    shipping_date = fields.Date(string="Date")
    shipping_type = fields.Selection([('received', 'Received'),
                                      ('delivered', 'Delivered')], string="Shipping Type")
    freight_ids = fields.Many2many('freight.freight', string="Shipping Information")

    def set_date(self):
        print("111111111111111111111")