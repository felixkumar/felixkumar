# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import traceback
import logging

from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.float_utils import float_compare

from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    purchase_order_id = fields.Many2one("purchase.order", string="Purchase Order")
    freight_id = fields.Many2one("freight.freight", string="Freight Record")
    edi_po_number = fields.Char(string='EDI PO Number', help='Purchase order number from the EDI')
    edi_store_id = fields.Many2one("edi.customer.store", string="EDI Store ID")
    do_not_confirm = fields.Boolean(string='Do Not Confirm', default=False)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(SaleOrder, self).create(vals_list)
        if res.edi_po_number and res.partner_id.edi_store_id:
            res.edi_store_id = res.partner_id.edi_store_id.id
        return res

    @api.onchange('purchase_order_id')
    def on_change_purchase_order(self):
        for rec in self.filtered(lambda x: x.purchase_order_id.id):
            rec.purchase_order_id.sale_order_id = rec._origin.id

    def action_confirm(self):
        """ Inherited the default action_confirm method to send a confirmation email and create OBL record from SO.
        """
        _logger.info("warefor_3pl_tus, action_confirm: %s %s" % (self, self.mapped('state')))
        if self.company_id.is_oxford and self.website_id:
            self = self.with_context(is_oxford_process_web=True, is_sale_order_process_web=True)
        if self.company_id.is_oxford:
            self = self.with_context(is_oxford_process=True, is_sale_order_process=True)

        try:
            res = super(SaleOrder, self.sudo()).action_confirm()
        except Exception as e:
            res = False
            tr_error = traceback.format_exc()
            _logger.info(tr_error)
            raise UserError(tr_error)
        for rec in self:
            if rec.company_id.is_oxford and self.website_id:
                template_id = self.sudo().env.ref("warefor_3pl_tus.oxf_mail_template_sale_confirmation", False)
                rec.with_context(force_send=True).sudo().message_post_with_template(template_id.id,
                                                                             email_layout_xmlid='mail.mail_notification_light')

            if rec.company_id.is_oxford and rec.state != 'to_approve':
                is_fba = rec.order_line.filtered(lambda l: l.product_id.is_fba)
                if not is_fba and not rec.do_not_confirm:
                    rec.sudo().action_create_freight_record_from_so()

            picking_id = rec.picking_ids.filtered(lambda p: p.picking_type_id.code == 'outgoing')
            if picking_id and rec.carrier_id:
                picking_id.sudo().write({'carrier_id': rec.carrier_id.id})
        return res

    def _get_confirmation_template(self):
        """ Get the mail template sent on SO confirmation (or for confirmed SO's).

        :return: `mail.template` record or None if default template wasn't found
        """
        if self.company_id.is_oxford and self.website_id:
            return False
        return self.env.ref('sale.mail_template_sale_confirmation', raise_if_not_found=False)

    def action_create_freight_record_from_so(self):
        """
        Creating the freight record from the sale order
        Author: Prakash Makwana
        Date: 22th May, 2023.
        :return: True
        """
        freight_obj = self.env['freight.freight'].sudo()

        reference = self.name
        shipstation_order_id = ""
        carrier_id = ""
        if hasattr(self, "shipstation_order_id"):
            reference = self.shipstation_order_id and reference + '-' + self.shipstation_order_id or reference
            shipstation_order_id = self.shipstation_order_id
            carrier_id = self.carrier_id.id

        if reference:
            freight_id = freight_obj.search([('reference', '=', reference)], limit=1)
            if freight_id:
                self.freight_id = freight_id.id
                return True

        # pick_ids = self.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing')
        if self and self.order_line:
            vals = {
                "import_id": self.partner_id.id,
                'is_outbound': True,
                'reference': reference,
                'outbound_partner_id': self.partner_shipping_id.id,
                "shipstation_order_id": shipstation_order_id,
                "shipstation_service_id": carrier_id,
                "edi_store_id": self.edi_store_id.id,
                "fulfillment_method": self.edi_po_number and "bulk_orders" or "e-commerce",
                'sale_id': self.id,
                'delivery_price': self.shipstation_delivery_price,
                'ship_to_postal_code': self.postal_code
            }

            if self.company_id.is_oxford or self._context.get('is_oxford_process'):
                freight_obj = freight_obj.sudo()
                warehouse_id = freight_obj.env['stock.warehouse'].sudo().search([('company_id.is_logistics', '=', True)],limit=1)
                # oxf_usa = freight_obj.env['res.partner'].sudo().search([('is_oxford_usa_corporation', '=', True)], limit=1)

                pick_ids = self.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing')
                partner_id = self.partner_id.id
                if self.company_id.is_oxford:
                    partner_id = self.company_id.partner_id.id
                vals.update({
                    'warehouse_id': warehouse_id.id,
                    "partner_id": partner_id,
                    'ship_from_partner_id': warehouse_id.partner_id.id,
                    'customer_po': self.name,
                    'po_date': self.shipstation_ship_date if self.shipstation_order_id else pick_ids and pick_ids[0].scheduled_date or "",
                    'pickup_schedule_date': fields.Datetime.now() if self.shipstation_order_id else pick_ids and pick_ids[0].scheduled_date or "",
                    # 'check_out_truck_yard': pick_ids and pick_ids[-1].date_done or "" if self.shipstation_order_id else False,
                    'bol_number': pick_ids and pick_ids[0].carrier_tracking_ref or "",
                })

            if self.shipstation_warehouse_id:
                is_logistics = self.shipstation_warehouse_id.company_id.is_logistics
                vals.update({
                    'warehouse_id': is_logistics and self.shipstation_warehouse_id.id or vals.get('warehouse_id'),
                    'ship_from_partner_id': self.shipstation_warehouse_id.partner_id.id,
                })

            freight_id = freight_obj.with_context(so_number=self.name).create(vals)
            # freight_id.partner_id = partner_id
            # billing_shipping_product = self.env.ref("warefor_3pl_tus.billing_shipping_product")
            if freight_id:
                freight_id.onchange_product_cost()
                freight_id.create_so_lines(self)
                self.freight_id = freight_id.id

            if freight_id and (self.company_id.is_oxford or self._context.get('is_oxford_process')):
                # company_id = self.env['res.company'].search([('is_logistics', '=', True)], limit=1)
                # freight_id.with_company(company_id).sudo().do_3_step_process()
                freight_id._compute_weight_volume()
                self.with_context(is_oxford_process=True).freight_id.create_vas_cost_lines()

            # if self.carrier_id and 'usps' in self.carrier_id.name:
            #     vas_cost = self.env['pallet.vas.cost']
            #     load_data = {
            #         'product_id': self.carrier_id.product_id.id,
            #         'total_unit': 1,
            #         'product_uom': self.env.ref('uom.product_uom_categ_unit').id,
            #         'unit_price': self.amount_total,
            #         'transit_app_id': freight_id.id,
            #     }
            #     vas_cost.create(load_data)

            # for pick in self.picking_ids:
            #     picking_ids = freight_id.picking_ids.filtered(lambda p: p.picking_type_code == pick.picking_type_code and (('PICK' in pick.name and 'PICK' in p.name) or ('PACK' in pick.name and 'PACK' in p.name) or ('OUT' in pick.name and 'RES' in p.name) or ('RES' in pick.name and 'OUT' in p.name)))
            #     if picking_ids:
            #         picking_ids = picking_ids[0]
            #         pick.freight_picking_id = picking_ids.id
            #         picking_ids.freight_picking_id = pick.id

        return True

    def action_cancel(self):
        """
        Delete the OBL record and transfers of OBL records when cancel the sale order
        """
        for rec in self:
            try:
                rec.freight_id.picking_ids.filtered(lambda p: p.state not in ['confirmed', 'assigned', 'done']).unlink()
                rec.freight_id.unlink()
            except Exception as e:
                continue
        res = super(SaleOrder, self).action_cancel()
        return res

    def unlink(self):
        """
        Delete the OBL record and transfers of OBL records when delete the sale order
        """
        for rec in self:
            try:
                rec.freight_id.picking_ids.filtered(lambda p: p.state not in ['confirmed', 'assigned', 'done']).unlink()
                rec.freight_id.sudo().unlink()
            except Exception as e:
                continue
        res = super(SaleOrder, self).unlink()
        return res


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _compute_signature(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        user_signature = self.env.user.user_signature
        for rec in self:
            rec.signature = user_signature

    signature = fields.Binary('Signature', help='Signature received through the portal.', copy=False, attachment=True,
                              compute="_compute_signature")
    ship_via = fields.Char(string="Ship Via")
    sale_order_id = fields.Many2one("sale.order", string="Sale Order", )
    is_create_ibl = fields.Boolean(string='Create IBL Record ?')

    @api.depends('order_line.move_ids.picking_id')
    def _compute_picking(self):
        for order in self:
            pickings = order.order_line.mapped('move_ids.picking_id')
            order.picking_ids = pickings + order.picking_ids
            for pick in order.picking_ids:
                for move_line in pick.move_ids:
                    po_line = order.order_line.filtered(
                        lambda l: l.product_id.id == move_line.product_id.id and l.product_qty == move_line.product_qty)
                    if po_line and move_line.id not in po_line.move_ids.ids:
                        rec_po_line = po_line.filtered(lambda l: not l.move_ids)
                        rec_po_line = rec_po_line or po_line
                        move_line.purchase_line_id = rec_po_line[-1].id
                        rec_po_line[-1].move_ids = [(4, move_line.id)]
            order.picking_count = len(order.picking_ids)

    @api.onchange('sale_order_id')
    def on_change_sale_order(self):
        for rec in self.filtered(lambda x: x.sale_order_id.id):
            rec.sale_order_id.purchase_order_id = rec._origin.id

    freight_record = fields.Many2many("freight.freight", string="Logistic Record")
    freight_record_len = fields.Integer("Is Freight Record", compute="_freight_record_len", store=True)
    logistic_record_id = fields.Many2one("freight.freight", string="Logistic Record")

    @api.depends('order_line.invoice_lines.move_id')
    def _compute_invoice(self):
        res = super(PurchaseOrder, self)._compute_invoice()
        new_bill = self.env["account.move"].search([('pl_purchase_id', '=', self.id)])
        self.invoice_count = self.invoice_count + len(new_bill)
        return res

    # def action_view_invoice(self, invoices=False):
    #     res = super(PurchaseOrder, self).action_view_invoice(invoices)
    #
    #     return res

    def action_view_invoice(self, invoices=False):
        """This function returns an action that display existing vendor bills of
        given purchase order ids. When only one found, show the vendor bill
        immediately.
        """
        new_bill = self.env["account.move"].search([('pl_purchase_id', '=', self.id)])
        if not new_bill:
            return super(PurchaseOrder, self).action_view_invoice(invoices)
        if not invoices:
            # Invoice_ids may be filtered depending on the user. To ensure we get all
            # invoices related to the purchase order, we read them in sudo to fill the
            # cache.
            self.sudo()._read(['invoice_ids'])
            invoices = self.invoice_ids
        if invoices:
            invoices = invoices + new_bill
        else:
            invoices = new_bill
        result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        # choose the view_mode accordingly
        if len(invoices) > 1:
            result['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = invoices.id
        else:
            result = {'type': 'ir.actions.act_window_close'}

        return result

    @api.depends('freight_record')
    def _freight_record_len(self):
        """
            Length for freight_record field
        """
        for rec in self:
            rec.freight_record_len = len(rec.freight_record)

    # pallet_configuration_id = fields.Many2one(comodel_name="pallet.configuration", string="Pallet Configuration")

    # @api.onchange('order_line', 'pallet_configuration_id')
    # def _get_total_pallet_qty(self):
    #     for rec in self:
    #         pallet_configuration = rec.pallet_configuration_id
    #         for line in rec.order_line:
    #             product_uom_qty = line.product_qty
    #             total_pallet = 0
    #             packaging_qty = 0
    #             if product_uom_qty:
    #                 product = line.product_id
    #                 if pallet_configuration and product:
    #                     pallet_size = product.product_height * product.product_width * product.product_length
    #                     pd_size = pallet_configuration.width * pallet_configuration.depth * pallet_configuration.max_height
    #                     if pallet_size and pd_size:
    #                         extra_qty = pd_size % pallet_size
    #                         packaging_qty = pd_size and int(pd_size / pallet_size) or 0.0
    #                         packaging_qty += extra_qty and 1 or 0
    #                         other_qty = product_uom_qty % packaging_qty if product_uom_qty > packaging_qty else 0
    #                         total_pallet = int(product_uom_qty / packaging_qty)
    #                         if other_qty:
    #                             total_pallet += 1
    #             line.total_pallet = total_pallet

    def _create_picking(self):
        if not self._context.get('is_pallet_process'):
            return super(PurchaseOrder, self)._create_picking()
        StockPicking = self.env['stock.picking']
        for order in self:
            for freight in order.freight_record:
                if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
                    order = order.with_company(order.company_id)
                    res = order._prepare_picking()
                    res.update({'freight_record_id': freight.id})
                    picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                    freight.picking_id = picking.id
                    order = order.with_context(fr_qty_for_move=freight)
                    moves = order.order_line._create_stock_moves(picking)
                    moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                    # for fr_line in freight.freight_order_line_ids:
                    #     fr_move_line = moves.filtered(lambda m: m.product_id.id == fr_line.goods.id)
                    #     if fr_move_line:
                    #         fr_move_line.move_line_ids.qty_done == fr_line.total_quantity
                    moves.move_dest_ids = False
                    seq = 0
                    for move in sorted(moves, key=lambda move: move.date):
                        seq += 5
                        move.sequence = seq
                    moves._action_assign()
                    picking.message_post_with_view('mail.message_origin_link',
                        values={'self': picking, 'origin': order},
                        subtype_id=self.env.ref('mail.mt_note').id)
        return True

    def button_confirm(self):
        """
        Confirm the purchase order and create the Pallets as per the configuration in incoming shipment.
        :return: res and Purchase object
        """
        configuration = self.env['purchase.logistic.configuration'].sudo().search(
            [('company_id', '=', self.company_id.id)], limit=1)
        is_oxford = self.company_id.is_oxford
        is_create_ibl = self.is_create_ibl
        if is_oxford or (is_create_ibl and self.company_id.is_logistics):
            self.with_context(configuration=configuration, is_oxford_process=is_oxford).action_create_freight_record()
        if self.freight_record:
            self = self.with_context(is_pallet_process=True)
        res = super(PurchaseOrder, self).button_confirm()
        # self.create_receipt_pallets()
        return res

    def create_receipt_pallets(self):
        """
        Create the Pallet as per the configuration and incoming shipment products with qty
        :return: True
        """
        return True
        _logger.info("********** Method: create_receipt_pallets: {} **************".format(self.ids))
        product_development = self.env['product.development']
        for record in self:
            partner_id = record.partner_id
            if len(record.name.split("O")) > 1:
                po_name = record.name.split("O")[-1]
            else:
                po_name = record.name.split("P")[-1]
            pickings_len = 0
            for freight in record.freight_record:
                freight = freight.with_context(transit_app=freight)
                picking = freight.picking_id
                if picking:
                    _logger.info("********** Processing total pickings: {} **************".format(picking.ids))
                    pickings_len += 1
                    _logger.info("********** Processing picking: {} **************".format(picking.ids))
                    pallet_item = 0
                    pallet_number = 0
                    for move_line in picking.move_ids:
                        other_qty_done = False
                        product_uom_qty = 0
                        packaging_qty = 0
                        _logger.info("********** Processing move_line: {} **************".format(move_line.ids))
                        pallet_item += 1
                        pallet_cost_id = freight
                        pallet_cost_obj = self.env["pallet.cost.config"]
                        product_id = move_line.product_id
                        _logger.info("********** Transit App: {} **************".format(pallet_cost_id))
                        if pallet_cost_id and pallet_cost_id.freight_order_line_ids:
                            picking = picking.with_context(is_split=True)
                            partner_id = pallet_cost_id.import_id and pallet_cost_id.import_id or partner_id
                            freight_order_line_ids = pallet_cost_id.freight_order_line_ids.filtered(
                                lambda f: f.goods == move_line.product_id)
                            if not freight_order_line_ids:
                                _logger.warning("********** Product line {} is not found in Freight record: {} ".format(
                                    move_line.product_id, pallet_cost_id.freight_order_line_ids))
                                pallet_item -= 1
                                continue
                            packaging_id = product_id.packaging_id.id
                            package_id = packaging_id and pallet_cost_id.product_package_ids.filtered(
                                lambda l: l.package_id.id == packaging_id and l.product_qty in freight_order_line_ids.mapped('total_quantity'))
                            if package_id:
                                package_id = package_id[0]
                                packaging_qty = package_id.package_per_pallet
                                product_uom_qty = package_id.package_qty
                                picking = picking.with_context(is_package=package_id)
                            else:
                                packaging_qty = freight_order_line_ids[0].total_pallet
                                packaging_qty = packaging_qty or pallet_cost_id.packaging_qty
                                product_uom_qty = move_line.product_uom_qty
                                picking = picking.with_context(is_package=False)

                        if packaging_qty and product_uom_qty:
                            if product_uom_qty <= packaging_qty:
                                pallet_number += 1
                                name = "{}/{}/0{}-{}".format(partner_id.vendor_identifier or "", po_name,
                                                             pickings_len, pallet_number)
                                picking = picking.with_context(is_split=False)
                                picking.create_shipment_pallet(name, move_line.product_id, product_uom_qty,
                                                               pallet_cost_id)
                            else:
                                other_qty = product_uom_qty % packaging_qty if product_uom_qty > packaging_qty else 0
                                total_pallet = int(product_uom_qty / packaging_qty)
                                if other_qty:
                                    total_pallet += 1
                                    other_qty_done = True
                                picking = picking.with_context(is_split=total_pallet)
                                for pallet_seq in range(0, total_pallet):
                                    pallet_number += 1
                                    name = "{}/{}/0{}-{}".format(partner_id.vendor_identifier or "", po_name,
                                                                 pickings_len, pallet_number)
                                    _logger.info(
                                        "********** Creating Pallet: {} **************".format(name))
                                    if other_qty and other_qty_done:
                                        picking.create_shipment_pallet(name, move_line.product_id, other_qty,
                                                                       pallet_cost_id)
                                        other_qty_done = False
                                    else:
                                        picking.create_shipment_pallet(name, move_line.product_id, packaging_qty,
                                                                       pallet_cost_id)
                if freight:
                    freight.total_pallet = len(freight.pallet_ids)
        return True

    @api.model
    def create(self, vals):
        """ Set PO sequence as per default company. """
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        self_comp = self.with_company(company_id)
        rec = super(PurchaseOrder, self_comp).create(vals)
        if rec.company_id.company_code:
            rec.name = rec.company_id.company_code + '-' + vals['name'] if vals['name'] else '/'
        return rec

    def action_create_freight_record(self):
        """
        Creating the freight record from the Purchase order with some of the Purchase order details
        Author: Prakash Makwana
        Date: 7th Sep, 2021.
        :return: True
        """
        freight_obj = self.env['freight.freight'].sudo()
        freight_record = self.freight_record
        if freight_record:
            freight_record.unlink()
        warehouse_id = self._context.get('configuration') and self._context.get('configuration').warehouse_id.id or False
        if self and self.order_line:
            customer_po = self.name
            if len(self.name.split('-')) > 1:
                customer_po = self.name.split('-')[-1]
            vals = {
                "import_id": self.partner_id.id,
                "warehouse_id": warehouse_id,
                "purchase_orders_ids": self.id,
                "partner_id": self.partner_id.freight_customer_id.id,
                "customer_po": customer_po,
            }
            if self._context.get('is_oxford_process') and not vals.get('warehouse_id'):
                freight_obj = freight_obj.sudo()
                warehouse_id = freight_obj.env['stock.warehouse'].sudo().search([('company_id.is_logistics', '=', True)],
                                                                                limit=1)
                vals.update({'warehouse_id': warehouse_id.id})

            if not vals.get('warehouse_id') \
                    and self.picking_type_id.company_id.is_logistics and self.picking_type_id.warehouse_id.id:
                vals.update({'warehouse_id': self.picking_type_id.warehouse_id.id})

            freight_id = freight_obj.with_context(po_number=self.name).create(vals)
            if freight_id:
                freight_id.onchange_product_cost()
                freight_id.create_po_lines()
                self.write({'freight_record': [(4, freight_id.id)]})
        return True

    def open_wizard_for_invoice_from_purchase(self):
        action = self.env["ir.actions.actions"]._for_xml_id("warefor_3pl_tus.act_custom_invoice_wizard_1")
        return action

    def _get_picking_type(self, company_id):
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not picking_type:
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        picking_type_ids = picking_type.filtered(lambda x:x.name == 'Consumables')
        if picking_type_ids:
            picking_type = picking_type_ids
        return picking_type[:1]

    def _get_destination_location(self):
        res = super()._get_destination_location()
        if self.company_id.use_virtual_location and self.partner_id.virtual_location_id:
            return self.partner_id.virtual_location_id.id
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        if not self._context.get('is_pallet_process'):
            return super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res

        qty = 0.0
        price_unit = self._get_stock_move_price_unit()

        move_dests = self.move_dest_ids
        if not move_dests:
            move_dests = self.move_ids.move_dest_ids.filtered(lambda m: m.state != 'cancel' and not m.location_dest_id.usage == 'supplier')

        if not move_dests:
            qty_to_attach = 0
            qty_to_push = self.product_qty - qty
        else:
            move_dests_initial_demand = self.product_id.uom_id._compute_quantity(
                sum(move_dests.filtered(lambda m: m.state != 'cancel' and not m.location_dest_id.usage == 'supplier').mapped('product_qty')),
                self.product_uom, rounding_method='HALF-UP')
            qty_to_attach = move_dests_initial_demand - qty
            qty_to_push = self.product_qty - move_dests_initial_demand

        freight = self._context.get('fr_qty_for_move')
        if freight:
            fr_line = freight.freight_order_line_ids.filtered(lambda l: l.goods.id == self.product_id.id)
            if fr_line:
                qty_to_push = sum(fr_line.mapped('total_quantity'))

        if float_compare(qty_to_attach, 0.0, precision_rounding=self.product_uom.rounding) > 0:
            product_uom_qty, product_uom = self.product_uom._adjust_uom_quantities(qty_to_attach, self.product_id.uom_id)
            res.append(self._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom))
        if float_compare(qty_to_push, 0.0, precision_rounding=self.product_uom.rounding) > 0:
            product_uom_qty, product_uom = self.product_uom._adjust_uom_quantities(qty_to_push, self.product_id.uom_id)
            extra_move_vals = self._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
            extra_move_vals['move_dest_ids'] = False  # don't attach
            res.append(extra_move_vals)
        return res

#     total_pallet = fields.Float(string="Required Pallets")


class PurchaseLogisticConfiguration(models.Model):
    _name = 'purchase.logistic.configuration'
    _description = 'Configuration for creating logistic record from purchase order'

    name = fields.Char("Name")
    company_id = fields.Many2one("res.company", string="Company")
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse")
