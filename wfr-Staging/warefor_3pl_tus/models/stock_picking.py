# -*- coding: utf-8 -*-

import re
import werkzeug
import functools
import io
import base64
import qrcode
import logging

from odoo.osv import expression
from odoo import models, fields, api, _
from odoo.http import request
from odoo.exceptions import UserError
from odoo.tests import Form

_logger = logging.getLogger(__name__)

compress = functools.partial(re.sub, r'\s', '')
ALGORITHM = 'sha1'
DIGITS = 6
TIMESTEP = 30
BLOCK_USER = [1580]


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def unlink(self):
        freight_record_id = self.freight_record_id
        res = super(StockPicking, self).unlink()
        if freight_record_id:
            freight_record_id._compute_picking_ids()
        return res

    @api.depends('move_line_ids.result_package_id', 'move_line_ids.result_package_id.shipping_weight', 'weight_bulk')
    def _compute_shipping_weight(self):
        for picking in self.sudo():
            # if shipping weight is not assigned => default to calculated product weight
            picking.shipping_weight = (
                picking.weight_bulk +
                sum(pack.shipping_weight or pack.weight for pack in picking.package_ids.sudo())
            )

    @api.onchange('date_done')
    def onchange_affective_date(self):
        for rec in self:
            rec._origin.sudo().move_line_ids.write({'date': rec.date_done})
            for move in rec.move_ids.account_move_ids:
                if move.state not in ['posted', 'cancel']:
                    rec.move_ids.account_move_ids._origin.sudo().write({'date': rec.date_done})
            if rec.freight_record_id:
                if 'pick' in rec.name.lower():
                    rec.freight_record_id.pick_date = rec.date_done
                if 'pack' in rec.name.lower():
                    rec.freight_record_id.pack_date = rec.date_done
                if 'out' in rec.name.lower():
                    rec.freight_record_id.out_date = rec.date_done

    def update_truck_driver_signature(self):
        action = self.env["ir.actions.actions"]._for_xml_id("warefor_3pl_tus.action_truck_driver_signature_wizard")
        action['context'] = {'default_picking_id': self.id}
        return action

    def update_warehouse_manager_signature(self):
        action = self.env["ir.actions.actions"]._for_xml_id("warefor_3pl_tus.action_warehouse_manager_signature_wizard")
        action['context'] = {'default_picking_id': self.id}
        return action

    def button_validate(self):
        # Updated the picking order with sudo user for validating another company picking order
        res = False
        for rec in self:
            rec = rec.sudo()

            for lines in rec.move_ids:
                if lines.location_id.is_inventory_adjustment_location or lines.location_id.usage == 'supplier':
                    continue
                product_id = rec.env['product.product'].with_context(location=rec.location_id.ids).browse(
                    lines.product_id.id)
                product_qty = sum(lines.mapped('product_uom_qty')) or 0
                reserved_product_qty = sum(lines.mapped('reserved_availability')) or 0
                product_qty = product_qty - reserved_product_qty
                if product_id.qty_available < product_qty and rec.location_id.usage not in ['customer', 'supplier']:
                    raise UserError(_("{} is not available in this quantity in Location {}".format(product_id.name,
                                                                                                      rec.location_id.name)))
            # rec.with_context(skip_process=True).onchange_purchase_order_id()

            # res = super(StockPicking, self.sudo()).button_validate()

            if rec.freight_record_id:
                stage_id = rec.env.ref('mc_freight_app.create_shipment', False)
                if stage_id:
                    rec.freight_record_id.write({'stage_id': stage_id.id})
                # if rec.freight_record_id.is_outbound:
                #     rec.freight_record_id.outbound_stage_id = rec.env.ref('mc_freight_app.invoiced_outbound').id
                rec.freight_record_id.is_shipped = True
            # rec._generate_qrcode()
            # if rec.move_pallet_in_rack_location:
            #     rec.move_pallets_in_rack_locations()
            if rec.next_location_id:
                rec.move_pallet_in_logistic()
            # if rec.receipt_picking_id and not rec._context.get('skip_pallet'):
            #     pallet_batch_ids = rec.receipt_picking_id.pallet_batch_ids or rec.pallet_batch_ids
            #     for pallet in pallet_batch_ids:
            #         pallet.write({
            #             'start_date': fields.Date.today(),
            #             'is_enabled': True,
            #             'state': 'in_progress',
            #         })
            rec.with_context(skip_process=True).onchange_purchase_order_id()
            # picking_ids = rec.custom_internal_transfer_id.picking_ids.filtered(lambda p: not p.state in ['done', 'cancel'])
            # if not picking_ids and rec.custom_internal_transfer_id:
            #     rec.custom_internal_transfer_id.internal_transfer_stage_id = 'done'
            #     if rec.custom_internal_transfer_id.internal_transfer_stage_id == 'done':
            #         rec.custom_internal_transfer_id.active = False
            # # archive_internal_transfer = rec.custom_internal_transfer_id.picking_ids.filtered(lambda p: not p.state in ['done'])
            # transfer_line = rec.custom_internal_transfer_id.internal_transfer_ids.filtered(lambda i: i.picking_id == rec and rec.state in ['done', 'cancel'])
            # if transfer_line:
            #     transfer_line.is_validated = True

                # For Updating Quantity for OXFORD COMPANY when Sale order delivery will be done
                # if rec.sale_id and rec.sale_id.company_id.is_oxford:
                #     picking_ids = rec.sale_id.picking_ids.filtered(lambda x: x.state == 'done' and
                #                                                               x.picking_type_code == 'outgoing')
                #     for picking in picking_ids:
                #         for move_line in picking.move_ids_without_package:
                #             if picking.sale_id.company_id in move_line.product_id.company_ids:
                #                 quant_id = rec.env['stock.quant'].search([('product_id', 'in', move_line.product_id.ids),
                #                                                            ('location_id.is_virtual_location', '=', True)])
                #                 if quant_id:
                #                     quant_id[0].quantity -= move_line.quantity_done

            confirm_related_transfer = rec.env['ir.config_parameter'].sudo().get_param(
                'warefor_3pl_tus.confirm_related_transfer')

            if confirm_related_transfer and not rec._context.get('confirm_related_transfer') and rec.freight_record_id:
                # ADDED NEW CONDITION FOR VALIDATING ONLY OXFORD COMPANY TRANSFER IF LINKED
                if rec.freight_picking_id and not rec.freight_picking_id.sale_id.edi_po_number and rec.company_id.is_logistics and rec.freight_picking_id.company_id.company_code == 'OXF':
                    rec.freight_picking_id.process_by_cron = True

        res = super(StockPicking, self.sudo()).button_validate()
        return res

    # @api.depends('picking_type_id', 'pallet_batch_id')
    def _generate_qrcode(self):
        for sp in self:
            input_data = ""
            input_data += "Name: " + sp.name if sp.name else ""
            input_data += "\nDelivery Address: " + sp.partner_id.name if sp.partner_id else ""
            input_data += "\nOperation Type: " + sp.picking_type_id.name if sp.picking_type_id else ""
            input_data += "\nSource Location: " + sp.location_id.name if sp.location_id else ""
            input_data += "\nDestination Location: " + sp.location_dest_id.name if sp.location_dest_id else ""
            input_data += "\nBack Order: " + sp.backorder_id.name if sp.backorder_id else ""
            pallet_data = ""
            for pallet in sp.pallet_batch_ids:
                if pallet_data:
                    pallet_data += "\n\t" + pallet.name
                else:
                    pallet_data += "\nPallets:\n\t" + pallet.name
            input_data += pallet_data
            product_data = ""
            for sm in sp.move_ids_without_package:
                if product_data:
                    product_data += "\n\t" + "Name: " + sm.product_id.name + " | Qty: " + str(sm.product_uom_qty)
                else:
                    product_data += "\nProduct Details:\n\t" + "Name: " + sm.product_id.name + " | Qty: " + str(
                        sm.product_uom_qty)
            input_data += product_data
            try:
                data = io.BytesIO()
                qr = qrcode.QRCode(version=1, box_size=4, border=5)
                qr.add_data(input_data)
                qr.make(fit=True)
                img = qr.make_image(fill='black', back_color='white')
                img.save(data, optimise=True, format='PNG')
                sp.qrcode = base64.b64encode(data.getvalue()).decode()
            except Exception as e:
                _logger.error("Unable to generate QR code:{}".format(e))

        # user_id = self.env['res.users'].browse(self._uid)
        # global_issuer = request and request.httprequest.host.split(':', 1)[0]
        # for w in self:
        #     product_details = ""
        #     pallet_details = ""
        #     for pallet in self.pallet_batch_ids:
        #         if pallet_details:
        #             pallet_details += "_ID_{}_NAME_{}".format(pallet.id, pallet.name)
        #         else:
        #             pallet_details += "ID_{}_NAME_{}".format(pallet.id, pallet.name)
        #     for product_line in w.move_ids_without_package.filtered(lambda p: p.product_id):
        #         if product_details:
        #             product_details += "_ID_{}_NAME_{}_QTY_{}".format(product_line.product_id.id,
        #                                                               product_line.product_id.name,
        #                                                               product_line.product_uom_qty)
        #             # product_details += "_ID_{}_QTY_{}_RTLPR_{}_UOM_{}".format(product_line.product_id.id,
        #             #                                                           product_line.product_uom_qty,
        #             #                                                           product_line.product_id.lst_price,
        #             #                                                           product_line.product_uom.name)
        #         else:
        #             product_details += "ID_{}_NAME_{}_QTY_{}".format(product_line.product_id.id,
        #                                                              product_line.product_id.name,
        #                                                              product_line.product_uom_qty)
        #             # product_details += "ID_{}_QTY_{}_RTLPR_{}_UOM_{}".format(product_line.product_id.id,
        #             #                                                   product_line.product_uom_qty,
        #             #                                                   product_line.product_id.lst_price, product_line.product_uom.name)
        #     issuer = global_issuer
        #     url = werkzeug.urls.url_unparse((
        #         'otpauth', 'totp',
        #         werkzeug.urls.url_quote(f'{issuer}:{user_id.login}', safe=':'),
        #         werkzeug.urls.url_encode({
        #             # 'secret': compress("secret_secret_test"),
        #             # 'customer_details': str(w.partner_id.name) if w.partner_id.name else "None",
        #             'pallet': pallet_details,
        #             'product_details': product_details,
        #             # 'src_location': str(w.location_id.display_name) if w.location_id.display_name else "None",
        #             # 'dest_location': str(w.location_dest_id.display_name) if w.location_dest_id.display_name else "None",
        #             # 'special_note': str(w.note) if w.note else "None",
        #             'issuer': issuer,
        #             # apparently a lowercase hash name is anathema to google
        #             # authenticator (error) and passlib (no token)
        #             'algorithm': ALGORITHM.upper(),
        #             'digits': DIGITS,
        #             'period': TIMESTEP,
        #         }), ''
        #     ))
        #
        #     data = io.BytesIO()
        #     import qrcode
        #     qrcode.make(url.encode(), box_size=4).save(data, optimise=True, format='PNG')
        #     w.qrcode = base64.b64encode(data.getvalue()).decode()

    box_id = fields.Many2one(comodel_name="product.3pl.box.tus", string="3PL Box")
    pallet_id = fields.Many2one(comodel_name="pallet.batch.tus", string="Pallet")
    pallet_batch_ids = fields.One2many("pallet.batch.tus", "picking_id", string="Pallet",
                                       domain="[('store_type', '=', 'product')]")
    qrcode = fields.Binary(string="Barcode")
    receipt_picking_id = fields.Many2one(comodel_name="stock.picking", string="Receipt Transfer",
                                         domain="[('picking_type_code', '=', 'incoming')]")
    receipt_pallet_name = fields.Char(string="Pallet Name", required=False, )
    next_location_id = fields.Many2one('stock.location', 'Next Location')
    moved_picking_id = fields.Many2one(comodel_name="stock.picking", string="Moved Inventory",
                                       domain="[('picking_type_code', '=', 'internal')]")
    is_use_pallet_stock = fields.Boolean("Is Use Pallet Stock?")
    move_pallet_in_rack_location = fields.Boolean("Move Pallets In Rack Locations?")
    freight_record_id = fields.Many2one("freight.freight", string="PL Record", domain=lambda self: [('active', 'in', [False,True])])
    signature_name = fields.Char(string="Signature Name")

    warehouse_manager_signature = fields.Binary(string="Signature")
    # truck_driver_name = fields.Char(string="Driver Name")
    truck_driver_name = fields.Many2one(comodel_name="truck.driver.name", string="Driver Name")
    truck_driver_signature = fields.Binary(string="Signature", related="truck_driver_name.signature")
    truck_driver_sign_date = fields.Datetime(string="Truck Driver Signature Date", related="truck_driver_name.create_date")
    warehouse_manager_sign_date = fields.Date(string="Warehouse Manager Signature Date")
    arrive_time = fields.Datetime(string='Arrive Time')
    seal_number = fields.Char(related="freight_record_id.seal_number_inbound",readonly=False)
    trailer = fields.Char(string="Trailer")

    purchase_order_id = fields.Many2one("purchase.order", string="Purchase Order")
    custom_internal_transfer_id = fields.Many2one("warefor.internal.transfer", string="Pallet")
    who_record_count = fields.Integer(string='Transfers Count', copy=False)

    freight_picking_id = fields.Many2one(comodel_name="stock.picking", string="Related Transfer")

    detail_location_id = fields.Many2one(comodel_name="stock.location", compute='_detail_stock_location', store=True,
                                         string="Detailed From")
    process_by_cron = fields.Boolean("Is Process By Schedule Action?", default=False)

    @api.depends("move_line_ids")
    def _detail_stock_location(self):
        for rec in self:
            move_line_ids = rec.move_line_ids.filtered(lambda x: x.location_id)
            if move_line_ids:
                rec.detail_location_id = move_line_ids[0].location_id.id
            else:
                rec.detail_location_id = rec.location_id

    def button_who_record(self):
        view_id = self.env.ref('warefor_3pl_tus.warefor_internal_transfer_form_view').id
        context = self._context.copy()
        return {
            'name': 'freight_freight_osd_transfer',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_model': 'warefor.internal.transfer',
            'type': 'ir.actions.act_window',
            'res_id': self.custom_internal_transfer_id.id,
            'target': 'self',
            'context': context,
        }

    @api.onchange('purchase_order_id')
    def onchange_purchase_order_id(self):
        for record in self:
            if record.purchase_order_id:
                record.purchase_order_id.picking_ids = [(4, record._origin.id)]
                for move_line in record.move_ids:
                    po_line = record.purchase_order_id.order_line.filtered(
                        lambda l: l.product_id.id == move_line.product_id.id and l.product_qty == move_line.product_qty)
                    if po_line and move_line.id not in po_line.move_ids.ids:
                        rec_po_line = po_line.filtered(lambda l: not l.move_ids)
                        rec_po_line = rec_po_line or po_line
                        move_line.purchase_line_id = rec_po_line[-1].id
                        rec_po_line[-1].move_ids = [(4, move_line.id)]
                record.purchase_order_id._compute_picking()
            elif not self._context.get('skip_process'):
                po_id = self.env["purchase.order"].search([('picking_ids', 'in', record._origin.id)])
                po_id.order_line.move_ids = [(3, record.move_ids.ids)]
                po_id.picking_ids = [(3, record._origin.id)]
                # record.move_ids.write({'purchase_line_id': False})
                po_id._compute_picking()

    # ToDo: Override field to edit the destination location when transfer is in the ready state.
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_dest_id,
        check_company=True, required=True,
        states={'draft': [('readonly', False)], 'waiting': [('readonly', False)], 'assigned': [('readonly', False)]})

    @api.model_create_multi
    def create(self, vals):
        res = super(StockPicking, self).create(vals)
        return_name = res.origin and res.origin.split(' ') or []
        if return_name and 'Return' in return_name:
            name = return_name[-1]
            picking_id = self.search([('name', '=', name)], limit=1)
            freight_record_id = picking_id.freight_record_id
            if picking_id and freight_record_id:
                res.freight_record_id = freight_record_id
                freight_record_id.picking_ids = [(4, res.id)]
                freight_record_id.osd_transfers_count += 1
                freight_record_id.osd_picking_ids = [(4, res.id)]
                freight_record_id.outbound_stage_id = self.env.ref('mc_freight_app.returns_outbound').id

        for val in vals:
            freight_record_id = self.env['freight.freight'].search([('name', '=', val.get('origin'))], limit=1)
            if freight_record_id:
                if res and freight_record_id:
                    res.freight_record_id = freight_record_id
                    freight_record_id.picking_ids = [(4, res.id)]
                    freight_record_id.osd_transfers_count += 1
                    freight_record_id.osd_picking_ids = [(4, res.id)]

        # By default ToDo button will be click when create a new transfer
        if res.picking_type_id.is_default_mark_todo:
            res.action_confirm()
        return res

    def write(self, values):
        res = super(StockPicking, self).write(values)
        for rec in self:
            if rec.freight_record_id:
                rec.freight_record_id.picking_ids = [(4, rec.id)]
                rec.freight_record_id._compute_picking_ids()
                # if 'date_done' in values:
                #     rec.freight_record_id.loading_start_date = rec.freight_record_id.loading_start_date or rec.date_done
                return_name = rec.origin and rec.origin.split(' ') or []
                if rec.freight_record_id and 'Return' not in return_name:
                    if rec.freight_record_id.fulfillment_method != 'e-commerce':
                        if 'pick' in rec.name.lower() and rec.state == 'done':
                            rec.freight_record_id.pick_date = rec.date_done
                            rec.freight_record_id.outbound_stage_id = self.env.ref('mc_freight_app.loading_outbound').id
                        if 'pack' in rec.name.lower() and rec.state == 'done':
                            rec.freight_record_id.pack_date = rec.date_done
                            rec.freight_record_id.outbound_stage_id = self.env.ref('mc_freight_app.loaded_outbound').id
                        if rec.picking_type_code == 'outgoing' and rec.state == 'done':
                            rec.freight_record_id.out_date = rec.date_done
                            rec.freight_record_id.outbound_stage_id = self.env.ref('mc_freight_app.shipped_outbound').id
                    else:
                        if 'pick' in rec.name.lower() and rec.state == 'done':
                            rec.freight_record_id.pick_date = rec.date_done
                            rec.freight_record_id.outbound_stage_id = self.env.ref('mc_freight_app.staged_outbound').id
                        if 'pack' in rec.name.lower() and rec.state == 'done':
                            rec.freight_record_id.pack_date = rec.date_done
                            rec.freight_record_id.outbound_stage_id = self.env.ref('mc_freight_app.loaded_outbound').id
                        if rec.picking_type_code == 'outgoing' and rec.state == 'done':
                            rec.freight_record_id.out_date = rec.date_done
                            rec.freight_record_id.outbound_stage_id = self.env.ref('mc_freight_app.shipped_outbound').id

            if rec.carrier_tracking_ref and rec.sale_id.freight_id:
                rec.sale_id.freight_id.update({"tracking_number" : rec.carrier_tracking_ref})
                pick_id = rec.sale_id.freight_id.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing')
                if pick_id:
                    self._cr.execute(f"update stock_picking set carrier_tracking_ref = '{rec.carrier_tracking_ref}', carrier_id = {rec.carrier_id.id} where id={pick_id.id}")
        return res

    @api.onchange('receipt_picking_id')
    def onchange_receipt_picking_id(self):
        """

        :return:
        """
        for record in self:
            pallet_ids = record.receipt_picking_id.pallet_batch_ids
            if record.receipt_picking_id.pallet_batch_ids:
                record.receipt_pallet_name = " | ".join(record.receipt_picking_id.pallet_batch_ids.mapped('name'))
                move_ids = record.move_ids
                if move_ids:
                    move_ids.unlink()
                for pallet in pallet_ids:
                    for product_line in pallet.product_ids:
                        self.env['stock.move'].create({
                            'name': product_line.product_id.name,
                            'location_id': record.location_id.id,
                            'location_dest_id': record.location_dest_id.id,
                            'picking_id': record.id,
                            'product_id': product_line.product_id.id,
                            'product_uom': product_line.product_id.uom_id.id,
                            'quantity_done': product_line.product_qty,
                            'product_uom_qty': product_line.product_qty,
                            'company_id': record.company_id.id
                        })

    def create_shipment_pallet(self, name="", product_id=False, qty=0, product_cost_id=False):
        """
        Create Pallet from incoming shipment and add the cost or fees from the added costs and fees in product
        :return: True
        """
        return True
        if self.pallet_batch_ids and not product_id:
            raise UserError(_("Pallet is already created for this incoming receipt!"))

        pallet_obj = self.env['pallet.batch.tus']
        pallet_product_line_obj = self.env['pallet.product.line']
        pallet_box_line_obj = self.env['pallet.box.line']

        pallet_box_line = {}
        pallet_product_line = {}
        # pallet_location_obj = self.env['stock.location.pallet']

        transit_app_id = self._context.get('transit_app') or self.freight_record_id

        package_id = self._context.get('is_package')

        store_type = package_id and 'box' or 'product'

        pallet_vals = {
            'name': name or self.name,
            'store_type': store_type,
            'warehouse_id': self.picking_type_id.warehouse_id.id,
            'picking_id': self.id,
            'transit_app_id': transit_app_id and transit_app_id.id,
            'markup_import_cost': transit_app_id and transit_app_id.markup_import_cost or 0
        }

        pallet_id = pallet_obj.create(pallet_vals)

        if store_type == 'box':
            product_package_ids = transit_app_id.product_package_ids
            pallet_box_line = {
                'box_id': package_id.package_id.id,
                'box_qty': package_id.package_per_pallet,
                'pallet_id': pallet_id.id
            }
            pallet_product_line = {
                'product_id': product_id.id,
                'product_qty': package_id.package_id.qty * qty,
                'pallet_id': pallet_id.id
            }
            if pallet_box_line:
                pallet_box_line_obj.create(pallet_box_line)

            if pallet_product_line:
                pallet_product_line_obj.create(pallet_product_line)
        else:
            pallet_product_line = {}
            if not product_id:
                for line in self.move_ids:
                    pallet_product_line = {
                        'product_id': line.product_id.id,
                        'product_qty': line.product_uom_qty,
                        'pallet_id': pallet_id.id
                    }
            else:
                pallet_product_line = {
                    'product_id': product_id.id,
                    'product_qty': qty,
                    'pallet_id': pallet_id.id
                }
                pallet_id.message_post(body="Created pallet from confirmed purchase order {}".format(self.name))

            if pallet_product_line:
                pallet_product_line_obj.create(pallet_product_line)

        # location_line = {
        #     'pallet_batch_id': pallet_id.id,
        #     'type': 'row',
        #     'code': 1,
        #     'stock_location_id': self.location_dest_id.id
        # }
        # pallet_location_obj.create(location_line)
        if product_cost_id:
            import_cost_ids = []
            storage_cost_ids = []
            vas_cost_ids = []
            fob_cost_ids = []
            total_pallet = self._context.get('is_split')
            if self._context.get('is_split'):
                for import_cost_id in product_cost_id.import_cost_ids:
                    import_cost_ids.append((0, 0, {
                        'name': import_cost_id.name,
                        'product_id': import_cost_id.product_id.id,
                        'actual_cost': import_cost_id.actual_cost / total_pallet,
                        # 'processing_fee_per': import_cost_id.processing_fee_per,
                    }))
                for storage_cost_id in product_cost_id.storage_cost_ids:
                    storage_cost_ids.append((0, 0, {
                        'name': storage_cost_id.name,
                        'product_id': storage_cost_id.product_id.id,
                        'unit_of_measure': storage_cost_id.unit_of_measure,
                        'total_pallet': storage_cost_id.total_pallet,
                        'total_cubic_feet': storage_cost_id.total_cubic_feet,
                        'unit_price': storage_cost_id.unit_price,
                        'total_cost': storage_cost_id.total_cost,
                    }))
                for vas_cost_id in product_cost_id.vas_cost_ids:
                    vas_cost_ids.append((0, 0, {
                        'name': vas_cost_id.name,
                        'product_id': vas_cost_id.product_id.id,
                        'unit_of_measure': vas_cost_id.unit_of_measure,
                        'total_cost': vas_cost_id.total_cost / total_pallet,
                    }))
            else:
                for import_cost_id in product_cost_id.import_cost_ids:
                    import_cost_ids.append((0, 0, {
                        'name': import_cost_id.name,
                        'product_id': import_cost_id.product_id.id,
                        'actual_cost': import_cost_id.actual_cost,
                        # 'processing_fee_per': import_cost_id.processing_fee_per,
                    }))
                for storage_cost_id in product_cost_id.storage_cost_ids:
                    storage_cost_ids.append((0, 0, {
                        'name': storage_cost_id.name,
                        'product_id': storage_cost_id.product_id.id,
                        'unit_of_measure': storage_cost_id.unit_of_measure,
                        'total_pallet': storage_cost_id.total_pallet,
                        'total_cubic_feet': storage_cost_id.total_cubic_feet,
                        'unit_price': storage_cost_id.unit_price,
                        'total_cost': storage_cost_id.total_cost,
                    }))
                for vas_cost_id in product_cost_id.vas_cost_ids:
                    vas_cost_ids.append((0, 0, {
                        'name': vas_cost_id.name,
                        'product_id': vas_cost_id.product_id.id,
                        'unit_of_measure': vas_cost_id.unit_of_measure,
                        'total_cost': vas_cost_id.total_cost,
                    }))
            for fob_cost_id in product_cost_id.fob_cost_ids:
                fob_cost_ids.append((0, 0, {
                    'product_id': fob_cost_id.product_id.id,
                    'fob_per': fob_cost_id.fob_per,
                    'total_cost': fob_cost_id.total_cost,
                }))
            if vas_cost_ids or storage_cost_ids or import_cost_ids:
                pallet_id.write({"vas_cost_ids": vas_cost_ids, "storage_cost_ids": storage_cost_ids,
                                 "import_cost_ids": import_cost_ids, "fob_cost_ids": fob_cost_ids})
        return True

    def move_pallet_in_next_location(self):
        picking_type = self.env['stock.picking.type'].search(
            [('code', '=', 'internal'), ('warehouse_id.company_id', '=', self.next_location_id.company_id.id)], limit=1)
        if picking_type:
            picking_id = self.env['stock.picking'].create({
                'location_id': self.location_dest_id.id,
                'location_dest_id': self.next_location_id.id,
                'move_type': 'direct',
                'immediate_transfer': True,
                'picking_type_id': picking_type.id,
                'receipt_picking_id': self.id,
                'is_locked': True,
                'company_id': self.next_location_id.company_id.id
            })
            for move_line in self.move_ids:
                self.env['stock.move'].create({
                    'name': move_line.product_id.name,
                    'location_id': picking_id.location_id.id,
                    'location_dest_id': picking_id.location_dest_id.id,
                    'picking_id': picking_id.id,
                    'product_id': move_line.product_id.id,
                    'product_uom': move_line.product_id.uom_id.id,
                    'quantity_done': move_line.product_uom_qty,
                    'product_uom_qty': move_line.product_uom_qty,
                    'company_id': picking_id.company_id.id
                })
            self.write({'moved_picking_id': picking_id.id})
            picking_id.write({'partner_id': False})
            move_ids_without_package = picking_id.move_ids_without_package
            for move_id in move_ids_without_package:
                move_id.picking_type_id = picking_id.picking_type_id.id
            picking_id.action_confirm()
        else:
            raise ValueError('Unable to found the internal transfer in company of destination location')

    def move_pallet_in_logistic(self):
        """

        :return:
        """
        next_location_id = self.next_location_id
        if self.next_location_id:
            pallet_batch_ids = self.pallet_batch_ids
            if pallet_batch_ids:
                logistics_company = self.env["res.company"].search([('is_logistics', '=', True)], limit=1)
                if not logistics_company:
                    raise UserError("Please configure the Logistic company!")
                picking_type = self.env['stock.picking.type'].search(
                    [('code', '=', 'internal'),
                     ('warehouse_id.company_id', 'in', logistics_company.ids)], limit=1)
                location_dest_id = self.location_dest_id.id
                if picking_type:
                    picking_id = self.env['stock.picking'].with_context(skip_pallet=True).create({
                        'location_id': location_dest_id,
                        'location_dest_id': next_location_id.id,
                        'move_type': 'direct',
                        'immediate_transfer': True,
                        'picking_type_id': picking_type.id,
                        'receipt_picking_id': self.id,
                        'is_locked': True,
                        'company_id': logistics_company.id,
                        'pallet_batch_ids': [[6, 0, pallet_batch_ids.ids]]
                    })
                    for pallet in pallet_batch_ids:
                        for product_line in pallet.product_ids:
                            product_id = product_line.product_id
                            self.env['stock.move'].create({
                                'name': product_id.name,
                                'location_id': picking_id.location_id.id,
                                'location_dest_id': picking_id.location_dest_id.id,
                                'picking_id': picking_id.id,
                                'product_id': product_id.id,
                                'product_uom': product_id.uom_id.id,
                                'quantity_done': product_line.product_qty,
                                'product_uom_qty': product_line.product_qty,
                                'company_id': logistics_company.id
                            })
                        pallet.write({
                            'start_date': fields.Date.today(),
                            'billing_from': fields.Date.today(),
                            'is_enabled': True,
                            'state': 'in_progress',
                            'location_id': next_location_id.id,
                            'current_location_id': next_location_id.id
                        })
                    self.write({'moved_picking_id': picking_id.id})
                    picking_id.write({'partner_id': False})
                    move_ids_without_package = picking_id.move_ids_without_package
                    for move_id in move_ids_without_package:
                        move_id.picking_type_id = picking_id.picking_type_id.id
                    picking_id.action_confirm()
                    picking_id.button_validate()
                    next_location_id.stored_pallet = len(pallet_batch_ids) + next_location_id.stored_pallet
            return True
        else:
            raise UserError("Unable to transfer the pallet in next location")

    def move_pallets_in_rack_locations(self):
        """
        Move the Pallets into the particular location from the transit location, find the available locations for
        moving the Pallets as per the configured store number of Pallets in company configuration
        Author: Prakash Makwana
        Date: 12th Aug, 2021.
        :return:True
        """
        if self.move_pallet_in_rack_location:
            pallet_batch_ids = self.pallet_batch_ids
            total_pallet = len(pallet_batch_ids)
            if pallet_batch_ids:
                logistic_company = self.env["res.company"].search([('is_logistics', '=', True)], limit=1)
                pallet_in_location = logistic_company.pallet_in_location
                rack_in_location = logistic_company.rack_in_location
                if pallet_in_location and rack_in_location:
                    # Number of racks need to fit the pallets
                    other_pallets = total_pallet % pallet_in_location if total_pallet > pallet_in_location else total_pallet
                    need_number_of_racks = int(total_pallet / pallet_in_location)
                    if other_pallets:
                        need_number_of_racks += 1
                    logistics_company = self.env['res.company'].search([('is_logistics', '=', True)], limit=1)
                    if not logistics_company:
                        raise UserError("Please configure the Logistic company!")
                    rack_locations_ids = self.env['stock.location'].search(
                        [
                            ("stored_pallet", "<", logistics_company.pallet_in_location),
                            ("is_rack", "=", True),
                            ('company_id', '=', logistics_company.id)
                        ], limit=need_number_of_racks, order="id")
                    if len(rack_locations_ids) != need_number_of_racks:
                        raise UserError("There are not available Racks(Locations) for storing the Pallets!")
                    picking_type = self.env['stock.picking.type'].search(
                        [('code', '=', 'internal'),
                         ('warehouse_id.company_id', 'in', logistics_company.ids)], limit=1)
                    location_dest_id = self.location_dest_id.id
                    if picking_type:
                        for rack_locations_id in rack_locations_ids:
                            moving_pallet = pallet_batch_ids[:pallet_in_location]
                            pallet_batch_ids -= moving_pallet
                            picking_id = self.env['stock.picking'].with_context(skip_pallet=True).create({
                                'location_id': location_dest_id,
                                'location_dest_id': rack_locations_id.id,
                                'move_type': 'direct',
                                'immediate_transfer': True,
                                'picking_type_id': picking_type.id,
                                'receipt_picking_id': self.id,
                                'is_locked': True,
                                'company_id': logistics_company.id,
                                'pallet_batch_ids': [[6, 0, moving_pallet.ids]]
                            })
                            for pallet in moving_pallet:
                                for product_line in pallet.product_ids:
                                    product_id = product_line.product_id
                                    self.env['stock.move'].create({
                                        'name': product_id.name,
                                        'location_id': picking_id.location_id.id,
                                        'location_dest_id': picking_id.location_dest_id.id,
                                        'picking_id': picking_id.id,
                                        'product_id': product_id.id,
                                        'product_uom': product_id.uom_id.id,
                                        'quantity_done': product_line.product_qty,
                                        'product_uom_qty': product_line.product_qty,
                                        'company_id': logistics_company.id
                                    })
                            self.write({'moved_picking_id': picking_id.id})
                            picking_id.write({'partner_id': False})
                            move_ids_without_package = picking_id.move_ids_without_package
                            for move_id in move_ids_without_package:
                                move_id.picking_type_id = picking_id.picking_type_id.id
                            picking_id.action_confirm()
                            picking_id.button_validate()
                            for pallet in moving_pallet:
                                pallet.write({
                                    'start_date': fields.Date.today(),
                                    'billing_from': fields.Date.today(),
                                    'is_enabled': True,
                                    'state': 'in_progress',
                                    'location_id': rack_locations_id.id,
                                    'current_location_id': rack_locations_id.id
                                })
                            rack_locations_id.stored_pallet = len(moving_pallet)
            return True
        else:
            raise UserError(
                "Unable to transfer the pallet in rack location, there isn't marked the 'Move pallet in rack locations'")

    def validated_linked_transfers(self):
        picking_ids = self.env['stock.picking'].sudo().search(
            [('state', '=', 'assigned'), ('process_by_cron', '=', True)])
        for picking in picking_ids:
            wiz = picking.with_context(skip_sms=True).button_validate()
            # Immediate Transfer
            if wiz and isinstance(wiz, dict) and wiz.get('res_model', False) == 'stock.immediate.transfer':
                try:
                    wiz = Form(self.env['stock.immediate.transfer'].with_context(wiz['context'])).save()
                    wiz = wiz.process()
                except Exception as exception:
                    _logger.info("stock.immediate.transfer : Error {} comes at the time of "
                                 "creating back order in picking : {}".format(exception, picking.id))
                    continue
        return True


