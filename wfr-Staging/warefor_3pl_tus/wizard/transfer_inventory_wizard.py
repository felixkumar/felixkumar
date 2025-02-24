# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError


class TransferInventoryWizard(models.TransientModel):
    _name = 'transfer.inventory.wizard'
    _description = 'Transfer Inventory Wizard'

    def _empty_location_ids(self):
        """

        :return:
        """
        domain = []
        if self._context.get('params'):
            model = self._context.get('params').get('model')
            id = self._context.get('params').get('id')
            if model == 'freight.freight' and id:
                freight_id = self.env[model].browse(id)
                product_ids = freight_id.freight_order_line_ids.mapped('goods')
                product_ids = self.env['product.product'].browse(product_ids.ids)
                location_ids = self.env['stock.location'].search([])
                quant_ids = self.env['stock.quant'].search([('location_id', 'in', location_ids.ids), ('available_quantity', '>', 0)])
                location_ids = location_ids - quant_ids.mapped('location_id')
                domain = [('id', 'in', location_ids.ids)]
        return domain

    location_id = fields.Many2one(comodel_name="stock.location", string="Location", domain=_empty_location_ids)
    freight_id = fields.Many2one(comodel_name="freight.freight", string="Location")

    def open_wizard_for_transfer_inventory(self):
        try:
            if not self.location_id:
                raise UserError("Please select the location for transfer the inventory!")
            freight_id = self.env[self._context.get('active_model')].browse([self._context.get('active_id')])
            freight_id.with_context(is_from_wizard=True).transfer_inventory_with_pallets(self.location_id)
        except Exception as e:
            raise UserError("{}".format(e))
