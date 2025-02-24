# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError


class FreightFreight(models.Model):
    _inherit = 'freight.freight'

    stock_move_ids = fields.One2many(
        'stock.move.reservation',
        'custom_sale_order_id',
        string="Stock Reservations",
        copy=False,
    )


class OsdFreightTransferLine(models.Model):
    _inherit = 'osd.freight.transfer.line'

    is_stock_reserve_created = fields.Boolean(
        string="Is Stock Created",
        copy=False,
    )

    def reservation_vals(self):

        vals = {
            'name': self.freight_id.name,
            'custom_so_line_id': self._origin.id,
            'product_id': self.sku_id.id,
            'product_uom_qty': self.quantity,
            'product_uom': self.sku_id.uom_id.id,
            'location_id': self.location_id.id,
            'product_lot_id': self.lot_id.id,
            'location_dest_id': self.location_id.id,
            'custom_sale_order_id': self._origin.freight_id.id,
            'reserve_request_date': fields.Datetime.now(),
            'reserve_request_user_id': self.env.uid,
            'state': 'reserved',
        }
        return vals

    def stock_vals(self):
        ctx = self._context.copy()
        stock_quant_id = self.env['stock.quant'].sudo().search([('product_id', '=', self.sku_id.id),
                                                                ('location_id', '=', self.location_id.id),
                                                                ('lot_id', '=', self.lot_id.id)])
        if stock_quant_id:
            available_qty = stock_quant_id.available_quantity - self.quantity
            reserved_qty = stock_quant_id.reserved_quantity + self.quantity
            vals = {
                'available_quantity': available_qty,
                'reserved_quantity': reserved_qty,
            }
            stock_quant_id.with_context(ctx).sudo().update(vals)
            self.on_hand_qty = stock_quant_id._get_available_quantity(self.sku_id, self.location_id)
        else:
            raise UserError(_("Stock is not found in the location."))

    def action_reservation_create(self):
        if not self.location_id:
            raise UserError(_("Please select the location to reserve the quantity!"))
        if self.quantity <= 0:
            raise UserError(_("Please select a quantity of more than zero."))
        if not self.is_stock_reserve_created:
            # if self.quantity > self.on_hand_qty:
            #     raise UserError(_("{} is not available in this quantity in Location {}".format(self.sku_id.name,
            #                                                                                    self.location_id.name)))
            vals = self.reservation_vals()
            ctx = self._context.copy()
            custom_reseravtion_obj = self.env['stock.move.reservation']
            self.stock_vals()
            self.write({'is_stock_reserve_created': True})
            return custom_reseravtion_obj.with_context(ctx).create(vals)
        # else:
        #     continue
            # raise UserError(_("You cannot reserve the quantities which is reserved already."))

    def stock_move_reservation_cancel(self):
        self.ensure_one()
        if self.is_stock_reserve_created:
            ctx = self._context.copy()
            stock_reservation_ids = self.env['stock.move.reservation'].sudo().search(
                [('custom_so_line_id', '=', self.id)])
            if stock_reservation_ids:
                stock_reservation_ids.with_context(ctx).sudo().update({
                    'state': 'reserve_cancel',
                })
        else:
            raise UserError(_("You cannot cancel the reserve the quantity which is not reserved."))

    def stock_quant_cancel_reserve(self):
        self.ensure_one()
        ctx = self._context.copy()
        stock_quant_obj = self.env['stock.quant'].sudo().search(
            [('product_id', '=', self.sku_id.id), ('location_id', '=', self.location_id.id),
             ('lot_id', '=', self.lot_id.id)])

        if stock_quant_obj:
            available_qty = stock_quant_obj.available_quantity + self.quantity
            reserved_qty = stock_quant_obj.reserved_quantity - self.quantity
            stock_quant_obj.with_context(ctx).sudo().update({
                'available_quantity': available_qty,
                'reserved_quantity': reserved_qty,
            })
            self.on_hand_qty = stock_quant_obj._get_available_quantity(self.sku_id, self.location_id)
        else:
            raise UserError(_("There is no stock in the location."))

    def action_reservation_cancel(self):
        self.stock_move_reservation_cancel()
        self.stock_quant_cancel_reserve()