class StockQuant(models.Model):
    _inherit = 'stock.quant'
    _description = 'Stock Quant'

    qty_per_pallet = fields.Float("Quantity Per Pallet", related='product_id.product_per_pallet', tracking=True)
    number_of_pallets = fields.Float("Number of Pallets", compute="_compute_irequired_pallet")
    warehouse_id = fields.Many2one('stock.warehouse', related='location_id.warehouse_id', store=True)
    category_id = fields.Many2one(comodel_name='product.category', related="product_id.categ_id", string="Product Category", store=True)

    @api.depends("inventory_quantity")
    def _compute_irequired_pallet(self):
        for rec in self:
            if rec.qty_per_pallet > 0:
                rec.number_of_pallets = rec.available_quantity / rec.qty_per_pallet
            else:
                rec.number_of_pallets = 0

    def _get_gather_domain(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False):
        domain = super(StockQuant, self)._get_gather_domain(product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False)
        if self._context.get('is_freight_process'):
            domain = expression.AND([[('location_id.is_omit_on_source_location', '=', False)], domain])
        return domain

    @api.model
    def _get_inventory_fields_create(self):
        """ Returns a list of fields user can edit when he want to create a quant in `inventory_mode`.
        """
        res = super()._get_inventory_fields_create()
        res += ['warehouse_id', 'in_date']
        return res


