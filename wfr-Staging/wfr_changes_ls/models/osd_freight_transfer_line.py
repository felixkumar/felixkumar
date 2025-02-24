import datetime

from odoo import fields, models, _
from odoo.exceptions import ValidationError


class OSDFreightTransferLineInherit(models.Model):
    _inherit = 'osd.freight.transfer.line'

    def ibl_create_transfers(self):
        """
        Finds existing input transfers, confirms them and creates new internal transfers for them.
        :return: None
        """
        if self.is_osd_inventory_transfered:
            return True
        freight_id = self.freight_id
        picking_id = False
        if not freight_id:
            raise ValidationError("Unable to transfer inventory, Please contact Administrator!")

        destination_location_id = self.destination_location_id
        if not destination_location_id:
            raise ValidationError("Please select the location for transfer the inventory!")
        if not self.sku_id:
            raise ValidationError("Product not found in record!")
        picking_type = self.env['stock.picking.type'].search(
            [
                ('is_inventory_adjustment', '=', True),
                ('warehouse_id', '=', freight_id.warehouse_id.id),
                ('warehouse_id.company_id', '=', destination_location_id.company_id.id)
            ],
            limit=1)
        if not picking_type:
            raise ValidationError('Unable to found the internal transfer type in company of destination location')
        location_id = picking_type.default_location_src_id
        if not location_id:
            raise ValidationError("Source location is not configured!")
        if freight_id.pickup_schedule_date:
            scheduled_date = freight_id.pickup_schedule_date
        else:
            scheduled_date = datetime.datetime.today()
        picking_id = self.env['stock.picking'].create({
            'location_id': location_id.id,
            'location_dest_id': destination_location_id.id,
            'move_type': 'direct',
            'immediate_transfer': True,
            'picking_type_id': picking_type.id,
            'is_locked': True,
            'company_id': destination_location_id.company_id.id,
            'freight_record_id': freight_id.id,
            'origin': freight_id.name,
            'scheduled_date': scheduled_date
        })

        product_id = self.sku_id
        line_vals = {
            'name': self.sku_id.name,
            'location_id': picking_id.location_id.id,
            'location_dest_id': picking_id.location_dest_id.id,
            'picking_id': picking_id.id,
            'product_id': product_id.id,
            'product_uom': product_id.uom_id.id,
            'quantity_done': self.quantity,
            'product_uom_qty': self.quantity,
            'company_id': picking_id.company_id.id,
            'lot_ids': [(6, 0, self.lot_id.ids)],
        }

        self.env['stock.move'].create(line_vals)
        picking_id.write({'partner_id': False})
        move_ids_without_package = picking_id.move_ids_without_package
        for move_id in move_ids_without_package:
            move_id.picking_type_id = picking_id.picking_type_id.id
        if self.lot_id:
            picking_id.move_line_ids.write({'lot_id': self.lot_id.id})
        freight_id.picking_ids = [(4, picking_id.id)]

    def osd_transfer_inventory(self):
        """
        Either finds existing transfers or creates new transfers and confirms them when the
        'Receive' button is clicked.
        :return: None
        """
        if self.is_osd_inventory_transfered:
            return True
        freight_id = self.freight_id
        picking_id = False
        if not freight_id:
            raise ValidationError("Unable to transfer inventory, Please contact Administrator!")
        if freight_id.picking_ids:
            pickings_ids = self.env['stock.picking'].search([('freight_record_id', '=', freight_id.id),
                                                             ('state', '!=', 'done')])
            picking_id = pickings_ids.filtered(lambda x:
                                               x.move_ids_without_package[0].product_id.id == self.sku_id.id)
            if picking_id:
                if picking_id.move_ids_without_package[0].product_uom_qty != self.quantity:
                    picking_id.move_ids_without_package[0].product_uom_qty = self.quantity
                    line_id = self.freight_id.freight_order_line_ids.filtered(lambda x: x.goods.id == self.sku_id.id)
                    line_id.total_quantity = self.quantity
                    line_id.total_value()
                    line_id.set_gross_weight()
                    line_id.onchange_required_pallet()
                picking_id.move_ids_without_package[0].quantity_done = self.quantity
        if not picking_id or not freight_id.picking_ids:
            destination_location_id = self.destination_location_id
            if not destination_location_id:
                raise ValidationError("Please select the location for transfer the inventory!")
            if not self.sku_id:
                raise ValidationError("Product not found in record!")
            picking_type = self.env['stock.picking.type'].search(
                [
                    ('is_inventory_adjustment', '=', True),
                    ('warehouse_id', '=', freight_id.warehouse_id.id),
                    ('warehouse_id.company_id', '=', destination_location_id.company_id.id)
                ],
                limit=1)
            if not picking_type:
                raise ValidationError('Unable to found the internal transfer in company of destination location')
            location_id = picking_type.default_location_src_id
            if not location_id:
                raise ValidationError("Source location is not configured!")
            picking_id = self.env['stock.picking'].create({
                'location_id': location_id.id,
                'location_dest_id': destination_location_id.id,
                'move_type': 'direct',
                'immediate_transfer': True,
                'picking_type_id': picking_type.id,
                'is_locked': True,
                'company_id': destination_location_id.company_id.id,
                'freight_record_id': freight_id.id,
                'origin': freight_id.name,
            })
            product_id = self.sku_id
            line_vals = {
                'name': self.sku_id.name,
                'location_id': picking_id.location_id.id,
                'location_dest_id': picking_id.location_dest_id.id,
                'picking_id': picking_id.id,
                'product_id': product_id.id,
                'product_uom': product_id.uom_id.id,
                'quantity_done': self.quantity,
                'product_uom_qty': self.quantity,
                'company_id': picking_id.company_id.id,
                'lot_ids': [(6, 0, self.lot_id.ids)],
            }
            self.env['stock.move'].create(line_vals)
            picking_id.write({'partner_id': False})
            move_ids_without_package = picking_id.move_ids_without_package
            for move_id in move_ids_without_package:
                move_id.picking_type_id = picking_id.picking_type_id.id
        picking_id.action_assign()
        picking_id.action_confirm()
        if self.lot_id:
            picking_id.move_line_ids.write({'lot_id': self.lot_id.id})
        picking_id.button_validate()
        freight_id.picking_ids = [(4, picking_id.id)]
        freight_id.transferred_date = fields.Date.today()
        self.is_osd_inventory_transfered = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': 'Inbounds has been Received',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }}
