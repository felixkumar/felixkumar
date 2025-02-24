# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger('Transferring OPS Line')


class OSDFreightTransferLine(models.Model):
    _name = 'osd.freight.transfer.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'OSD Freight Transfer Line'

    pallet_type = fields.Selection(
        selection=[('Mixed', 'Mixed'), ('Partial', 'Partial'), ('Full', 'Full')],
        string="Pallet Type"
    )
    sub_pallet = fields.Char(string="Sub Pallet")
    sscc_18_char = fields.Char(string="SSCC-18 Barcode Number")
    freight_order_line_id = fields.Many2one('freight.order.line', string="Freight Order Line")
    freeze = fields.Boolean('Read Only')
    sscc_barcode_id = fields.Many2one('sscc18.barcode', string="SSCC-18 Barcode Number")

    # @api.model
    # def write(self, vals):
    #     print("osd frst", vals)
        # if 'pallet_type' in vals.get('pallet_type') or 'sub_pallet' in vals.get('sub_pallet'):
        #     print(self.sscc_18_char)

    # def generate_sscc_18(self):
    #     """
    #     Generate Pallet SSCC barcode
    #     :return:
    #     """
    #     for all in self:
    #         print(all,"*************")
    #         for rec in all.osd_transfer_ids:
    #             print(rec,"((((((((((((()))))))))))))))))))")
    #             if not rec.sscc_18_char:
    #                 print("<<<<<<<>>>>>>>")
    #                 """
    #                 Document Reference: for generating pallet SSCC barcodes
    #                 https://www.gs1us.org/DesktopModules/Bring2mind/DMX/Download.aspx?Command=Core_Download&EntryId=177&language=en-US&PortalId=0&TabId=134
    #                 """
    #                 generated_sscc_code = []
    #                 app_identifier = "(00)"
    #                 extension_digit = '0'
    #                 def calculate_check_digit(number):
    #                     total = sum(int(d) * (3 if (i % 2 == 0) else 1) for i, d in enumerate(reversed(number)))
    #                     return (10 - (total % 10)) % 10
    #
    #                 def extract_serial_no(barcodes, gs1code):
    #                     gs1_length = len(gs1code) + 5
    #                     start = len(barcodes) - gs1_length
    #                     serial_end = 21
    #                     str_serial_no = str(barcodes[gs1_length:serial_end])
    #                     return str_serial_no
    #
    #                 def generate_new_barcode(barcodes, gs1):
    #                     str_serial_number = extract_serial_no(barcodes, gs1)
    #                     last_serial_number = int(str_serial_number)
    #                     width = 16 - len(gs1)
    #                     new_serial_number = "{:0{width}d}".format(last_serial_number + 1, width=width)
    #                     sscc_not_check_digit = f"{extension_digit}{gs1_code}{new_serial_number}"
    #                     check_digits = calculate_check_digit(sscc_not_check_digit)
    #                     generate_sscc_code = "{app_identifier}{extension_digit}{gs1_code}{serial_number}{check_digit}".format(
    #                         app_identifier=app_identifier,
    #                         extension_digit=extension_digit,
    #                         gs1_code=gs1_code,
    #                         serial_number=new_serial_number,
    #                         check_digit=check_digits
    #                     )
    #                     return generate_sscc_code
    #                 if rec.pallet_type == 'Mixed':
    #                     existing_records = self.env['osd.freight.transfer.line'].search([('freight_id', '=', rec.freight_id.id), ('id', '!=', rec.id)])
    #                     print(existing_records)
    #                     count = 1
    #                     for iterate in existing_records:
    #                         count +=1
    #                         print(iterate, count)
    #                         print(iterate.pallet_type, rec.pallet_type, iterate.sub_pallet, rec.sub_pallet, "ertyu")
    #                         if iterate.pallet_type == rec.pallet_type and iterate.sub_pallet == rec.sub_pallet:
    #                             rec.sscc_18_char = iterate.sscc_18_char
    #                             rec.freight_order_line_id.sudo().write({
    #                                 'sscc_18_char': rec.sscc_18_char,
    #                                 'sub_pallet': rec.sub_pallet,
    #                                 'pallet_type': rec.pallet_type,
    #                             })
    #                             return
    #                         else:
    #                             continue
    #                 company_name = self.partner_id.company_name
    #                 company_id = self.env['res.company'].sudo().search([('name', '=', company_name)], limit=1)
    #                 gs1_code = company_id.gs1_company_prefix or "0000000"
    #                 required_serial_length = 16 - len(gs1_code)
    #                 if not (7 <= len(gs1_code) <= 10):
    #                     raise ValidationError("GS1 Company Prefix must be between 7 and 10 digits")
    #                 last_record = rec.env['sscc18.barcode'].search(
    #                     [('company_id', '=', company_id.id),
    #                      ('gs1_code', '=', gs1_code)], order="create_date desc", limit=1)
    #                 if not last_record:
    #                     serial_number = "0" * required_serial_length
    #                     serial_number = serial_number[:-1] + "1"
    #                     sscc_without_check_digit = f"{extension_digit}{gs1_code}{serial_number}"
    #                     check_digit = calculate_check_digit(sscc_without_check_digit)
    #                     generated_sscc_code = "{app_identifier}{extension_digit}{gs1_code}{serial_number}{check_digit}".format(
    #                         app_identifier=app_identifier,
    #                         extension_digit=extension_digit,
    #                         gs1_code=gs1_code,
    #                         serial_number=serial_number,
    #                         check_digit=check_digit
    #                     )
    #                     rec.env['sscc18.barcode'].sudo().create({
    #                         'sscc18_barcode': generated_sscc_code,
    #                         'company_id': company_id.id,
    #                         'gs1_code': gs1_code,
    #                         'serial_no': serial_number
    #                     })
    #                     rec.sscc_18_char = generated_sscc_code
    #                 else:
    #                     rec_serial = last_record.serial_no
    #                     len_rec = len(rec_serial)
    #                     expected_serial_no = '9' * len_rec
    #                     if rec_serial == expected_serial_no:
    #                         expired_record = rec.env['sscc18.barcode'].search([('expiry_date', '<', date.today()),
    #                                                                            ('company_id', '=',
    #                                                                             company_id.id),
    #                                                                            ('gs1_code', '=', gs1_code)]
    #                                                                           , limit=1)
    #                         if expired_record:
    #                             expired_barcode = expired_record.sscc18_barcode
    #                             rec.env['sscc18.barcode'].sudo().create({
    #                                 'sscc18_barcode': expired_barcode,
    #                                 'company_id': company_id.id,
    #                                 'gs1_code': gs1_code,
    #                                 'serial_no': expired_record.serial_no
    #                             })
    #                             rec.sscc_18_char = expired_barcode
    #                             expired_record.unlink()
    #                     else:
    #                         last_barcode = last_record.sscc18_barcode
    #                         if last_record and last_barcode:
    #                             generated_sscc_code = generate_new_barcode(last_barcode, gs1_code)
    #                             already_exist = rec.env['sscc18.barcode'].sudo().search(
    #                                 [('sscc18_barcode', '=', generated_sscc_code), ('company_id', '=', company_id.id)])
    #                             if already_exist:
    #                                 highest_rec = rec.env['sscc18.barcode'].sudo().search([
    #                                     ('company_id', '=', company_id.id)
    #                                 ], order="sscc18_barcode desc", limit=1)
    #                                 barcode = highest_rec.sscc18_barcode
    #                                 generated_sscc_code = generate_new_barcode(barcode, gs1_code)
    #                                 str_serial_number = extract_serial_no(generated_sscc_code, gs1_code)
    #                                 rec.env['sscc18.barcode'].sudo().create({
    #                                     'sscc18_barcode': generated_sscc_code,
    #                                     'company_id': company_id.id,
    #                                     'gs1_code': gs1_code,
    #                                     'serial_no': str_serial_number
    #                                 })
    #                                 rec.sscc_18_char = generated_sscc_code
    #                             else:
    #                                 last_serial_number = extract_serial_no(generated_sscc_code, gs1_code)
    #                                 rec.env['sscc18.barcode'].sudo().create({
    #                                     'sscc18_barcode': generated_sscc_code,
    #                                     'company_id': company_id.id,
    #                                     'gs1_code': gs1_code,
    #                                     'serial_no': last_serial_number
    #                                 })
    #                                 rec.sscc_18_char = generated_sscc_code
    #                     print(rec.sub_pallet, rec.pallet_type)
    #                     rec.freight_order_line_id.sudo().write({
    #                         'sub_pallet': rec.sub_pallet,
    #                         'pallet_type': rec.pallet_type,
    #                         'sscc_18_char': rec.sscc_18_char
    #                     })

    # def generate_sscc_18(self):
    #     """
    #     Generate Pallet SSCC barcode
    #     :return:
    #     """
    #     for rec in self:
    #         """
    #         Document Reference: for generating pallet SSCC barcodes
    #         https://www.gs1us.org/DesktopModules/Bring2mind/DMX/Download.aspx?Command=Core_Download&EntryId=177&language=en-US&PortalId=0&TabId=134
    #         """
    #         generated_sscc_code = []
    #         app_identifier = "(00)"
    #         extension_digit = '0'
    #
    #         def calculate_check_digit(number):
    #             total = sum(int(d) * (3 if (i % 2 == 0) else 1) for i, d in enumerate(reversed(number)))
    #             return (10 - (total % 10)) % 10
    #
    #         def extract_serial_no(barcodes, gs1code):
    #             gs1_length = len(gs1code) + 5
    #             start = len(barcodes) - gs1_length
    #             serial_end = 21
    #             str_serial_no = str(barcodes[gs1_length:serial_end])
    #             return str_serial_no
    #
    #         def generate_new_barcode(barcodes, gs1):
    #             str_serial_number = extract_serial_no(barcodes, gs1)
    #             last_serial_number = int(str_serial_number)
    #             width = 16 - len(gs1)
    #             new_serial_number = "{:0{width}d}".format(last_serial_number + 1, width=width)
    #             sscc_not_check_digit = f"{extension_digit}{gs1_code}{new_serial_number}"
    #             check_digits = calculate_check_digit(sscc_not_check_digit)
    #             generate_sscc_code = "{app_identifier}{extension_digit}{gs1_code}{serial_number}{check_digit}".format(
    #                 app_identifier=app_identifier,
    #                 extension_digit=extension_digit,
    #                 gs1_code=gs1_code,
    #                 serial_number=new_serial_number,
    #                 check_digit=check_digits
    #             )
    #             return generate_sscc_code
    #
    #         if rec.pallet_type == 'Mixed':
    #             record = self.env['osd.freight.transfer.line'].search([('freight_id', '=', rec.freight_id.id)])
    #             for i in record:
    #                 if i.pallet_type and i.sub_pallet and i.sscc_18_char:
    #                     if i.pallet_type == rec.pallet_type and i.sub_pallet == rec.sub_pallet:
    #                         rec.sscc_18_char = i.sscc_18_char
    #                         if rec.freight_order_line_id:
    #                             rec.freight_order_line_id.sscc_18_char = i.sscc_18_char
    #                             rec.freight_order_line_id.pallet_type = i.pallet_type
    #                             rec.freight_order_line_id.sub_pallet = i.sub_pallet
    #                         return
    #         company_name = self.freight_id.partner_id.company_name
    #         company_id = self.env['res.company'].sudo().search([('name', '=', company_name)], limit=1)
    #         gs1_code = company_id.gs1_company_prefix or "0000000"
    #         required_serial_length = 16 - len(gs1_code)
    #         if not (7 <= len(gs1_code) <= 10):
    #             raise ValidationError("GS1 Company Prefix must be between 7 and 10 digits")
    #         last_record = rec.env['sscc18.barcode'].search(
    #             [('company_id', '=', company_id.id),
    #              ('gs1_code', '=', gs1_code)], order="create_date desc", limit=1)
    #         if not last_record:
    #             serial_number = "0" * required_serial_length
    #             serial_number = serial_number[:-1] + "1"
    #             sscc_without_check_digit = f"{extension_digit}{gs1_code}{serial_number}"
    #             check_digit = calculate_check_digit(sscc_without_check_digit)
    #             generated_sscc_code = "{app_identifier}{extension_digit}{gs1_code}{serial_number}{check_digit}".format(
    #                 app_identifier=app_identifier,
    #                 extension_digit=extension_digit,
    #                 gs1_code=gs1_code,
    #                 serial_number=serial_number,
    #                 check_digit=check_digit
    #             )
    #             rec.env['sscc18.barcode'].sudo().create({
    #                 'sscc18_barcode': generated_sscc_code,
    #                 'company_id': company_id.id,
    #                 'gs1_code': gs1_code,
    #                 'serial_no': serial_number
    #             })
    #             rec.sscc_18_char = generated_sscc_code
    #         else:
    #             rec_serial = last_record.serial_no
    #             len_rec = len(rec_serial)
    #             expected_serial_no = '9' * len_rec
    #             if rec_serial == expected_serial_no:
    #                 expired_record = rec.env['sscc18.barcode'].search([('expiry_date', '<', date.today()),
    #                                                                    ('company_id', '=',
    #                                                                     company_id.id),
    #                                                                    ('gs1_code', '=', gs1_code)]
    #                                                                   , limit=1)
    #                 if expired_record:
    #                     expired_barcode = expired_record.sscc18_barcode
    #                     rec.env['sscc18.barcode'].sudo().create({
    #                         'sscc18_barcode': expired_barcode,
    #                         'company_id': company_id.id,
    #                         'gs1_code': gs1_code,
    #                         'serial_no': expired_record.serial_no
    #                     })
    #                     rec.sscc_18_char = expired_barcode
    #                     expired_record.unlink()
    #             else:
    #                 last_barcode = last_record.sscc18_barcode
    #                 if last_record and last_barcode:
    #                     generated_sscc_code = generate_new_barcode(last_barcode, gs1_code)
    #                     already_exist = rec.env['sscc18.barcode'].sudo().search(
    #                         [('sscc18_barcode', '=', generated_sscc_code), ('company_id', '=', company_id.id)])
    #                     if already_exist:
    #                         highest_rec = rec.env['sscc18.barcode'].sudo().search([
    #                             ('company_id', '=', company_id.id)
    #                         ], order="sscc18_barcode desc", limit=1)
    #                         barcode = highest_rec.sscc18_barcode
    #                         generated_sscc_code = generate_new_barcode(barcode, gs1_code)
    #                         str_serial_number = extract_serial_no(generated_sscc_code, gs1_code)
    #                         rec.env['sscc18.barcode'].sudo().create({
    #                             'sscc18_barcode': generated_sscc_code,
    #                             'company_id': company_id.id,
    #                             'gs1_code': gs1_code,
    #                             'serial_no': str_serial_number
    #                         })
    #                         rec.sscc_18_char = generated_sscc_code
    #                     else:
    #                         last_serial_number = extract_serial_no(generated_sscc_code, gs1_code)
    #                         rec.env['sscc18.barcode'].sudo().create({
    #                             'sscc18_barcode': generated_sscc_code,
    #                             'company_id': company_id.id,
    #                             'gs1_code': gs1_code,
    #                             'serial_no': last_serial_number
    #                         })
    #                         rec.sscc_18_char = generated_sscc_code
    #                         if rec.freight_order_line_id:
    #                             rec.freight_order_line_id.sscc_18_char = generated_sscc_code
    #                             rec.freight_order_line_id.pallet_type = i.pallet_type
    #                             rec.freight_order_line_id.sub_pallet = i.sub_pallet

    def _logistic_record_line_sku(self):
        domain= []
        if self.env.context.get('active_id', False):
            freight_id = self.env['freight.freight'].sudo().browse(int(self.env.context.get('active_id', False)))
            domain.append(('id','in',freight_id.freight_order_line_ids.mapped('goods').ids))
        if self.env.context.get('params',False) and self.env.context.get('params',False).get('id',False):
            freight_id = self.env['freight.freight'].sudo().browse(self.env.context.get('params', False).get('id',False))
            domain.append(('id', 'in', freight_id.freight_order_line_ids.mapped('goods').ids))
        return domain

    @api.onchange('sku_id')
    def onchange_sku_id(self):
        for rec in self:
            if rec.sku_id:
                f_lines = rec.freight_id.freight_order_line_ids.filtered(lambda l: l.goods.id == rec.sku_id.id)
                if f_lines:
                    rec.po_number = f_lines[0].id

    @api.onchange('pallet_type')
    def change_pallet_type(self):
        self.freight_order_line_id.pallet_type = self.pallet_type

    @api.onchange('sub_pallet')
    def onchange_subpallet_type(self):
        self.freight_order_line_id.sub_pallet = self.sub_pallet


    def _logistic_record_warehouse_location(self):
        domain = []
        if self.env.context.get('active_id', False):
            freight_id = self.env['freight.freight'].sudo().browse(int(self.env.context.get('active_id', False)))
            locations = self.env['stock.location'].search([('warehouse_id', '=', freight_id.warehouse_id.id)])
            # if self.location_id:
            #     locations.remove(self.location_id.id)
            location_ids = locations-self.destination_location_id
            domain.append(('id', 'in', location_ids.ids))
        if self.env.context.get('params',False) and self.env.context.get('params',False).get('id',False):
            freight_id = self.env['freight.freight'].sudo().browse(self.env.context.get('params', False).get('id',False))
            locations = self.env['stock.location'].search([('warehouse_id', '=', freight_id.warehouse_id.id)])
            # if self.location_id:
            #     locations.remove(self.location_id.id)
            location_ids = locations - self.destination_location_id
            domain.append(('id', 'in', location_ids.ids))
        return domain

    def _logistic_record_warehouse_dest_location(self):
        domain = []
        if self.env.context.get('active_id', False):
            freight_id = self.env['freight.freight'].sudo().browse(int(self.env.context.get('active_id', False)))
            locations = self.env['stock.location'].search([('warehouse_id', '=', freight_id.warehouse_id.id)])
            # if self.location_id:
            #     locations.remove(self.location_id.id)
            location_ids = locations-self.location_id
            domain.append(('id', 'in', location_ids.ids))
        if self.env.context.get('params',False) and self.env.context.get('params',False).get('id',False):
            freight_id = self.env['freight.freight'].sudo().browse(self.env.context.get('params', False).get('id',False))
            locations = self.env['stock.location'].search([('warehouse_id', '=', freight_id.warehouse_id.id)])
            # if self.location_id:
            #     locations.remove(self.location_id.id)
            location_ids = locations - self.location_id
            domain.append(('id', 'in', location_ids.ids))
        return domain

    freight_id = fields.Many2one(comodel_name="freight.freight", string="PL Record")
    sku_id = fields.Many2one(comodel_name="product.product", string="SKU", domain=_logistic_record_line_sku)
    lot_id = fields.Many2one('stock.lot', 'Lot #', domain="[('product_id', '=', sku_id)]")
    description = fields.Char(related="sku_id.name", string="Description")
    quantity = fields.Float(string="Quantity", digits=(999, 0), tracking=True)
    location_id = fields.Many2one("stock.location", string="Location")
    destination_location_id = fields.Many2one(comodel_name="stock.location", string="Location")
    is_outbound_pl = fields.Boolean(related="freight_id.is_outbound", string="Is Outbound")
    on_hand_qty = fields.Float(string="On Hand Quantity", readonly=True, compute="_compute_on_hand_qty")
    warehouse_id = fields.Many2one(related="freight_id.warehouse_id", string="Warehouse", store=True)
    is_osd_inventory_transfered = fields.Boolean(string="Transfer Created")
    pick_picking_id = fields.Many2one("stock.picking", string="Warehouse")
    pack_picking_id = fields.Many2one("stock.picking", string="Pack Transfer")
    ship_picking_id = fields.Many2one("stock.picking", string="Ship Transfer")
    pack_picking_state = fields.Selection(related="pack_picking_id.state", string="Transfer State")
    ship_picking_state = fields.Selection(related="ship_picking_id.state", string="Transfer State")
    po_number = fields.Many2one("freight.order.line", string="PO Number")

    @api.depends("quantity", 'location_id')
    def _compute_on_hand_qty(self):
        for rec in self:
            rec.on_hand_qty = 0
            if rec.sku_id:
                if not rec.is_outbound_pl and rec.destination_location_id:
                    rec.on_hand_qty = self.env['stock.quant']._get_available_quantity(rec.sku_id, rec.destination_location_id)
                elif rec.is_outbound_pl and rec.location_id:
                    rec.on_hand_qty = self.env['stock.quant']._get_available_quantity(rec.sku_id, rec.location_id)

    @api.onchange('destination_location_id', 'quantity')
    def onchange_destination_location_id(self):
        for rec in self:
            if not rec.is_outbound_pl:
                if rec.sku_id and rec.destination_location_id:
                    rec.on_hand_qty = self.env['stock.quant']._get_available_quantity(rec.sku_id, rec.destination_location_id)
                freight_id = rec.freight_id
                destination_location_id = rec.destination_location_id
                if destination_location_id:
                    picking_type = rec.env['stock.picking.type'].search(
                        [
                            ('is_inventory_adjustment', '=', True),
                            ('warehouse_id', '=', freight_id.warehouse_id.id),
                            ('warehouse_id.company_id', '=', destination_location_id.company_id.id)
                        ],
                        limit=1)
                    if picking_type:
                        rec.location_id = picking_type.default_location_src_id.id
            elif rec.is_outbound_pl and rec.sku_id:
                rec.destination_location_id = self.env['stock.location'].search(
                    [('warehouse_id', '=', rec.warehouse_id.id), ('is_destination_location', '=', True)])
                if rec.sku_id and rec.destination_location_id:
                    stock_quant = self.env['stock.quant']
                    company_ids = self.env["res.company"].search([('is_logistics', '=', True)])
                    # lot_ids = self.env['stock.lot'].search([('product_id', '=', rec.sku_id.id)], order='id')
                    # lot_ids = lot_ids.filtered(lambda x: x.product_qty) and lot_ids.filtered(lambda x: x.product_qty)[0]
                    quant_ids = stock_quant.search([('product_id', '=', rec.sku_id.id),
                                                    ('location_id.usage', '=', 'internal'),
                                                    ('lot_id', '=', rec.lot_id.id),
                                                    ('location_id.warehouse_id', '=', rec.freight_id.warehouse_id.id),
                                                    ('company_id', 'in', company_ids.ids),
                                                    ('location_id.is_omit_on_source_location', '=', False)], order='create_date', limit=1)
                    quant_ids = quant_ids.filtered(lambda q: q.available_quantity > rec.quantity)
                    if quant_ids and rec.sku_id.tracking != 'none':
                        if not rec.location_id:
                            rec.location_id = quant_ids.mapped('location_id') and quant_ids.mapped('location_id')[0].id
                            lot_id = quant_ids.mapped('lot_id') and quant_ids.mapped('lot_id')[0].id
                            if not rec.lot_id:
                                rec.lot_id = lot_id
                        if rec.location_id:
                            rec.on_hand_qty = stock_quant._get_available_quantity(rec.sku_id, rec.location_id)
                            if not rec.lot_id:
                                rec.lot_id = quant_ids.mapped('lot_id') and quant_ids.mapped('lot_id')[0].id
                    elif quant_ids:
                        if not rec.location_id:
                            rec.location_id = quant_ids.mapped('location_id') and quant_ids.mapped('location_id')[0].id
                        if rec.location_id:
                            rec.on_hand_qty = stock_quant._get_available_quantity(rec.sku_id, rec.location_id)
                    # rec.action_reservation_create()


    def osd_transfer_inventory(self):
        if self.is_osd_inventory_transfered:
            return True
        freight_id = self.freight_id
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
        line_id = self.freight_id.freight_order_line_ids.filtered(lambda x: x.goods.id == self.sku_id.id)
        # if self.quantity <= line_id.total_quantity:
        move_id = self.env['stock.move'].create(line_vals)
        # else:
        #     raise ValidationError('Input quantity less than {}'.format(line_id.total_quantity))
        # move_id = self.env['stock.move'].create(line_vals)
        picking_id.write({'partner_id': False})
        move_ids_without_package = picking_id.move_ids_without_package
        for move_id in move_ids_without_package:
            move_id.picking_type_id = picking_id.picking_type_id.id
        picking_id.action_assign()
        picking_id.action_confirm()
        # lot_id = picking_id.move_line_ids.lot_id
        # if len(lot_id) == 1:
        #     picking_id.move_line_ids.write({'lot_id': lot_id.id})
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

    def osd_transfer_inventory_outbound(self):
        """
            Method for creating transfer's from OPS outbound
        """
        if self.pick_picking_id:
            return True
        freight_id = self.freight_id
        warehouse_id = self.freight_id.warehouse_id
        location_id = self.location_id
        destination_location_id = self.destination_location_id
        if not location_id or not destination_location_id:
            raise ValidationError("Please select the location for transfer the inventory!")
        if not self.sku_id:
            raise ValidationError("Product not found in record!")
        if self.quantity > self.on_hand_qty:
            raise ValidationError(_("{} is not available in this quantity in Location {}".format(self.sku_id.name,self.location_id.name)))

        if warehouse_id.delivery_steps == 'pick_pack_ship':
            product_id = self.sku_id

            # Pick
            pick_picking_id = self.env['stock.picking'].create({
                'location_id': location_id.id,
                'location_dest_id': destination_location_id.id,
                'move_type': 'direct',
                'immediate_transfer': True,
                'picking_type_id': warehouse_id.pick_type_id.id,
                'is_locked': True,
                'company_id': location_id.company_id.id,
                'freight_record_id': freight_id.id,
                'partner_id': freight_id.outbound_partner_id.id
            })
            line_vals = {
                'name': product_id.name,
                'location_id': pick_picking_id.location_id.id,
                'location_dest_id': pick_picking_id.location_dest_id.id,
                'picking_id': pick_picking_id.id,
                'product_id': product_id.id,
                'product_uom': product_id.uom_id.id,
                'quantity_done': self.quantity,
                'product_uom_qty': self.quantity,
                'company_id': pick_picking_id.company_id.id,
                'lot_ids': [(6, 0, self.lot_id.ids)]
            }
            line_id = self.freight_id.freight_order_line_ids.filtered(lambda x: x.goods.id == self.sku_id.id)
            # if self.quantity <= line_id.total_quantity:
            move_id = self.env['stock.move'].create(line_vals)
            _logger.info("1] Created Move: {}, move ids: {}, move qty: {}".
                         format(move_id.id, pick_picking_id.move_line_ids.ids,
                                pick_picking_id.move_line_ids.mapped('qty_done')))
            # else:
            #     raise ValidationError('Input quantity less than {}'.format(line_id.total_quantity))
            # move_id = self.env['stock.move'].create(line_vals)
            move_ids_without_package = pick_picking_id.move_ids_without_package
            for move_id in move_ids_without_package:
                move_id.picking_type_id = pick_picking_id.picking_type_id.id
            _logger.info("2] Created Move: {}, move ids: {}, move qty: {}".
                         format(move_id.id, pick_picking_id.move_line_ids.ids,
                                pick_picking_id.move_line_ids.mapped('qty_done')))
            pick_picking_id.action_assign()
            _logger.info("3] Created Move: {}, move ids: {}, move qty: {}".
                         format(move_id.id, pick_picking_id.move_line_ids.ids,
                                pick_picking_id.move_line_ids.mapped('qty_done')))
            move_line_ids = pick_picking_id.move_line_ids[1:]
            move_line_ids.unlink()
            pick_picking_id.action_confirm()
            _logger.info("4] Created Move: {}, move ids: {}, move qty: {}".
                         format(move_id.id, pick_picking_id.move_line_ids.ids,
                                pick_picking_id.move_line_ids.mapped('qty_done')))
            if self.lot_id:
                pick_picking_id.move_line_ids.write({'lot_id': self.lot_id.id})
            pick_picking_id.button_validate()
            _logger.info("5] Created Move: {}, move ids: {}, move qty: {}".
                         format(move_id.id, pick_picking_id.move_line_ids.ids,
                                pick_picking_id.move_line_ids.mapped('qty_done')))
            freight_id.write({'picking_ids': [(4, pick_picking_id.id)]})
            self.pick_picking_id = pick_picking_id.id

            # Pack
            pack_picking_id = self.env['stock.picking'].create({
                'location_id': destination_location_id.id,
                'location_dest_id': warehouse_id.pack_type_id.default_location_dest_id.id,
                'move_type': 'direct',
                'immediate_transfer': True,
                'picking_type_id': warehouse_id.pack_type_id.id,
                'is_locked': True,
                'company_id': location_id.company_id.id,
                'freight_record_id': freight_id.id,
                'partner_id': freight_id.outbound_partner_id.id
            })
            line_vals = {
                'name': product_id.name,
                'location_id': pack_picking_id.location_id.id,
                'location_dest_id': pack_picking_id.location_dest_id.id,
                'picking_id': pack_picking_id.id,
                'product_id': product_id.id,
                'product_uom': product_id.uom_id.id,
                'quantity_done': self.quantity,
                'product_uom_qty': self.quantity,
                'company_id': pack_picking_id.company_id.id,
                'lot_ids': [(6, 0, self.lot_id.ids)]
            }
            move_id = self.env['stock.move'].create(line_vals)
            # move_id = self.env['stock.move'].create(line_vals)
            move_ids_without_package = pack_picking_id.move_ids_without_package
            for move_id in move_ids_without_package:
                move_id.picking_type_id = pack_picking_id.picking_type_id.id
            # pack_picking_id.action_assign()
            # pack_picking_id.action_confirm()
            # lot_id = pack_picking_id.move_line_ids.lot_id
            # if len(lot_id) == 1:
            #     pack_picking_id.move_line_ids.write({'lot_id': lot_id.id})
            move_line_ids = pack_picking_id.move_line_ids[1:]
            move_line_ids.unlink()
            pack_picking_id.move_line_ids.write({'lot_id': self.lot_id.id})
            freight_id.write({'picking_ids': [(4, pack_picking_id.id)]})
            self.pack_picking_id = pack_picking_id.id

            # Ship
            ship_picking_id = self.env['stock.picking'].create({
                'location_id': warehouse_id.out_type_id.default_location_src_id.id,
                'location_dest_id': warehouse_id.out_type_id.default_location_dest_id.id,
                'move_type': 'direct',
                'immediate_transfer': True,
                'picking_type_id': warehouse_id.out_type_id.id,
                'is_locked': True,
                'company_id': location_id.company_id.id,
                'freight_record_id': freight_id.id,
                'partner_id': freight_id.outbound_partner_id.id
            })
            line_vals = {
                'name': product_id.name,
                'location_id': ship_picking_id.location_id.id,
                'location_dest_id': ship_picking_id.location_dest_id.id,
                'picking_id': ship_picking_id.id,
                'product_id': product_id.id,
                'product_uom': product_id.uom_id.id,
                'quantity_done': self.quantity,
                'product_uom_qty': self.quantity,
                'company_id': ship_picking_id.company_id.id,
                'lot_ids': [(6, 0, self.lot_id.ids)]
            }
            move_id = self.env['stock.move'].create(line_vals)
            move_ids_without_package = ship_picking_id.move_ids_without_package
            for move_id in move_ids_without_package:
                move_id.picking_type_id = ship_picking_id.picking_type_id.id
            # ship_picking_id.action_assign()
            # pack_picking_id.action_confirm()
            # lot_id = pack_picking_id.move_line_ids.lot_id
            # if len(lot_id) == 1:
            #     pack_picking_id.move_line_ids.write({'lot_id': lot_id.id})
            move_line_ids = ship_picking_id.move_line_ids[1:]
            move_line_ids.unlink()
            ship_picking_id.move_line_ids.write({'lot_id': self.lot_id.id})
            freight_id.write({'picking_ids': [(4, ship_picking_id.id)], 'transferred_date': fields.Date.today()})
            self.ship_picking_id = ship_picking_id.id

            self.is_osd_inventory_transfered = True
            if self.freight_id.osd_transfer_ids and len(self.freight_id.osd_transfer_ids) == len(self.freight_id.osd_transfer_ids.filtered(lambda x:x.is_osd_inventory_transfered)):
                if self.freight_id.outbound_stage_id.sequence <= self.env.ref('mc_freight_app.staged_outbound').sequence:
                    self.freight_id.outbound_stage_id = self.env.ref('mc_freight_app.staged_outbound').id
                if self.freight_id.osd_rec_stage_id.sequence <= self.env.ref('warefor_3pl_tus.osd_checkin').sequence:
                    self.freight_id.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_checkin').id
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': 'Outbound has been Staged.',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }}
        else:
            picking_type = self.env['stock.picking.type'].search(
                [
                    ('code', '=', 'outgoing'),
                    ('warehouse_id', '=', freight_id.warehouse_id.id),
                    ('warehouse_id.company_id', '=', location_id.company_id.id)
                ],
                limit=1)
            if not picking_type:
                raise ValidationError('Unable to found the operation type in company for this transfer')
            picking_id = self.env['stock.picking'].create({
                'location_id': location_id.id,
                'location_dest_id': destination_location_id.id,
                'move_type': 'direct',
                'immediate_transfer': True,
                'picking_type_id': picking_type.id,
                'is_locked': True,
                'company_id': location_id.company_id.id,
                'freight_record_id': freight_id.id,
                'partner_id': freight_id.outbound_partner_id.id
            })
            product_id = self.sku_id
            line_vals = {
                'name': product_id.name,
                'location_id': picking_id.location_id.id,
                'location_dest_id': picking_id.location_dest_id.id,
                'picking_id': picking_id.id,
                'product_id': product_id.id,
                'product_uom': product_id.uom_id.id,
                'quantity_done': self.quantity,
                'product_uom_qty': self.quantity,
                'company_id': picking_id.company_id.id
            }
            line_id = self.freight_id.freight_order_line_ids.filtered(lambda x: x.goods.id == self.sku_id.id)
            # if self.quantity <= line_id.total_quantity:
            move_id = self.env['stock.move'].create(line_vals)
            # else:
            #     raise ValidationError('Input quantity less than {}'.format(line_id.total_quantity))
            # move_id = self.env['stock.move'].create(line_vals)
            move_ids_without_package = picking_id.move_ids_without_package
            for move_id in move_ids_without_package:
                move_id.picking_type_id = picking_id.picking_type_id.id
            picking_id.action_assign()
            picking_id.action_confirm()
            lot_id = picking_id.move_line_ids.lot_id
            if len(lot_id) == 1:
                picking_id.move_line_ids.write({'lot_id': lot_id.id})
            picking_id.button_validate()
            freight_id.write({'picking_ids': [(4, picking_id.id)], 'transferred_date': fields.Date.today()})
            self.is_osd_inventory_transfered = True
            # if self.freight_id.osd_transfer_ids and len(self.freight_id.osd_transfer_ids) == self.freight_id.osd_transfer_ids.filtered(lambda x:x.is_osd_inventory_transfered):
            #     self.freight_id.outbound_stage_id = self.env.ref('mc_freight_app.staged_outbound').id
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': 'Outbound has been Staged.',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }}

    def validate_pack_transfer(self): # LOAD
        if self.pack_picking_id:
            self.pack_picking_id.action_assign()
            # move_line_ids = self.pack_picking_id.move_line_ids[1:]
            # move_line_ids.unlink()
            if self.lot_id:
                self.pack_picking_id.move_line_ids.write({'lot_id': self.lot_id.id})
            self.pack_picking_id.action_confirm()
            self.pack_picking_id.button_validate()
            # if self.freight_id.osd_transfer_ids and len(self.freight_id.osd_transfer_ids) == len(self.freight_id.osd_transfer_ids.filtered(lambda x:x.pack_picking_state == 'done' and x.is_osd_inventory_transfered)):
            #     self.freight_id.outbound_stage_id = self.env.ref('mc_freight_app.loaded_outbound').id
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': 'Outbound has been Loaded.',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }}

    def validate_ship_transfer(self):  # SHIP
        if self.ship_picking_id:
            self.ship_picking_id.action_assign()
            # move_line_ids = self.ship_picking_id.move_line_ids[1:]
            # move_line_ids.unlink()
            if self.lot_id:
                self.ship_picking_id.move_line_ids.write({'lot_id': self.lot_id.id})
            self.ship_picking_id.action_confirm()
            self.ship_picking_id.button_validate()
            # if self.freight_id.osd_transfer_ids and len(self.freight_id.osd_transfer_ids) == len(self.freight_id.osd_transfer_ids.filtered(lambda x:x.pack_picking_state == 'done' and x.is_osd_inventory_transfered and x.ship_picking_state == 'done')):
            #     self.freight_id.outbound_stage_id = self.env.ref('mc_freight_app.shipped_outbound').id
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': 'Outbound has been Shipped.',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }}

    def open_osd_line_view(self):
        view = self.env.ref('warefor_3pl_tus.osd_freight_transfer_line_action')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'osd.freight.transfer.line',
            'views': [[False, "form"]],
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
        }

    def write(self, vals):
        if vals.get('quantity'):
            display_msg = "Receive Inbounds Line" + \
                          '<br>' + "QUANTITY : " + str(self.quantity)
            res = super(OSDFreightTransferLine, self).write(vals)
            display_msg += " <span class='fa fa-long-arrow-right'/> " + str(self.quantity)
            self.env['mail.message'].create({
                'body': display_msg,
                'model': 'freight.freight',
                'res_id': self.freight_id.id,
                'subtype_id': '2',
            })
            return res
        else:
            return super(OSDFreightTransferLine, self).write(vals)

    @api.model
    def create(self, vals):
        """
        Set warehouse stock location as a destination location in IBL transfer line
        """
        res = super(OSDFreightTransferLine, self).create(vals)
        if (res and not res.is_outbound_pl and
                self.env.user.has_group('user_warehouse_restriction.user_warehouse_restriction_group_user')):
            res.destination_location_id = res.warehouse_id.lot_stock_id.id
        return res