class StockLot(models.Model):
    _inherit = 'stock.lot'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.user.has_group('user_warehouse_restriction.user_warehouse_restriction_group_user'):
            domain = expression.OR([[['product_id', 'in', self.env['product.product'].search([]).ids]], domain])
        return super(StockLot, self).search_read(domain, fields, offset, limit, order)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.user.has_group('user_warehouse_restriction.user_warehouse_restriction_group_user'):
            domain = expression.OR([[['product_id', 'in', self.env['product.product'].search([]).ids]], domain])
        return super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)

    @api.model
    def get_views(self, views, options=None):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            options['toolbar'] = False
        res = super().get_views(views, options)
        # if self.env.user.id in BLOCK_USER and res.get('views'):
        #     if res.get('views', {}).get('list', {}).get('arch', "") and 'tree' in res.get('views', {}).get('list',
        #                                                                                                    {}).get(
        #             'arch', ""):
        #         data = res['views']['list']['arch']
        #         data = data.replace("tree", 'tree create="false"', 1)
        #         res['views']['list']['arch'] = data
        #     if res.get('views', {}).get('form', {}).get('arch', "") and 'form' in res.get('views', {}).get('form',
        #                                                                                                    {}).get(
        #             'arch', ""):
        #         data = res['views']['form']['arch']
        #         data = data.replace("form", 'form create="false"', 1)
        #         res['views']['form']['arch'] = data
        #     if res.get('views', {}).get('kanban', {}).get('arch', "") and 'kanban' in res.get('views', {}).get('kanban',
        #                                                                                                        {}).get(
        #             'arch', ""):
        #         data = res['views']['kanban']['arch']
        #         data = data.replace("kanban", 'kanban create="false"', 1)
        #         res['views']['kanban']['arch'] = data
        return res

    def write(self, vals):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            raise UserError("You don't have enough access, Please contact your system administrator.")
        res = super(StockLot, self).write(vals)
        return res


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    @api.model
    def get_views(self, views, options=None):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            options['toolbar'] = False
        res = super().get_views(views, options)
        # if self.env.user.id in BLOCK_USER and res.get('views'):
        #     if res.get('views', {}).get('list', {}).get('arch', "") and 'tree' in res.get('views', {}).get('list',
        #                                                                                                    {}).get(
        #             'arch', ""):
        #         data = res['views']['list']['arch']
        #         data = data.replace("tree", 'tree create="false"', 1)
        #         res['views']['list']['arch'] = data
        #     if res.get('views', {}).get('form', {}).get('arch', "") and 'form' in res.get('views', {}).get('form',
        #                                                                                                    {}).get(
        #             'arch', ""):
        #         data = res['views']['form']['arch']
        #         data = data.replace("form", 'form create="false"', 1)
        #         res['views']['form']['arch'] = data
        #     if res.get('views', {}).get('kanban', {}).get('arch', "") and 'kanban' in res.get('views', {}).get('kanban',
        #                                                                                                        {}).get(
        #             'arch', ""):
        #         data = res['views']['kanban']['arch']
        #         data = data.replace("kanban", 'kanban create="false"', 1)
        #         res['views']['kanban']['arch'] = data
        return res

    def write(self, vals):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            raise UserError("You don't have enough access, Please contact your system administrator.")
        res = super(StockQuantPackage, self).write(vals)
        return res


