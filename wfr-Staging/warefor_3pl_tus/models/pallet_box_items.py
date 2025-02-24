# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PalletBoxItems(models.Model):
    _name = 'pallet.box.items'
    _description = 'Pallet Box Items'

    product_box_id = fields.Many2one(comodel_name="product.3pl.box.tus", string="Box", related="picking_id.box_id",
                                     store=True)
    pallet_id = fields.Many2one(comodel_name="pallet.batch.tus", string="Pallet")
    picking_id = fields.Many2one(comodel_name="stock.picking", string="Delivery Order")
    move_lines = fields.Many2many('stock.move', string="Stock Moves", compute="_compute_move_lines")

    @api.depends('picking_id')
    def _compute_move_lines(self):
        for record in self:
            record.move_lines = record.picking_id.move_ids
