# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError


class TransferInventoryOutboundWizard(models.TransientModel):
    _name = 'transfer.inventory.outbound.wizard'
    _description = 'Transfer Inventory Outbound Wizard'

    location_id = fields.Many2one(comodel_name="stock.location", string="Location")
    destination_location_id = fields.Many2one(comodel_name="stock.location", string="Destination Location")
    freight_id = fields.Many2one(comodel_name="freight.freight", string="Freight")

    def open_wizard_for_transfer_inventory_outbound(self):
        try:
            if not self.destination_location_id:
                raise UserError("Please select the location for transfer the inventory!")
            freight_id = self.env[self._context.get('active_model')].browse([self._context.get('active_id')])
            freight_id.with_context(is_from_wizard=True).transfer_inventory_outbound(self.destination_location_id)
            # if freight_id.is_outbound:
            #     freight_id.outbound_stage_id = self.env.ref('mc_freight_app.shipped_outbound').id
        except Exception as e:
            raise UserError("{}".format(e))


# class TransferInventoryOutboundLine(models.TransientModel):
#     _name = 'transfer.inventory.outbound.line'
#     _description = 'Transfer Inventory Outbound Line'
#
#     def domain_product_id(self):
#         freight_id = self._context.get('default_freight_id')
#         if not freight_id:
#             return []
#         freight_id = self.env['freight.freight'].browse(freight_id)
#         product_ids = freight_id.freight_order_line_ids.mapped('goods')
#         domain = [('id', 'in', product_ids.ids)]
#         return domain
#
#     @api.depends('location_id')
#     def _compute_location_id(self):
#         for rec in self:
#             rec.available_qty = 0
#             if rec.location_id:
#                 quant_ids = self.env['stock.quant'].search(
#                     [('product_id', '=', rec.product_id.id), ('location_id', '=', rec.location_id.id)])
#                 rec.available_qty = sum(quant_ids.mapped('quantity'))
#
#     outbound_id = fields.Many2one(comodel_name="transfer.inventory.outbound.wizard", string="Outbound Inventory")
#     freight_id = fields.Many2one(comodel_name="freight.freight", string="Freight", related="outbound_id.freight_id")
#     location_id = fields.Many2one(comodel_name="stock.location", string="Location")
#     destination_location_id = fields.Many2one(comodel_name="stock.location", string="Destination Location")
#     product_id = fields.Many2one(comodel_name="product.product", string="Product", domain=domain_product_id)
#     lot_id = fields.Many2one('stock.lot', 'Lot #', domain="[('product_id', '=', product_id)]", check_company=True)
#     require_qty = fields.Float(string="Require Qty")
#     available_qty = fields.Float(string="Available Qty", compute=_compute_location_id)
#     delivery_qty = fields.Float(string="Deliver Qty")
#
#     @api.onchange('delivery_qty')
#     def onchange_delivery_qty(self):
#         if self.delivery_qty > self.require_qty:
#             raise UserError('Deliver quantity is always less than or equal to require quantity!')
#
#     @api.onchange('product_id')
#     def _onchange_product_id(self):
#         if self.product_id:
#             if self._context.get('active_model') == 'freight.freight' and self._context.get('active_ids'):
#                 freight_ids = self.env['freight.freight'].browse(self._context.get('active_ids'))
#                 line_ids = freight_ids.mapped('freight_order_line_ids').filtered(
#                     lambda p: p.goods.id == self.product_id.id)
#                 self.require_qty = line_ids and sum(line_ids.mapped('total_quantity')) or 0
#                 if line_ids.__len__() == 1:
#                     self.lot_id = line_ids.lot_id.id
#             quant_ids = self.env['stock.quant'].search([('product_id', '=', self.product_id.id), ('quantity', '>', 0)])
#             location_ids = quant_ids and quant_ids.mapped('location_id').ids or []
#             domain = {'location_id': [('id', 'in', location_ids), ('usage', '=', 'internal')]}
#             return {'domain': domain}
