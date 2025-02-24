# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MassPalletsMovement(models.TransientModel):
    """ This model will helps to move the multiple pallets at a time with the Purchase order """
    _name = 'mass.pallets.movement'
    _description = 'Mass Pallets Movement'

    purchase_id = fields.Many2one('purchase.order', string="Purchase Order")
    pallet_ids = fields.Many2many('pallet.batch.tus', string="Pallets")
    location_id = fields.Many2one('stock.location', string="Location")

    @api.onchange('purchase_id')
    def onchange_purchase_id(self):
        freight_ids = self.env['freight.freight'].search([('purchase_orders_ids', 'in', self.purchase_id.ids)])
        pallet_ids = freight_ids.pallet_ids.filtered(lambda p: not p.end_date)
        domain = {'pallet_ids': [('id', 'in', pallet_ids.ids)]}
        return {'domain': domain}

    def move_po_pallets(self):
        """
        Move the multiple pallets from pallet source location to selected destination location
        :return:
        """
        location_id = self.location_id
        if not location_id:
            raise ValidationError("Unable to found destination location for pallets!")
        for pallet in self.pallet_ids:
            pallet.with_context(pallet_location_id=location_id).transfer_inventory()
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "Yeah! Pallets are moved successfully.",
                'type': 'rainbow_man',
            }
        }
