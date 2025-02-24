# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import math


class StockMove(models.Model):
    _inherit = 'stock.move'

    pallet_id = fields.Many2one(comodel_name="pallet.batch.tus", string="Pallet")
    no_of_pallets = fields.Float(string='# of Pallets', compute='_get_no_of_pallet', store=True)

    @api.depends('quantity_done', 'product_uom_qty')
    def _get_no_of_pallet(self):
        for rec in self:
            product_per_pallet = rec.product_id.product_per_pallet
            qty = 0
            if rec.quantity_done > 0:
                qty = rec.quantity_done
            else:
                qty = rec.product_uom_qty
            if product_per_pallet > 0 and qty:
                rec.no_of_pallets = math.ceil(qty / product_per_pallet)
            else:
                rec.no_of_pallets = 0

    @api.onchange('pallet_id', 'product_uom_qty', 'product_id')
    def onchange_pallet_id(self):
        for record in self:
            pallet_id = record.pallet_id
            if pallet_id and record.product_uom_qty:
                pallet_line = pallet_id.product_ids.filtered(lambda p: p.product_id.id == record.product_id.id and record.product_uom_qty <= p.remaining_qty)
                pallet_line = pallet_line and pallet_line[0]
                if pallet_line and (record.product_uom_qty > pallet_line.remaining_qty):
                    raise ValidationError("Did not found the product quantity in a pallet.")
                elif not pallet_line:
                    raise ValidationError("Did not found the product quantity in a pallet.")
            elif pallet_id and not record.product_uom_qty:
                raise ValidationError("Did not found the product or product quantity in a pallet.")

    def write(self, values):
        res = super(StockMove, self).write(values)
        if any(['pallet_id' in values.keys(), 'product_uom_qty' in values.keys(), 'product_id' in values.keys()]):
            for record in self:
                if record.picking_id.is_use_pallet_stock:
                    pallet_id = record.pallet_id
                    if pallet_id and record.product_uom_qty:
                        pallet_line = pallet_id.product_ids.filtered(
                            lambda p: p.product_id.id == record.product_id.id and record.product_uom_qty <= p.remaining_qty)
                        pallet_line = pallet_line and pallet_line[0]
                        if pallet_line and (record.product_uom_qty <= pallet_line.remaining_qty):
                            pallet_line.sold_qty += record.product_uom_qty
        return res

    @api.model_create_multi
    def create(self, values):
        res = super(StockMove, self).create(values)
        for record in res:
            if record.picking_id.is_use_pallet_stock:
                pallet_id = record.pallet_id
                if pallet_id and record.product_uom_qty:
                    pallet_line = pallet_id.product_ids.filtered(
                        lambda p: p.product_id.id == record.product_id.id and record.product_uom_qty <= p.remaining_qty)
                    pallet_line = pallet_line and pallet_line[0]
                    if pallet_line and (record.product_uom_qty <= pallet_line.remaining_qty):
                        pallet_line.sold_qty += record.product_uom_qty
        return res


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    active = fields.Boolean(string='Active', default=True)
    no_of_pallets = fields.Float(string='# of Pallets', related='move_id.no_of_pallets')
