# -*- coding: utf-8 -*-

from odoo import api, models, fields


class TransferInventorySignatureWizard(models.TransientModel):
    _name = 'warehouse.manager.signature.wizard'
    _description = 'Transfer Inventory Wizard'

    name = fields.Char(string="Manager Name")
    signature = fields.Image('Signature', help='Signature', copy=False, attachment=True)
    picking_id = fields.Many2one('stock.picking')
    signature_date = fields.Date(string="Date", )

    def update_warehouse_manager_signature(self):
        """
        Update manager name in transfer
        :return:
        """
        if self.picking_id:
            self.picking_id.warehouse_manager_signature = self.signature
            self.picking_id.warehouse_manager_sign_date = self.signature_date