class FreightPort(models.Model):
    _inherit = 'freight.port'

    @api.model
    def get_views(self, views, options=None):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            options['toolbar'] = False
        res = super().get_views(views, options)
        # if self.env.user.id in BLOCK_USER and res.get('views'):
        #     if res.get('views', {}).get('list', {}).get('arch', "") and 'tree' in res.get('views', {}).get('list',
        #                                                                                                    {}).get(
        #             'arch', ""):
        #         data = res['views']['list']['arch']
        #         data = data.replace("tree", 'tree create="false"', 1)
        #         res['views']['list']['arch'] = data
        #     if res.get('views', {}).get('form', {}).get('arch', "") and 'form' in res.get('views', {}).get('form',
        #                                                                                                    {}).get(
        #             'arch', ""):
        #         data = res['views']['form']['arch']
        #         data = data.replace("form", 'form create="false"', 1)
        #         res['views']['form']['arch'] = data
        #     if res.get('views', {}).get('kanban', {}).get('arch', "") and 'kanban' in res.get('views', {}).get('kanban',
        #                                                                                                        {}).get(
        #             'arch', ""):
        #         data = res['views']['kanban']['arch']
        #         data = data.replace("kanban", 'kanban create="false"', 1)
        #         res['views']['kanban']['arch'] = data
        return res

    def write(self, vals):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            raise UserError("You don't have enough access, Please contact your system administrator.")
        res = super(FreightPort, self).write(vals)
        return res


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def create_returns(self):
        """
        Use : Inherit create_returns method and mark export_order = False
        for prevent order export validation at time of validate return picking
        """
        res = super(ReturnPicking, self).create_returns()
        return res
