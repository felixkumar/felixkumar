# -*- coding: utf-8 -*-

from odoo import api, models, fields


class TruckDriverSignatureWizard(models.TransientModel):
    _name = 'truck.driver.signature.wizard'
    _description = 'Truck Driver Signature Wizard'

    name = fields.Char(string="Truck Driver Name")
    signature = fields.Image('Signature', help='Signature', copy=False, attachment=True)
    picking_id = fields.Many2one('stock.picking')
    signature_date = fields.Date(string="Date")

    def update_truck_driver_signature(self):
        """
        Update truck driver signature in transfer
        :return:
        """
        if self.picking_id:
            self.picking_id.truck_driver_signature = self.signature
            self.picking_id.truck_driver_sign_date = self.signature_date
