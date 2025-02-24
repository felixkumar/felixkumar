# -*- coding: utf-8 -*-


from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockMoveReservation(models.Model):
    _name = "stock.move.reservation"
    _inherits = {'stock.move': 'move_id'}
    _description = "Stock Reservation"

    reserve_code = fields.Char(
        string="Reservation Code",
        default="New",
        copy=False,
        readonly=True,
    )
    move_id = fields.Many2one(
        'stock.move',
        'Reservation Move',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
    custom_so_line_id = fields.Many2one(
        'osd.freight.transfer.line',
        string="Order Line",
        copy=False,
        readonly=True,
        ondelete='cascade',

    )
    product_lot_id = fields.Many2one('stock.lot', 'Lot #')
    custom_sale_order_id = fields.Many2one(
        'freight.freight',
        string='Freight Order',
        copy=False,
        readonly=True,
    )
    reserve_request_date = fields.Datetime(
        string="Reservation Date",
        copy=False,
        readonly=True,
    )
    reserve_request_user_id = fields.Many2one(
        'res.users',
        string='Reservation By',
        copy=False,
        readonly=True,
    )

    is_stock_reserve_cancelled = fields.Boolean(
        string="Is Stock Created",
        copy=False,
    )

    def action_product_reservation_cancel(self):
        self.ensure_one()
        if self.custom_so_line_id.is_stock_reserve_created:
            ctx = self._context.copy()
            stock_quant_obj = self.env['stock.quant'].sudo().search(
                [('product_id', '=', self.product_id.id), ('location_id', '=', self.location_id.id),
                 ('lot_id', '=', self.product_lot_id.id)])
            if stock_quant_obj:
                available_qty = stock_quant_obj.available_quantity + self.product_uom_qty
                reserved_qty = stock_quant_obj.reserved_quantity - self.product_uom_qty
                stock_quant_obj.with_context(ctx).sudo().update({
                    'available_quantity': available_qty,
                    'reserved_quantity': reserved_qty,
                })
                self.with_context(ctx).sudo().update({
                    'state': 'reserve_cancel',
                })
                self.custom_so_line_id.on_hand_qty = stock_quant_obj._get_available_quantity(self.custom_so_line_id.sku_id, self.location_id)
            else:
                raise UserError(_("There is no stock in the location."))
        self.is_stock_reserve_cancelled = True

    @api.model
    def create(self, vals):
        if vals.get('reserve_code', _('New')) == _('New'):
            vals['reserve_code'] = self.env['ir.sequence'].next_by_code('stock.move.reservation') or _('New')
        return super(StockMoveReservation, self).create(vals)


class StockMove(models.Model):
    _inherit = 'stock.move'

    state = fields.Selection(selection_add=[('reserved', 'Reserved'), ('reserve_cancel', 'Reserved Cancelled')])
