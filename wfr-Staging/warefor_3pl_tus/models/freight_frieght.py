# -*- coding: utf-8 -*-

import base64
import logging
import math
import calendar
import io
from datetime import date, timedelta, datetime
from calendar import monthrange
import pytz
from dateutil import tz

from odoo import models, fields, api, _
from odoo.tools.misc import xlsxwriter
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class FreightFreight(models.Model):
    _inherit = 'freight.freight'
    _description = 'Transit for shipment and deliveries'

    packaging_qty = fields.Float(_('Packaging Quantity'), default=48.0,
                                 help=_("Pallet package should be W=3, D=4, H=4"))
    import_cost_ids = fields.One2many(comodel_name="pallet.import.cost", inverse_name="transit_app_id",
                                      string=_("Import Cost"))
    fob_cost_ids = fields.One2many(comodel_name="pallet.fob.cost", inverse_name="transit_app_id",
                                   string=_("Calculated against FOB"))
    storage_cost_ids = fields.One2many(comodel_name="pallet.storage.cost", inverse_name="transit_app_id",
                                       string=_("Storage Fees"))
    vas_cost_ids = fields.One2many(comodel_name="pallet.vas.cost", inverse_name="transit_app_id",
                                   string=_("Value Added Service"))
    is_confirmed = fields.Boolean(string="Confirmed Transit Order?")
    invoice_count = fields.Integer(string='Invoice Count', compute="_compute_invoice_count")
    invoice_ids = fields.Many2many('custom.invoice', string='Invoice', copy=False)
    pallet_ids = fields.One2many("pallet.batch.tus", "transit_app_id", string="Pallets")
    total_pallet = fields.Integer("Total Pallets")
    existing_pallet = fields.Integer("Existing Pallets", compute="_compute_existing_pallet")

    entry_number = fields.Char(string="Customs Entry Number")
    awb_no = fields.Char(string="BOL / AWB")
    vessel_name = fields.Char(string="Vessel Name")
    vessel_web_link = fields.Char(string="Vessel Web Link")
    final_destination_id = fields.Many2one(comodel_name="final.destination", string="Final Destination")
    number_of_containers = fields.Char(string="No Of Containers")
    volume = fields.Char(string="Volume")
    # inbound_count = fields.Integer(string='Inbound Count')
    # storage_count = fields.Integer(string='Storage Count')

    markup_import_cost = fields.Float(string="MU (%)", default=00.0)
    import_cost = fields.Float(string=_("Total Inbound Cost"), compute="_compute_import_cost")
    total_storage_cost = fields.Float(string=_("Total Storage Cost"), compute="_compute_existing_pallet")

    pallet_configuration_id = fields.Many2one(comodel_name="pallet.configuration", string="Pallet Configuration")
    product_package_ids = fields.One2many(comodel_name="freight.package.line", inverse_name="freight_id",
                                          string="Package Lines")
    # This both fields for all pallet costs
    cost_per_pallet = fields.Float(string="Cost Per Pallet", compute='_compute_cost_per_pallet_piece', store=True,
                                   help="Cost per pallet")
    cost_per_piece = fields.Float(string="Cost Per Saleable Unit", compute='_compute_cost_per_pallet_piece', store=True,
                                  help="Cost per unit")
    # This fields for FOB price
    company_currency_id = fields.Many2one("res.currency", string='Currency', compute="_compute_currency", readonly=True)
    fob_per_piece = fields.Float(string="FOB Price per Pallet", store=True, compute='_compute_cost_per_pallet_piece',
                                 help="FOB per unit")
    image = fields.Binary(string="Image", tracking=True)
    picking_id = fields.Many2one("stock.picking", string="Recipient")
    shipment_summary = fields.Char(string="Shipment Summary")

    # Docs
    bill_of_lading = fields.Binary(string="Bill of Lading")
    bill_of_lading_file = fields.Char(string="Bill of Lading File")
    certificate_of_origin = fields.Binary(string="Certificate of Origin")
    certificate_of_origin_file = fields.Char(string="Certificate of Origin File")
    customs_entry_summary = fields.Binary(string="Customs Entry Summary")
    customs_entry_summary_file = fields.Char(string="Customs Entry Summary File")
    arrival_notice_ids = fields.Many2many('ir.attachment', 'freight_attachment_arrival_invoice_rel', 'freight_id',
                                          'attachment_id', 'Arrival Notices')
    freight_invoice_ids = fields.Many2many('ir.attachment', 'freight_attachment_freight_invoice_rel', 'freight_id',
                                           'attachment_id', 'Freight Invoices', copy=False)
    other_attachment_ids = fields.Many2many('ir.attachment', 'freight_other_attachment_rel', 'freight_id',
                                            'attachment_id', 'Other')
    pallet_label_number = fields.Integer(string="Pallet Label Number", default=0)
    account_move_ids = fields.Many2many('account.move', 'account_move_freight_freight_rel', 'move_id', 'freight_id',
                                        "Invoices", copy=False)
    account_move_count = fields.Integer(string='Invoice Count', compute="_compute_account_move_count")

    picking_ids = fields.Many2many("stock.picking", string="Transfer Record", copy=False, tracking=True)
    osd_picking_ids = fields.Many2many('stock.picking', 'freight_stock_picking_rel', 'freight_id', 'picking_id',
                                       string='OS&D Transfer', copy=False)
    transfers_count = fields.Integer(string='Transfers Count', compute="_compute_picking_ids", store=True)
    osd_transfers_count = fields.Integer(string='OS&D Transfers Count', store=True)
    transferred_date = fields.Date('Transferred Date')
    customer_po = fields.Char(string="Customer PO", required=False, )
    arrival_at_warefor = fields.Datetime(string="Arrival @ Warefor", required=False, )
    active = fields.Boolean(_('Active'), default=True)
    drayage_id = fields.Many2one(comodel_name="res.partner", string="Drayage / Carrier")
    vendor_code_id = fields.Many2one("vendor.code.line", string="Vendor Code")
    arrive_date = fields.Datetime(string='Arrive Time')
    departure_date = fields.Datetime(string='Departure Time')
    schedule_date = fields.Datetime(string='Scheduled Time')
    date_done = fields.Datetime(string='Order Transmission Date', default=fields.Datetime.now)
    trailer = fields.Char(string="Trailer", tracking=True)
    # truck_driver_name = fields.Many2one(comodel_name="truck.driver.name", string="Driver Name")
    truck_driver_name = fields.Char(string="Driver Name", compute="_compute_truck_driver_name", store=True,
                                    tracking=True)
    signature = fields.Binary(string="Signature")
    driver_signature_date = fields.Datetime(string="Driver Signature Date", compute='_compute_signature_date',
                                            store=True)

    inbound_logistics_id = fields.Many2many('freight.freight', 'freight_freight_outbound_rel', 'freight_id',
                                            'outbound_id', 'Related IBL Records')
    outbound_logistics_id = fields.Many2many('freight.freight', 'freight_freight_inbound_rel', 'freight_id',
                                             'inbound_id', 'Related OBL Records')
    po_date = fields.Date(string="PO Date")
    osd_ids = fields.One2many(comodel_name="freight.osd.report", inverse_name="freight_id", string="OS & D",
                              tracking=True)
    osd_transfer_ids = fields.One2many(comodel_name="osd.freight.transfer.line", inverse_name="freight_id",
                                       string="Transfer Inventory")
    container_start = fields.Datetime(string="Start Time", required=False, )
    container_end = fields.Datetime(string="End Time", required=False, )
    total_time = fields.Float(string="Time Spent", digits=(12, 2), required=False, compute="total_spend_time")
    is_show_btn = fields.Boolean(string="Is Show Button")

    check_in_truck_yard = fields.Datetime(string="Check-In - Truck Yard", tracking=True)
    unload_start_date = fields.Datetime(string="Unload - Start", tracking=True)
    unload_end_date = fields.Datetime(string="Unload - End", tracking=True)
    unload_end_date_local = fields.Datetime(string="Unload - End", compute="compute_unload_end_date")
    loading_end_date_local = fields.Datetime(string="Unload - End", compute="compute_loading_end_date")
    check_in_date_local = fields.Datetime(string="Unload - End", compute="compute_check_in_date")
    unload_time = fields.Char(string="Unload Time", compute="total_unload_time", tracking=True, store=True)
    check_out_truck_yard = fields.Datetime(string="Check-Out - Truck Yard", tracking=True)
    receiving_level_of_service = fields.Float(string="LOS (Days)", tracking=True)
    freight_image = fields.Binary(string="Image", tracking=True)
    detail_file = fields.Binary("File")

    trailer_type = fields.Char(string="Trailer Type", tracking=True)
    pickup_schedule_date = fields.Datetime(string="Tender Drop Date", tracking=True)
    loading_start_date = fields.Datetime(string="Loading Start Date/Time", tracking=True)
    loading_end_date = fields.Datetime(string="Loading End Date/Time", tracking=True)
    loading_time = fields.Char(string="Loading Time", compute="total_loading_time", tracking=True, store=True)
    osd_remark = fields.Char(string="Remark", tracking=True)
    # osd_stage_id = fields.Selection(string="Stage", tracking=True, selection=[('scheduled', 'SCHEDULED'), ('checked_in', 'CHECKED IN'), ('in_progress', 'IN PROGRESS'), ('processed', 'PROCESSED'), ('checked_out', 'CHECKED OUT')], default='new',)
    osd_rec_stage_id = fields.Many2one("freight.osd.stage", string="Warehouse Ops Stage", tracking=True,
                                       group_expand='_read_group_stage_ids')
    vessel_voyage = fields.Char(string="Vessel Voyage")
    load_id_number = fields.Char(string="Load ID #", tracking=True)
    # is_check_in = fields.Boolean(string="Is Check IN")
    # is_started = fields.Boolean(string="Is Start")
    # is_ended = fields.Boolean(string="Is End")

    # is_osd_rec_auto_archive = fields.Boolean(string="Is Auto Archive", compute='_compute_osd_rec_auto_archive')
    internal_transfer_ids = fields.One2many(comodel_name="warefor.internal.transfer", inverse_name="freight_id",
                                            string=_("Internal Transfer"))
    internal_transfers_count = fields.Integer(string='Transfers Count', compute="_compute_internal_transfer_ids",
                                              store=True)
    storage_type_id = fields.Many2one(comodel_name="storage.type.ibl", string="Storage Type")
    is_deleted = fields.Boolean(string="Is Deleted")
    number_of_pallets = fields.Integer(string="# of Pallets", compute="_compute_number_of_pallets", store=True)
    total_line_qty = fields.Integer(string="Total Quantity", compute="_compute_number_of_pallets", store=True)
    is_red_flag = fields.Boolean(string="Red Flag", compute="_compute_red_flag_", store=True, default=False, copy=False)
    tracking_number = fields.Char(string="Tracking #")
    is_imported_record = fields.Boolean(string="Is Imported Record?", default=False, copy=False)

    # E-COMMERCE Part Start

    fulfillment_method = fields.Selection(selection=[('bulk_orders', 'Bulk Orders'), ('e-commerce', 'E-Commerce')],
                                          strigng="Fulfillment Method", default="bulk_orders")

    # retailer_store = fields.Char(string="Retailer / Store")
    edi_store_id = fields.Many2one("edi.customer.store", string="EDI Store ID")
    shipstation_service_id = fields.Many2one('delivery.carrier', string='Shipstation Service',
                                             help="Shipstation service to use for the order from this carrier.")
    shipstation_order_id = fields.Char(string="Order ID")

    ship_to_postal_code = fields.Char(string="Ship To Postal Code")
    carrier_zone = fields.Char(string="Carrier Zone")
    pick_date = fields.Datetime("Pick")
    pack_date = fields.Datetime("Pack")
    out_date = fields.Datetime("Out")
    sale_id = fields.Integer(string="Sale ID")

    # EDI Fields
    edi_carrier_alpha_code = fields.Char(string='EDI Carrier Alpha Code')
    edi_shipment_identifier = fields.Char(string='EDI Shipment Identifier')
    edi_create_date = fields.Date(string='EDI Date')
    edi_bill_of_lading_number = fields.Char(string='EDI Bill of Lading Number')
    edi_bill_of_landing_number = fields.Char(string='CarrierProNumber')
    edi_date_time_qualifier = fields.Char(string='Datetime Qualifier', help='Code specifying the type of date')
    qualifier_date = fields.Datetime(string='Qualifier Datetime', help='Qualifier Date')
    shipping_serial_id = fields.Char("ShippingSerialID")
    carrier_package_id = fields.Char("CarrierPackageID")
    edi_weight_qualifier = fields.Selection(selection=[('G', 'Gross Weight'), ('N', 'Net Weight')],
                                            string='EDI Weight Qualifier', default='N')

    delivery_status = fields.Selection(selection="_delivery_status_selection", string='Delivery Status', tracking=True,
                                       store="True")
    delivery_status_bkp = fields.Char(string='BKP Delivery Status')
    # delivery_status_sel = fields.Selection(DELIVERY_STATUS, string='Delivery Status')
    delivery_history = fields.Text(string='Delivery History')
    # claim_info = fields.Text(string='Claim Info')
    first_scann = fields.Datetime(string='First Scan', tracking=True)
    delivery_eta = fields.Datetime(string='Delivery ETA')
    calculated_eta = fields.Datetime(string='Calculated ETA', compute="_compute_delivery_metrics")
    delivery_actual = fields.Datetime(string='Delivery Actual')
    delivery_metrics = fields.Char(string='Delivery Metrics', compute="_compute_delivery_metrics")

    is_prime_record = fields.Boolean(string='Is Prime?', compute="_compute_is_prime", store=False,
                                     search="_search_is_prime")
    is_prime_locked = fields.Boolean(string='Is Prime Locked?', compute="_compute_is_prime_locked", store=True)
    is_mfc_stage = fields.Boolean(string='Is Missing First Scan?', compute="_compute_mfc_stage", store=True)
    delivery_price = fields.Float("Delivery Price", digits=(8, 2))
    claims = fields.Many2one(comodel_name='freight.claims', string='Claims')
    claim_case_number = fields.Char(string='Claim Case Number')
    claim_check_number = fields.Char(string='Claim Check Number')
    claim_remark = fields.Char(string='Claim Remarks')
    claim_amount = fields.Monetary(string='Claim Amount', currency_field='company_currency_id')

    def calculate_pallets(self):
        self.sync_osd_freight_lines()
        for line in self.freight_order_line_ids:
            if line.freight_id.is_outbound and not line.is_processed:
                line.is_processed = True
                # Fetch full pallet size from the product
                full_pallet_qty = int(line.goods.product_per_pallet)
                if line.total_quantity >= full_pallet_qty != 0:
                    qty = line.total_quantity
                    line.total_quantity = full_pallet_qty
                    line.pallet_type = "Full"
                    qty -= full_pallet_qty

                    # Keep processing until no quantity is left
                    while qty > 0:
                        if qty >= full_pallet_qty:
                            # Create a full pallet line item
                            self.env['freight.order.line'].create({
                                'goods': line.goods.id,
                                'total_quantity': full_pallet_qty,
                                'is_full_pallet': True,  # Mark as full
                                'is_processed': True,
                                'pallet_type': "Full",
                                'po_number': line.po_number,
                                'freight_id': line.freight_id.id,
                            })
                            qty -= full_pallet_qty  # Deduct full pallet size
                        else:
                            # Create a line item for the remainder
                            self.env['freight.order.line'].create({
                                'goods': line.goods.id,
                                'total_quantity': qty,
                                'is_full_pallet': False,  # Not a full pallet
                                'is_processed': True,
                                'po_number': line.po_number,
                                'freight_id': line.freight_id.id,
                            })
                            qty = 0  # Stop processing as all quantity is accounted for

    def unlink_records(self):
        for i in self:
            for j in i.osd_transfer_ids:
                if j.pallet_type != "Full":
                    current = j.sudo().write({
                        'sub_pallet': False,
                        'pallet_type': False,
                        'sscc_18_char': False,
                        'sscc_barcode_id': False
                    })
                    freight = j.freight_order_line_id.sudo().write({
                        'sub_pallet': False,
                        'pallet_type': False,
                        'sscc_18_char': False,
                    })
                    j.freeze = False

    def generate_sscc_18(self):
        """
        Generate Pallet SSCC barcode
        :return:
        """
        for all in self:
            for rec in all.osd_transfer_ids:
                company_name = self.partner_id.company_name or self.partner_id.name
                company_id = self.env['res.company'].sudo().search([('name', '=', company_name)], limit=1)
                if rec.sub_pallet or rec.pallet_type or rec.sscc_18_char:
                    if rec.sscc_18_char and not rec.sscc_barcode_id:
                        already_exist = rec.env['sscc18.barcode'].sudo().search([('sscc18_barcode', '=', rec.sscc_18_char), ('company_id', '=', company_id.id)])
                        rec.sscc_barcode_id = already_exist.id
                    if not rec.sscc_18_char:
                        if rec.pallet_type == 'Mixed' and not rec.sub_pallet:
                            continue
                        """
                        Document Reference: for generating pallet SSCC barcodes
                        https://www.gs1us.org/DesktopModules/Bring2mind/DMX/Download.aspx?Command=Core_Download&EntryId=177&language=en-US&PortalId=0&TabId=134
                        """
                        generated_sscc_code = []
                        app_identifier = "(00)"
                        extension_digit = '0'
                        def calculate_check_digit(number):
                            total = sum(int(d) * (3 if (i % 2 == 0) else 1) for i, d in enumerate(reversed(number)))
                            return (10 - (total % 10)) % 10

                        def extract_serial_no(barcodes, gs1code):
                            gs1_length = len(gs1code) + 5
                            start = len(barcodes) - gs1_length
                            serial_end = 21
                            str_serial_no = str(barcodes[gs1_length:serial_end])
                            return str_serial_no

                        def generate_new_barcode(barcodes, gs1):
                            str_serial_number = extract_serial_no(barcodes, gs1)
                            last_serial_number = int(str_serial_number)
                            width = 16 - len(gs1)
                            new_serial_number = "{:0{width}d}".format(last_serial_number + 1, width=width)
                            sscc_not_check_digit = f"{extension_digit}{gs1_code}{new_serial_number}"
                            check_digits = calculate_check_digit(sscc_not_check_digit)
                            generate_sscc_code = "{app_identifier}{extension_digit}{gs1_code}{serial_number}{check_digit}".format(
                                app_identifier=app_identifier,
                                extension_digit=extension_digit,
                                gs1_code=gs1_code,
                                serial_number=new_serial_number,
                                check_digit=check_digits
                            )
                            return generate_sscc_code
                        if rec.pallet_type == 'Mixed' and rec.sub_pallet:
                            existing_records = self.env['osd.freight.transfer.line'].search([
                                ('freight_id', '=', rec.freight_id.id),
                                ('pallet_type', '=', rec.pallet_type),
                                ('sub_pallet', '=', rec.sub_pallet)
                            ], limit=1)
                            if existing_records.pallet_type == rec.pallet_type and existing_records.sub_pallet == rec.sub_pallet:
                                if existing_records.sscc_18_char:
                                    rec.sscc_18_char = existing_records.sscc_18_char
                                    rec.sscc_barcode_id = existing_records.sscc_barcode_id.id

                                    rec.freight_order_line_id.sudo().write({
                                        'sscc_18_char': rec.sscc_18_char,
                                        'sub_pallet': rec.sub_pallet,
                                        'pallet_type': rec.pallet_type,
                                    })
                                    rec.freeze = True
                                    continue
                        gs1_code = company_id.gs1_company_prefix or "0000000"
                        required_serial_length = 16 - len(gs1_code)
                        if not (7 <= len(gs1_code) <= 10):
                            raise ValidationError("GS1 Company Prefix must be between 7 and 10 digits")
                        last_record = rec.env['sscc18.barcode'].search(
                            [('company_id', '=', company_id.id),
                             ('gs1_code', '=', gs1_code)], order="create_date desc", limit=1)
                        if not last_record:
                            serial_number = "0" * required_serial_length
                            serial_number = serial_number[:-1] + "1"
                            sscc_without_check_digit = f"{extension_digit}{gs1_code}{serial_number}"
                            check_digit = calculate_check_digit(sscc_without_check_digit)
                            generated_sscc_code = "{app_identifier}{extension_digit}{gs1_code}{serial_number}{check_digit}".format(
                                app_identifier=app_identifier,
                                extension_digit=extension_digit,
                                gs1_code=gs1_code,
                                serial_number=serial_number,
                                check_digit=check_digit
                            )
                            sscc_obj = rec.env['sscc18.barcode'].sudo().create({
                                'sscc18_barcode': generated_sscc_code,
                                'company_id': company_id.id,
                                'gs1_code': gs1_code,
                                'serial_no': serial_number
                            })
                            rec.sscc_18_char = generated_sscc_code
                            rec.sscc_barcode_id = sscc_obj.id
                        else:
                            rec_serial = last_record.serial_no
                            len_rec = len(rec_serial)
                            expected_serial_no = '9' * len_rec
                            if rec_serial == expected_serial_no:
                                expired_record = rec.env['sscc18.barcode'].search([('expiry_date', '<', date.today()),
                                                                                   ('company_id', '=',
                                                                                    company_id.id),
                                                                                   ('gs1_code', '=', gs1_code)]
                                                                                  , limit=1)
                                if expired_record:
                                    expired_barcode = expired_record.sscc18_barcode
                                    re_created_rec = rec.env['sscc18.barcode'].sudo().create({
                                        'sscc18_barcode': expired_barcode,
                                        'company_id': company_id.id,
                                        'gs1_code': gs1_code,
                                        'serial_no': expired_record.serial_no
                                    })
                                    rec.sscc_18_char = expired_barcode
                                    rec.sscc_barcode_id = re_created_rec.id
                                    expired_record.unlink()
                            else:
                                last_barcode = last_record.sscc18_barcode
                                if last_record and last_barcode:
                                    generated_sscc_code = generate_new_barcode(last_barcode, gs1_code)
                                    already_exist = rec.env['sscc18.barcode'].sudo().search(
                                        [('sscc18_barcode', '=', generated_sscc_code), ('company_id', '=', company_id.id)])
                                    if already_exist:
                                        highest_rec = rec.env['sscc18.barcode'].sudo().search([
                                            ('company_id', '=', company_id.id)
                                        ], order="sscc18_barcode desc", limit=1)
                                        barcode = highest_rec.sscc18_barcode
                                        generated_sscc_code = generate_new_barcode(barcode, gs1_code)
                                        str_serial_number = extract_serial_no(generated_sscc_code, gs1_code)
                                        new_sscc_obj = rec.env['sscc18.barcode'].sudo().create({
                                            'sscc18_barcode': generated_sscc_code,
                                            'company_id': company_id.id,
                                            'gs1_code': gs1_code,
                                            'serial_no': str_serial_number
                                        })
                                        rec.sscc_18_char = generated_sscc_code
                                        rec.sscc_barcode_id = new_sscc_obj.id
                                    else:
                                        last_serial_number = extract_serial_no(generated_sscc_code, gs1_code)
                                        new_sscc_obj = rec.env['sscc18.barcode'].sudo().create({
                                            'sscc18_barcode': generated_sscc_code,
                                            'company_id': company_id.id,
                                            'gs1_code': gs1_code,
                                            'serial_no': last_serial_number
                                        })
                                        rec.sscc_18_char = generated_sscc_code
                                        rec.sscc_barcode_id = new_sscc_obj.id
                            rec.freeze = True
                            rec.freight_order_line_id.sudo().write({
                                'sub_pallet': rec.sub_pallet,
                                'pallet_type': rec.pallet_type,
                                'sscc_18_char': rec.sscc_18_char
                            })


    def _delivery_status_selection(self):
        stages_ids = self.env['freight.stages.data'].search([])
        tag_ids = stages_ids.mapped('status_ids').sorted('name').mapped('name')
        tag_ids = list(set(tag_ids))
        tag_ids.sort()
        return [(tag, tag) for tag in tag_ids]

    @api.depends('freight_order_line_ids')
    def _compute_is_prime(self):
        for rec in self:
            rec.is_prime_record = False
            if any(rec.freight_order_line_ids.goods.mapped('is_prime')):
                rec.is_prime_record = True

    @api.depends('freight_order_line_ids.goods')
    def _compute_is_prime_locked(self):
        for rec in self:
            rec.is_prime_locked = False
            if any(rec.freight_order_line_ids.goods.mapped('is_prime')):
                rec.is_prime_locked = True

    def _search_is_prime(self, operator, value):
        f_lines = self.env['freight.order.line'].search([('is_outbound', '=', True)])
        f_lines = f_lines.filtered(lambda l: l.goods.is_prime)
        obl_ids = f_lines.freight_id
        return [('id', 'in', obl_ids.ids), ('active', 'in', [True, False])]

    @api.depends('outbound_stage_id')
    def _compute_mfc_stage(self):
        for rec in self:
            mfc_stage_id = self.env.ref('mc_freight_app.missing_first_scan').id
            rec.is_mfc_stage = mfc_stage_id == rec.outbound_stage_id.id and True or False

    @api.model
    def get_views(self, views, options=None):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            options['toolbar'] = False
        res = super().get_views(views, options)
        # if self.env.user.id in BLOCK_USER and res.get('views'):
        #     if res.get('views', {}).get('list', {}).get('arch', "") and 'tree' in res.get('views', {}).get('list', {}).get('arch', ""):
        #         data = res['views']['list']['arch']
        #         data = data.replace("tree", 'tree create="false"', 1)
        #         res['views']['list']['arch'] = data
        #     if res.get('views', {}).get('form', {}).get('arch', "") and 'form' in res.get('views', {}).get('form', {}).get('arch', ""):
        #         data = res['views']['form']['arch']
        #         data = data.replace("form", 'form create="false"', 1)
        #         res['views']['form']['arch'] = data
        #     if res.get('views', {}).get('kanban', {}).get('arch', "") and 'kanban' in res.get('views', {}).get('kanban', {}).get('arch', ""):
        #         data = res['views']['kanban']['arch']
        #         data = data.replace("kanban", 'kanban create="false"', 1)
        #         res['views']['kanban']['arch'] = data
        return res

    @api.depends('delivery_eta', 'delivery_actual', 'pickup_schedule_date')
    def _compute_delivery_metrics(self):
        for rec in self:
            delivery_metrics = ""
            plus_delta = ""
            if rec.first_scann and rec.delivery_actual:
                delivery_metrics = rec.delivery_actual - rec.first_scann
                if rec.pickup_schedule_date and rec.delivery_eta:
                    delta = rec.delivery_eta - rec.delivery_actual
                    plus_delta = rec.pickup_schedule_date + delta
            rec.calculated_eta = plus_delta
            rec.delivery_metrics = str(delivery_metrics)

    @api.onchange('edi_carrier_alpha_code', 'edi_shipment_identifier', 'edi_create_date', 'edi_bill_of_lading_number',
                  'edi_bill_of_landing_number', 'edi_date_time_qualifier', 'qualifier_date', 'shipping_serial_id',
                  'carrier_package_id', 'weight', 'edi_weight_qualifier')
    def _onchange_edi_fields(self):
        for record in self:
            if record.reference:
                sale_id = self.env['sale.order'].sudo().search([('id', '=', record.sale_id)], limit=1)
                if sale_id:
                    out_transfer_id = sale_id.picking_ids.filtered(
                        lambda p: p.picking_type_code == 'outgoing' and p.state not in ['done', 'cancel'])
                    if out_transfer_id:
                        out_transfer_id.edi_carrier_alpha_code = record.edi_carrier_alpha_code
                        out_transfer_id.edi_shipment_identifier = record.edi_shipment_identifier
                        out_transfer_id.edi_create_date = record.edi_create_date
                        out_transfer_id.edi_bill_of_lading_number = record.edi_bill_of_lading_number
                        out_transfer_id.edi_bill_of_landing_number = record.edi_bill_of_landing_number
                        out_transfer_id.edi_date_time_qualifier = record.edi_date_time_qualifier
                        out_transfer_id.qualifier_date = record.qualifier_date
                        out_transfer_id.shipping_serial_id = record.shipping_serial_id
                        out_transfer_id.carrier_package_id = record.carrier_package_id
                        out_transfer_id.edi_weight_qualifier = record.edi_weight_qualifier
                        out_transfer_id.edi_obl_weight = record.weight
                        out_transfer_id.edi_obl_uom = "LB"

    # E-COMMERCE Part End

    @api.depends('freight_order_line_ids.required_pallet')
    def _compute_number_of_pallets(self):
        for rec in self:
            if rec.freight_order_line_ids:
                pallets = rec.freight_order_line_ids.mapped('required_pallet')
                total_quantity = rec.freight_order_line_ids.mapped('total_quantity')
                rec.number_of_pallets = sum(pallets)
                rec.total_line_qty = sum(total_quantity)
            else:
                rec.number_of_pallets = 0
                rec.total_line_qty = 0

    @api.depends('osd_rec_stage_id', 'osd_transfer_ids', 'freight_order_line_ids',
                 'osd_transfer_ids.is_osd_inventory_transfered', 'osd_transfer_ids.pack_picking_state',
                 'osd_transfer_ids.ship_picking_state')
    def _compute_red_flag_(self):
        for rec in self:
            total_quantity = rec.freight_order_line_ids.mapped('total_quantity')
            received_qty = rec.freight_order_line_ids.mapped('qty_received')
            staged_qty = rec.freight_order_line_ids.mapped('qty_staged')
            shipped_qty = rec.freight_order_line_ids.mapped('qty_shipped')
            rec.is_red_flag = False
            if rec.is_outbound:
                if rec.osd_rec_stage_id.name in ['Checked In (IB Full) / Staged (OB)',
                                                 'Processed (IB Empty/OB Loaded)']:
                    rec.is_red_flag = True if sum(total_quantity) > sum(staged_qty) else False
                elif rec.osd_rec_stage_id.name == 'Checked Out':
                    rec.is_red_flag = True if sum(total_quantity) > sum(shipped_qty) else False
            else:
                if rec.osd_rec_stage_id.name in ['Processed (IB Empty/OB Loaded)', 'Checked Out']:
                    rec.is_red_flag = True if sum(total_quantity) > sum(received_qty) else False

    def delete_two_step_verification(self):
        if len(self._context.get('active_ids') or []) > 1:
            if self.env.user.has_group('warefor_3pl_tus.group_ibl_obl_multi_record_delete_access'):
                res = self.unlink()
                return res
            raise UserError("Sorry, You can't delete multiple record at a time.")
        if not self.env.user.has_group('warefor_3pl_tus.group_ibl_obl_delete_access'):
            raise UserError("Sorry, You can't delete this Record.")

        name = _('Confirm')
        view = self.env.ref('warefor_3pl_tus.freight_2step_delete_view_form')
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'freight.2step.delete',
            'views': [(view.id, 'form')],
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'new',
            'context': {'default_freight_id': self.id}
        }

    def generate_internal_transfer(self):
        """
        Create warefor Internal Transfer
        :return:
        """
        name = _('Confirm')
        view = self.env.ref('warefor_3pl_tus.freight_2step_delete_view_form')
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'freight.2step.delete',
            'views': [(view.id, 'form')],
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'new',
            'context': {'default_freight_id': self.id}
        }

    def button_internal_transfers(self):
        internal_transfer_ids = self.internal_transfer_ids.ids
        return {
            'name': _('Transfers'),
            'view_mode': 'tree,form',
            'res_model': 'warefor.internal.transfer',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', internal_transfer_ids)],
        }

    @api.onchange('name')
    def _onchange_name(self):
        for rec in self:
            if rec.is_outbound:
                if self.search([('name', '=', rec.name), ('is_outbound', '=', True)]).__len__() > 1:
                    raise UserError(_('Record already exists with this name create obl'))
            if not rec.is_outbound:
                if self.search([('name', '=', rec.name), ('is_outbound', '!=', True)]).__len__() > 1:
                    raise UserError(_('Record already exists with this name create ibl'))

    @api.depends('internal_transfer_ids')
    def _compute_internal_transfer_ids(self):
        for record in self:
            record.internal_transfers_count = len(record.internal_transfer_ids)
            for internal_transfer_id in record.internal_transfer_ids:
                internal_transfer_id.freight_id = record.id

    def open_wizard_credit_memo(self):
        # invoice_ids = self.mapped('account_move_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("warefor_3pl_tus.action_custom_credit_memo_wz")
        action['context'] = dict(self.env.context)
        action['context']['invoice_id_domain'] = self.account_move_ids.filtered(lambda i: i.state == 'posted').ids
        return action

    @api.depends('osd_transfer_ids.is_osd_inventory_transfered')
    def _compute_remaining_qty(self):
        for record in self:
            total_line_qty = sum(record.freight_order_line_ids.mapped('total_quantity'))
            received_line = record.osd_transfer_ids.filtered(lambda x: x.is_osd_inventory_transfered)
            osd_line_qty = sum(received_line.mapped('quantity'))
            if not total_line_qty == osd_line_qty:
                record.is_remaining_qty = False
                record.color = 3
            else:
                record.is_remaining_qty = True

    is_remaining_qty = fields.Boolean(string="Is Remaining", default=True, compute='_compute_remaining_qty', store=True)

    # @api.depends('osd_transfer_ids.is_osd_inventory_transfered', 'account_move_count', 'check_out_truck_yard')
    # def _compute_osd_rec_auto_archive(self):
    #     for rec in self:
    #         rec.is_osd_rec_auto_archive = True
    #         if rec.osd_transfer_ids and rec.active:
    #             is_active = all(rec.osd_transfer_ids.mapped('is_osd_inventory_transfered'))
    #             picking_ids = rec.picking_ids.filtered(lambda p: p.state in ['done', 'cancel'])
    #             if rec.account_move_count and is_active and picking_ids and len(picking_ids) == len(rec.picking_ids):
    #                 if not rec.is_outbound and rec.check_out_truck_yard:
    #                     rec.is_osd_rec_auto_archive = is_active
    #                     rec.active = not is_active
    #                 elif rec.is_outbound:
    #                     rec.is_osd_rec_auto_archive = is_active
    #                     rec.active = not is_active

    def compute_loading_end_date(self):
        for rec in self:
            rec.loading_end_date_local = rec.loading_end_date
            if rec.loading_end_date:
                rec.loading_end_date_local = rec.loading_end_date.replace(tzinfo=pytz.timezone(rec.env.user.tz)).date()
                from_zone = tz.gettz('UTC')
                to_zone = tz.gettz(rec.env.user.tz)
                loading_end_date_utc = rec.loading_end_date.replace(tzinfo=from_zone)
                rec.loading_end_date_local = loading_end_date_utc.astimezone(to_zone).date()

    def compute_unload_end_date(self):
        for rec in self:
            rec.unload_end_date_local = rec.unload_end_date
            if rec.unload_end_date:
                rec.unload_end_date_local = rec.unload_end_date.replace(tzinfo=pytz.timezone(rec.env.user.tz)).date()
                from_zone = tz.gettz('UTC')
                to_zone = tz.gettz(rec.env.user.tz)
                unload_end_date_utc = rec.unload_end_date.replace(tzinfo=from_zone)
                rec.unload_end_date_local = unload_end_date_utc.astimezone(to_zone).date()

    def compute_check_in_date(self):
        for rec in self:
            rec.check_in_date_local = rec.check_in_truck_yard
            if rec.check_in_truck_yard:
                rec.check_in_date_local = rec.check_in_truck_yard.replace(tzinfo=pytz.timezone(rec.env.user.tz)).date()
                from_zone = tz.gettz('UTC')
                to_zone = tz.gettz(rec.env.user.tz)
                check_in_truck_yard_utc = rec.check_in_truck_yard.replace(tzinfo=from_zone)
                rec.check_in_date_local = check_in_truck_yard_utc.astimezone(to_zone).date()

    def _compute_currency(self):
        company_currency_id = self.env.company.currency_id.id
        for rec in self:
            rec.company_currency_id = company_currency_id

    def open_ibl_ops_record(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'freight.freight',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [[self.env.ref('warefor_3pl_tus.freight_freights_osd_main_form_view').id, 'form']],
            'context': {'is_ops_model': True},
        }

    def _generate_osd_line(self):
        for freight_id in self.env['freight.freight'].search([]):
            osd_line_list = []
            for line in freight_id.freight_order_line_ids:
                osd_id = freight_id.osd_ids.filtered(lambda o: o.sku_id.id == line.goods.id)
                if osd_id:
                    continue
                line_val = (0, 0, {
                    'sku_id': line.goods and line.goods.id or None,
                    'freight_id': freight_id.id,
                    'osd_total_qty': line.total_quantity,
                })
                osd_line_list.append(line_val)
            freight_id.write({"osd_ids": osd_line_list})

    @api.onchange('pickup_schedule_date')
    def _onchange_pickup_schedule_date(self):
        for rec in self:
            if rec._origin.osd_rec_stage_id.sequence <= self.env.ref('warefor_3pl_tus.osd_scheduled').sequence:
                rec._origin.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_scheduled').id
            if rec._origin.stage_id.sequence <= self.env.ref('mc_freight_app.freight_quote').sequence:
                rec._origin.stage_id = self.env.ref('mc_freight_app.freight_quote').id
            if rec.is_outbound and rec._origin.outbound_stage_id.sequence <= self.env.ref(
                    'mc_freight_app.scheduled_outbound').sequence:
                rec._origin.outbound_stage_id = self.env.ref('mc_freight_app.scheduled_outbound').id

    @api.onchange('check_in_truck_yard')
    def _onchange_check_in_truck_yard(self):
        for rec in self:
            if rec._origin.osd_rec_stage_id.sequence <= self.env.ref('warefor_3pl_tus.osd_checkin').sequence:
                rec._origin.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_checkin').id
            if rec._origin.stage_id.sequence <= self.env.ref('mc_freight_app.inventory_received_at_brw').sequence:
                rec._origin.stage_id = self.env.ref('mc_freight_app.inventory_received_at_brw').id

    @api.onchange('unload_start_date')
    def _onchange_unload_start_date(self):
        for rec in self:
            if rec._origin.osd_rec_stage_id.sequence <= self.env.ref('warefor_3pl_tus.osd_inprocess').sequence:
                rec._origin.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_inprocess').id
            if rec._origin.stage_id.sequence <= self.env.ref('mc_freight_app.unloading_truck').sequence:
                rec._origin.stage_id = self.env.ref('mc_freight_app.unloading_truck').id

    @api.onchange('unload_end_date')
    def _onchange_unload_end_date(self):
        for rec in self:
            if rec._origin.osd_rec_stage_id.sequence <= self.env.ref('warefor_3pl_tus.osd_processed').sequence:
                rec._origin.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_processed').id
            if rec._origin.stage_id.sequence <= self.env.ref('mc_freight_app.empties_stage').sequence:
                rec._origin.stage_id = self.env.ref('mc_freight_app.empties_stage').id

    #         ================================================

    @api.onchange('loading_start_date')
    def _onchange_loading_start_date(self):
        for rec in self:
            if rec._origin.osd_rec_stage_id.sequence <= self.env.ref('warefor_3pl_tus.osd_inprocess').sequence:
                rec._origin.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_inprocess').id
            if rec._origin.outbound_stage_id.sequence <= self.env.ref('mc_freight_app.loading_outbound').sequence:
                rec._origin.outbound_stage_id = self.env.ref('mc_freight_app.loading_outbound').id

    @api.onchange('loading_end_date')
    def _onchange_loading_end_date(self):
        for rec in self:
            if rec._origin.osd_rec_stage_id.sequence <= self.env.ref('warefor_3pl_tus.osd_processed').sequence:
                rec._origin.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_processed').id
            if rec._origin.outbound_stage_id.sequence <= self.env.ref('mc_freight_app.loaded_outbound').sequence:
                rec._origin.outbound_stage_id = self.env.ref('mc_freight_app.loaded_outbound').id

    #         ================================================

    @api.onchange('check_out_truck_yard')
    def _onchange_check_out_truck_yard(self):
        for rec in self:
            if rec.check_out_truck_yard:
                if rec._origin.osd_rec_stage_id.sequence <= self.env.ref('warefor_3pl_tus.osd_checkout').sequence:
                    rec._origin.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_checkout').id
                if rec.stage_id.sequence <= self.env.ref('mc_freight_app.container_checked_out').sequence:
                    rec.stage_id = self.env.ref('mc_freight_app.container_checked_out').id
                if rec.outbound_stage_id.sequence <= self.env.ref('mc_freight_app.shipped_outbound').sequence:
                    rec.outbound_stage_id = self.env.ref('mc_freight_app.shipped_outbound').id
                # rec.active = False

    def container_start_time(self):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            return True
        if self.unload_start_date:
            raise UserError(_('Already Unloading Started !'))
        if not self.check_in_truck_yard:
            raise UserError(_('Please CHECK IN First !'))
        self.write({"unload_start_date": fields.Datetime.now(),
                    "osd_rec_stage_id": self.env.ref('warefor_3pl_tus.osd_inprocess').id,
                    "stage_id": self.env.ref('mc_freight_app.unloading_truck').id, })

    def container_stop_time(self):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            return True
        if self.unload_end_date:
            raise UserError(_('Already Unloading Stoped !'))
        self.unload_end_date = fields.Datetime.now()
        self.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_processed').id
        self.stage_id = self.env.ref('mc_freight_app.empties_stage').id
        if not self.check_in_truck_yard:
            raise UserError(_('Please CHECK IN First !'))
        if not self.unload_start_date:
            raise UserError(_('Please START unloading First !'))

    def container_checkin(self):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            return True
        if self.check_in_truck_yard:
            raise UserError(_('Already Check In !'))
        self.write({"check_in_truck_yard": fields.Datetime.now(),
                    "check_out_truck_yard": False,
                    "loading_start_date": False,
                    "loading_end_date": False,
                    "date_done": False})
        self.write({"osd_rec_stage_id": self.env.ref('warefor_3pl_tus.osd_checkin').id,
                    "stage_id": self.env.ref('mc_freight_app.inventory_received_at_brw').id, })

    def container_checkout(self):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            return True
        if self.check_out_truck_yard:
            raise UserError(_('Already Check Out !'))
        if self.is_outbound:
            if not self.loading_end_date:
                raise UserError(_('Please END Loading First !'))
        else:
            if not self.unload_end_date:
                raise UserError(_('Please STOP Unloading First !'))
        self.check_out_truck_yard = fields.Datetime.now()
        self.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_checkout').id
        self.stage_id = self.env.ref('mc_freight_app.container_checked_out').id
        self.outbound_stage_id = self.env.ref('mc_freight_app.shipped_outbound').id
        # self.active = False
        if not self.check_in_truck_yard:
            raise UserError(_('Please CHECK IN First !'))

    def loading_start_time(self):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            return True
        if self.loading_start_date:
            raise UserError(_('Already Loading Started !'))
        self.write({"check_out_truck_yard": False,
                    "loading_start_date": fields.Datetime.now(),
                    "loading_end_date": False,
                    "date_done": False})
        self.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_inprocess').id
        self.outbound_stage_id = self.env.ref('mc_freight_app.loading_outbound').id
        if not self.check_in_truck_yard:
            raise UserError(_('Please CHECK IN First !'))
        for rec in self:
            for transfer in rec.osd_transfer_ids.filtered(lambda x: x.pack_picking_id):
                transfer.pack_picking_id.action_assign()

    def loading_stop_time(self):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            return True
        if self.loading_end_date:
            raise UserError(_('Already Loading Ended !'))
        self.write({"check_out_truck_yard": False,
                    "loading_end_date": fields.Datetime.now(),
                    "date_done": False})
        self.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_processed').id
        self.outbound_stage_id = self.env.ref('mc_freight_app.loaded_outbound').id
        if not self.check_in_truck_yard:
            raise UserError(_('Please CHECK IN First !'))
        if not self.loading_start_date:
            raise UserError(_('Please START First !'))

    def bol_date_update(self):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            return True
        if self.date_done:
            raise UserError(_('BOL Date Already Generated !'))
        self.write({"check_out_truck_yard": False, "date_done": fields.Datetime.now()})
        if not self.check_in_truck_yard:
            raise UserError(_('Please CHECK IN First !'))

    @api.depends('date_done', 'loading_start_date', 'loading_end_date', 'out_date')
    def total_loading_time(self):
        """
            Counting loading Time and LEVEL OF SERVICE (Days)
        """
        for rec in self:
            if rec.pickup_schedule_date and rec.out_date and rec.fulfillment_method == 'e-commerce':
                loading_time = rec.out_date - rec.pickup_schedule_date
                rec.loading_time = str(loading_time)
            else:
                rec.loading_time = ""

            if rec.loading_start_date and rec.loading_end_date and rec.fulfillment_method != 'e-commerce':
                loading_time = rec.loading_end_date - rec.loading_start_date
                rec.loading_time = str(loading_time)
            else:
                rec.loading_time = rec.loading_time or ""

            if rec.date_done and rec.loading_end_date:
                time = rec.loading_end_date - rec.date_done
                tot_min = time.total_seconds() / 60
                total_time = tot_min and tot_min / 60
                days = total_time / 24
                rec.receiving_level_of_service = days
            else:
                rec.receiving_level_of_service = ""

    @api.depends('unload_start_date', 'unload_end_date', 'check_in_truck_yard')
    def total_unload_time(self):
        """
            Counting Unloading Time and LEVEL OF SERVICE (Days)
        """
        for rec in self:
            if rec.check_in_truck_yard and rec.unload_end_date:
                time = rec.unload_end_date - rec.check_in_truck_yard
                tot_min = time.total_seconds() / 60
                total_time = tot_min and tot_min / 60
                days = total_time / 24
                rec.receiving_level_of_service = days
            else:
                rec.receiving_level_of_service = ""

            if rec.unload_start_date and rec.unload_end_date:
                time = rec.unload_end_date - rec.unload_start_date
                rec.unload_time = time
            else:
                rec.unload_time = ""

    @api.depends('freight_order_line_ids')
    def _compute_weight_volume(self):
        for rec in self:
            for lines in rec.freight_order_line_ids:
                lines.total_value()
                lines.set_gross_weight()
                lines.onchange_required_pallet()

            total_qty = sum(rec.freight_order_line_ids.mapped('total_quantity')) or 1

            rec.weight = sum(rec.freight_order_line_ids.mapped('net_weight'))
            rec.weight_kg = rec.weight * 0.453592

            rec.volume_cuft = sum(rec.freight_order_line_ids.mapped('volume_by_ft'))
            rec.volume_cbm = rec.volume_cuft / 35.3147

            # rec.cost_per_cuft = rec.volume_cuft / total_qty
            # rec.cost_per_cbm = rec.volume_cbm / total_qty

            data = []
            transfer_line = []
            stock_quant = self.env['stock.quant']
            company_ids = self.env["res.company"].search([('is_logistics', '=', True)])

            # rec.generate_pallet_config_ids()

            for line in rec.freight_order_line_ids:
                if rec.is_outbound:
                    osd_transfer_ids = rec.osd_transfer_ids.filtered(lambda o: o.sku_id.id == line.goods.id)
                    if osd_transfer_ids:
                        continue
                    quant_ids = stock_quant.search(
                        [('product_id', '=', line.goods.id),
                         ('lot_id', '=', line.lot_id.id),
                         ('company_id', 'in', company_ids.ids),
                         ('location_id.warehouse_id', '=', rec.warehouse_id.id),
                         ('location_id.is_omit_on_source_location', '=', False),
                         ('location_id.usage', '=', 'internal')], order='in_date ASC')
                    left_quantity = line.total_quantity
                    destination_location = self.env['stock.location'].search(
                        [('warehouse_id', '=', rec.warehouse_id.id), ('is_destination_location', '=', True)])
                    if not destination_location:
                        raise UserError(_("Please configure the destination location first!"))
                    while left_quantity > 0:
                        if not quant_ids:
                            left_quantity = 0
                            continue
                        quant_id = quant_ids[0]
                        added_qty = min(left_quantity, quant_id.available_quantity)
                        if added_qty:
                            left_quantity = left_quantity - added_qty
                            transfer_line.append((0, 0, {'sku_id': line.goods.id, 'quantity': added_qty,
                                                         'lot_id': line.lot_id.id,
                                                         'location_id': quant_id.location_id.id,
                                                         'destination_location_id': destination_location[0].id}))
                        quant_ids = quant_ids[1:]
                else:
                    osd_id = rec.osd_ids.filtered(lambda o: o.sku_id.id == line.goods.id)
                    osd_transfer_ids = rec.osd_transfer_ids.filtered(lambda o: o.sku_id.id == line.goods.id)
                    if not osd_id:
                        data.append((0, 0, {'sku_id': line.goods.id, 'osd_total_qty': line.total_quantity}))
                    if not osd_transfer_ids:
                        transfer_line.append(
                            (
                                0, 0,
                                {'sku_id': line.goods.id, 'quantity': line.total_quantity, 'lot_id': line.lot_id.id}))
            if data:
                rec.osd_ids = data
            if transfer_line:
                rec.osd_transfer_ids = transfer_line

    @api.depends('signature')
    def _compute_truck_driver_name(self):
        """
        Generating sequence for bol number in IBL/OBL record
        :return:
        """
        for record in self:
            record.truck_driver_name = record.truck_driver_name
            if record.signature:
                record.date_done = fields.Datetime.now()
                if record.env.company.company_code == 'WFL':
                    bol_number = self.env['ir.sequence'].next_by_code('sequ.bol.wfl')
                    record['bol_number'] = bol_number
                elif record.env.company.company_code == 'WFS':
                    bol_number = self.env['ir.sequence'].next_by_code('sequ.bol.wfs')
                    record['bol_number'] = bol_number
            #     self.truck_driver_name = ''

    @api.depends('container_start', 'container_end')
    def total_spend_time(self):
        """
        """
        for rec in self:
            rec.total_time = 0
            container_end = rec.container_end or fields.Datetime.now()
            if rec.container_start:
                time = container_end - rec.container_start
                tot_min = time.total_seconds() / 60
                rec.total_time = tot_min and tot_min / 60

    def osd_report(self, product_ids=[]):
        data = {'freight_ids': self.ids, 'product_ids': product_ids}
        return self.env.ref('warefor_3pl_tus.osd_report_template').report_action(self, data=data)
        # return self

    def default_ship_from(self):
        """
        Returns: record set
        """
        ship_from_partner = list(set(
            self.env['stock.warehouse'].sudo().search([]).filtered(lambda w: w.is_3pl_warehouse).mapped(
                'partner_id.id')))
        return [('id', 'in', ship_from_partner)]

    ship_from_partner_id = fields.Many2one("res.partner", string="Ship From", domain=default_ship_from)

    @api.depends('signature')
    def _compute_signature_date(self):
        for rec in self:
            rec.driver_signature_date = fields.Datetime.now()

    # def action_view_bill_of_lading(self):
    #     picking_ids = self.mapped('picking_ids')
    #     if not picking_ids:
    #         raise ValidationError("Unable to found transfer in this IBL record!")
    #     report = self.env['ir.actions.report']._get_report_from_name("warefor_3pl_tus.logistic_record_bill_of_lading_report")
    #     context = dict(self.env.context, active_ids=picking_ids.ids)
    #
    #     report_action = {
    #         'context': context,
    #         'type': 'ir.actions.report',
    #         'report_name': report.report_name,
    #         'report_type': report.report_type,
    #         'report_file': report.report_file,
    #         'name': report.name,
    #     }
    #
    #     return report_action

    def generate_sign(self):
        action = self.env["ir.actions.actions"]._for_xml_id("warefor_3pl_tus.mark_sign_wizard_action")
        action['context'] = {'default_freight_id': self.id}
        return action

    # @api.onchange('inbound_logistics_id', 'outbound_logistics_id')
    # def onchange_inbound_outbound_logistics_id(self):
    #     #     """
    #     #     Linking logistics records (two-way links from/to each record).
    #     #     """
    #
    #     if not self._context.get('no_update_data_ibl'):
    #         for inbound_logistics_id in self.inbound_logistics_id:
    #             inbound_logistics_id.with_context(no_update_data_ibl=True).write({'inbound_logistics_id': [(6, 0, self._origin.ids)]})
    #
    #     if not self._context.get('no_update_data_obl'):
    #         for outbound_logistics_id in self.outbound_logistics_id:
    #             outbound_logistics_id.with_context(no_update_data_obl=True).write({'outbound_logistics_id': [(6, 0, self._origin.ids)]})

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for record in self:
            # record.transfers_count = len(record.picking_ids)
            new_transfer = self.env["stock.picking"].search([('freight_record_id', '=', record.id)])
            record.transfers_count = len(new_transfer)

    # def name_get(self):
    #     if self._name != 'freight.freight':
    #         res = super(FreightFreight, self).name_get()
    #         return res
    #     res = []
    #     for record in self:
    #         res.append((record.id, ("%s") % (record.reference or record.name)))
    #     return res

    @api.depends('import_cost_ids', 'fob_cost_ids', 'storage_cost_ids', 'vas_cost_ids', 'freight_order_line_ids')
    def _compute_cost_per_pallet_piece(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        for record in self:
            total_pallet_qty = sum(record.freight_order_line_ids.mapped('required_pallet'))
            total_qty = sum(record.freight_order_line_ids.mapped('total_quantity'))
            net_weight = sum(record.freight_order_line_ids.mapped('net_weight')) or 1
            total_kg = sum(record.freight_order_line_ids.mapped('total_kg')) or 1
            total_pallet = record.total_pallet or total_pallet_qty
            total_standard_price = sum(record.freight_order_line_ids.mapped('value'))

            if total_standard_price and total_qty:
                record.fob_per_piece = round(total_standard_price / total_qty, 2)
            else:
                record.fob_per_piece = 0

            if not total_pallet:
                record.cost_per_pallet = 0
                record.cost_per_piece = 0
                continue

            import_cost = sum(record.import_cost_ids.mapped('total_cost'))
            fob_cost = sum(record.fob_cost_ids.mapped('total_cost'))
            storage_cost = record.total_storage_cost
            vas_cost = sum(record.vas_cost_ids.mapped('total_cost'))

            total_cost = sum([import_cost, fob_cost, storage_cost, vas_cost])

            record.cost_per_pallet = total_pallet and round(total_cost / total_pallet, 2) or 0
            record.cost_per_piece = total_qty and round(total_cost / total_qty, 2) or 0

            record.price_per_pound = net_weight and total_cost / net_weight or 0
            total_weight_kg = net_weight * 0.45359237
            if record.is_outbound:
                record.price_per_kg = total_cost / total_weight_kg * 1000
                record.cost_per_cuft = record.volume_cuft and total_cost / record.volume_cuft or 0
            else:
                weight_metric_ton = record.weight_kg / 1000
                record.price_per_kg = weight_metric_ton and total_cost / weight_metric_ton or 0
                record.cost_per_cuft = record.weight and total_cost / record.weight or 0
            record.cost_per_cbm = record.volume_cbm and total_cost / record.volume_cbm or 0

    @api.onchange('pallet_configuration_id')
    def onchange_pallet_configuration_id(self):
        for rec in self:
            pallet_configuration = rec.pallet_configuration_id
            product_package_ids = rec.product_package_ids
            if product_package_ids:
                rec.freight_order_line_ids.write({'total_pallet': 0, 'required_pallet': 0})
                product_package_ids.unlink()
            if not pallet_configuration:
                continue
            data = []
            for line in rec.freight_order_line_ids:
                product_uom_qty = line.total_quantity
                total_pallet = 0
                packaging_qty = 0
                product = line.goods
                if product_uom_qty and pallet_configuration and product:
                    if not product.packaging_id:
                        packaging_qty = product.product_per_pallet
                        if packaging_qty:
                            total_pallet = math.ceil(product_uom_qty / packaging_qty)
                    else:
                        package = product.packaging_id
                        package_qty = package.qty
                        if not package_qty:
                            continue
                        pallet_qty = 0
                        total_pallet = 0
                        required_package = math.ceil(product_uom_qty / package_qty)
                        packaging_qty = package.package_per_pallet
                        total_pallet = packaging_qty and math.ceil(required_package / packaging_qty) or 0
                        vals = {
                            'package_qty': required_package,
                            'require_pallets': total_pallet,
                            'package_per_pallet': packaging_qty,
                            'product_qty': product_uom_qty,
                            'package_id': package.id
                        }
                        data.append((0, 0, vals))

                line.total_pallet = packaging_qty
                line.required_pallet = math.ceil(total_pallet)
            if data:
                rec.write({'product_package_ids': data, 'pallet_configuration_id': pallet_configuration.id})

    @api.onchange('loading_end_date', 'unload_end_date')
    def _onchange_obl_invoice_date(self):
        if self.is_outbound:
            for record in self.account_move_ids:
                record._origin.update({'invoice_date': self.loading_end_date_local})
        else:
            for record in self.account_move_ids:
                record._origin.update({'invoice_date': self.unload_end_date_local})

    @api.onchange('markup_import_cost')
    def _onchange_markup_import_cost(self):
        for rec in self:
            rec.import_cost_ids.write({'processing_fee_per': rec.markup_import_cost})

    @api.depends('import_cost_ids.total_cost', 'markup_import_cost')
    def _compute_import_cost(self):
        for record in self:
            import_cost_ids = record.import_cost_ids
            fob_cost_ids = record.fob_cost_ids
            import_cost_total = import_cost_ids and sum(import_cost_ids.mapped('total_cost')) or 0
            fob_cost_total = fob_cost_ids and sum(fob_cost_ids.mapped('total_cost')) or 0
            record.import_cost = import_cost_total + fob_cost_total

    # @api.depends('import_cost_ids.total_cost', 'markup_import_cost')
    # def _compute_storage_cost(self):
    #     for record in self:
    #         import_cost_ids = record.import_cost_ids
    #         import_cost_total = import_cost_ids and sum(import_cost_ids.mapped('total_cost')) or 0
    #         record.import_cost = import_cost_total

    @api.depends("pallet_ids")
    def _compute_existing_pallet(self):
        """
        Compute exist pallets in Transit App to use it in creating invoice
        :return:
        """
        for rec in self:
            rec.existing_pallet = len(rec.pallet_ids) - len(rec.pallet_ids.filtered(lambda p: p.end_date))
            storage_cost_ids = rec.storage_cost_ids
            storage_cost = storage_cost_ids and sum(storage_cost_ids.mapped('total_cost')) or 0
            rec.total_storage_cost = storage_cost

    @api.depends("invoice_ids")
    def _compute_invoice_count(self):
        """
        Count the number of custom invoices attached with Transit App
        :return:
        """
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    @api.depends("account_move_ids")
    def _compute_account_move_count(self):
        """
        Count the number of Account Moves attached with Transit App
        :return:
        """
        for rec in self.sudo():
            rec.account_move_count = len(rec.account_move_ids)

    # def action_shipment_confirmation(self):
    #     # for po in self.purchase_orders_ids:
    #     #     if po.state in ['draft', 'sent', 'to approve']:
    #     #         po.with_context(transit_app=self).button_confirm()
    #     confirmation_stage = self.env['freight.stage'].search([('is_shipment_confirmation', '=', True)], limit=1)
    #     if confirmation_stage:
    #         return False
    #         self.write({'stage_id': confirmation_stage.id, 'is_confirmed': True})

    @api.model
    def create(self, vals):
        stage_id = self.env.ref('mc_freight_app.dock_audit_approved', False)
        if stage_id:
            vals.update({'stage_id': stage_id.id})
        if self._context.get('import_file'):
            vals.update({'is_imported_record': True, 'fulfillment_method': 'e-commerce'})
        res = super(FreightFreight, self).create(vals)
        # required_pallet = res.freight_order_line_ids.filtered(lambda x:x.goods and x.required_pallet != 0).mapped('required_pallet')
        # total_unit = math.ceil(sum(required_pallet))
        # [vas.update({'total_unit': total_unit, 'total_cost': total_unit * vas.unit_price}) for vas in res.vas_cost_ids]
        if res.is_outbound:
            if self.search([('name', '=', res.name), ('is_outbound', '=', True)]).__len__() > 1:
                raise UserError(_('Record already exists with this name create obl'))
        if not res.is_outbound:
            if self.search([('name', '=', res.name), ('is_outbound', '!=', True)]).__len__() > 1:
                raise UserError(_('Record already exists with this name create ibl'))
        # if self.search([('name', '=', res.name)]).__len__() > 1:
        #     raise UserError(_('Record already exists with this name'))
        for inbound_logistics_id in res.inbound_logistics_id:
            inbound_logistics_id.update({'inbound_logistics_id': [(6, 0, res._origin.ids)]})
        for outbound_logistics_id in res.outbound_logistics_id:
            outbound_logistics_id.update({'outbound_logistics_id': [(6, 0, res._origin.ids)]})
        res.write({"osd_rec_stage_id": self.env.ref('warefor_3pl_tus.freight_osd_new').id})
        if res.pickup_schedule_date:
            res.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_scheduled').id
            res.stage_id = self.env.ref('mc_freight_app.freight_quote').id
            res.outbound_stage_id = self.env.ref('mc_freight_app.scheduled_outbound').id
        if res.check_in_truck_yard:
            res.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_checkin').id
            res.stage_id = self.env.ref('mc_freight_app.inventory_received_at_brw').id
        if res.loading_start_date:
            res.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_inprocess').id
            res.outbound_stage_id = self.env.ref('mc_freight_app.loading_outbound').id
        if res.loading_end_date:
            res.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_processed').id
            res.outbound_stage_id = self.env.ref('mc_freight_app.loaded_outbound').id
        if res.unload_start_date:
            res.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_inprocess').id
            res.stage_id = self.env.ref('mc_freight_app.unloading_truck').id
        if res.unload_end_date:
            res.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_processed').id
            res.stage_id = self.env.ref('mc_freight_app.empties_stage').id
        if res.check_out_truck_yard:
            res.osd_rec_stage_id = self.env.ref('warefor_3pl_tus.osd_checkout').id
            res.stage_id = self.env.ref('mc_freight_app.container_checked_out').id
            res.outbound_stage_id = self.env.ref('mc_freight_app.shipped_outbound').id

        res._compute_weight_volume()

        if not res.vas_cost_ids and not self._context.get('so_number') and self._context.get('is_oxford_process'):
            res.create_vas_cost_lines()
        elif not self._context.get('is_oxford_process'):
            res.generate_pallet_config_ids()

        if not res.actual_req_items:
            items = []
            for each in res.freight_order_line_ids:
                items.append((0, 0, {
                    'product_id': each.goods.id,
                    'case_qty': each.qty_carton,
                    'quantity': each.total_quantity
                }))
            res.actual_req_items = items

        # if res._context.get('import_file') and res._context.get('is_outbound'):
        #     res.do_3_step_process()
        return res

    def freight_do_3_step_process(self):
        company_id = self.env['res.company'].search([('is_logistics', '=', True)], limit=1)
        if company_id:
            self = self.with_company(company_id)
        domain = [('create_date', '>=', "04/01/2024"), ('is_outbound', '=', True), ('picking_ids', '=', False),
                  ('fulfillment_method', '=', 'e-commerce'), ('outbound_stage_id.name', '!=', "Review")]
        freight_ids = self.env['freight.freight'].search(domain, limit=100)
        if company_id:
            freight_ids = freight_ids.check_stock_avilalibility()
            freight_ids.with_company(company_id).with_context(skip_access_process=True).do_3_step_process()
        return True

    def check_stock_avilalibility(self):
        freight_ids = self.env['freight.freight']
        stock_quant = self.env['stock.quant']
        company_ids = self.env["res.company"].search([('is_logistics', '=', True)])
        for rec in self:
            warehouse_id = rec.warehouse_id

            is_avilable_stock = []
            for line in rec.freight_order_line_ids:
                quant_ids = stock_quant.search([('product_id', '=', line.goods.id),
                                                ('location_id.usage', '=', 'internal'),
                                                ('location_id.warehouse_id', '=', warehouse_id.id),
                                                ('company_id', 'in', company_ids.ids),
                                                ('location_id.is_omit_on_source_location', '=', False)],
                                               order='create_date', limit=1)
                quant_ids = quant_ids.filtered(lambda q: q.available_quantity > line.total_quantity)
                if quant_ids:
                    is_avilable_stock.append(True)
                else:
                    is_avilable_stock.append(False)
            if is_avilable_stock and all(is_avilable_stock):
                freight_ids |= rec
            else:
                rec.outbound_stage_id = self.env.ref('mc_freight_app.shipped_review', raise_if_not_found=False).id
        return freight_ids

    def action_view_invoice(self):
        invoice_ids = self.mapped('invoice_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("warefor_3pl_tus.custom_invoice_action")
        action['domain'] = [('id', 'in', invoice_ids.ids)]
        return action

    def action_view_account_move(self):
        invoices = self.mapped('account_move_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_move_type': 'out_invoice',
        }
        if len(self) == 1:
            context.update({
                'default_partner_id': self.import_id and self.import_id.id,
                'default_user_id': self.user_id.id,
            })
        action['context'] = context
        return action

    def open_wizard_for_invoice(self):
        # invoice_ids = self.mapped('invoice_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("warefor_3pl_tus.act_custom_invoice_wizard_1")
        # action['domain'] = [('id', 'in', invoice_ids.ids)]
        return action

    def write(self, vals):
        """
        When change the any costs in transit record, then automatically change the pallet cost
        :param vals:
        :return:
        """
        # for rec in self:
        #     is_confirmed = rec.is_confirmed
        #     if vals.get('arrival_at_warefor'):
        #         stage_id = self.env.ref('mc_freight_app.freight_quote', False)
        #         if stage_id:
        #             vals.update({'stage_id': stage_id.id})
        # if self.env.user.id in BLOCK_USER:
        #     raise UserError(_("You don't have enough access, Please contact your system administrator."))
        for rec in self:
            if 'delivery_status' in vals.keys() and rec.is_outbound:
                new_status = self.get_delivery_status(vals.get('delivery_status'))
                if new_status:
                    vals['outbound_stage_id'] = new_status
            elif 'first_scann' in vals.keys() and rec.is_outbound:
                new_status = self.get_delivery_status(vals.get('delivery_status') or rec.delivery_status)
                if new_status:
                    vals['outbound_stage_id'] = new_status
        res = super(FreightFreight, self).write(vals)
        self.osd_transfer_ids.onchange_destination_location_id()
        for rec in self:
            if rec.is_outbound:
                if rec.search([('name', '=', rec.name), ('is_outbound', '=', True)]).__len__() > 1:
                    if 'shipstation' in str(rec._context):
                        rec.name = 'SHIPSTATION ' + rec.name
                    else:
                        raise UserError(_('Record already exists with this name write obl {}'.format(rec.name)))
            else:
                if rec.search([('name', '=', rec.name), ('is_outbound', '!=', True)]).__len__() > 1:
                    raise UserError(_('Record already exists with this name write ibl {}'.format(rec.name)))
            if 'inbound_logistics_id' in vals and not rec._context.get('no_update_data_ibl'):
                for inbound_logistics_id in rec.inbound_logistics_id:
                    inbound_logistics_id.with_context(no_update_data_ibl=True).write(
                        {'inbound_logistics_id': [(6, 0, rec._origin.ids)]})

            if 'outbound_logistics_id' in vals and not rec._context.get('no_update_data_obl'):
                for outbound_logistics_id in rec.outbound_logistics_id:
                    outbound_logistics_id.with_context(no_update_data_obl=True).write(
                        {'outbound_logistics_id': [(6, 0, rec._origin.ids)]})

            import_cost = []
            storage_cost = []
            vas_cost = []
            fob_cost = []
            data = {}
            # pallets = rec.pallet_ids.filtered(lambda x: not x.end_date)
            pallets = rec.pallet_ids
            if pallets:
                if 'import_cost_ids' in vals.keys():
                    pallets.import_cost_ids.unlink()
                    for import_cost_id in rec.import_cost_ids:
                        import_cost.append((0, 0, {
                            'name': import_cost_id.name,
                            'product_id': import_cost_id.product_id.id,
                            'actual_cost': rec.total_pallet and import_cost_id.actual_cost / rec.total_pallet or 0,
                            # 'processing_fee_per': import_cost_id.processing_fee_per,
                        }))
                    data.update({"import_cost_ids": import_cost})
                if 'fob_cost_ids' in vals.keys():
                    pallets.fob_cost_ids.unlink()
                    for fob_cost_id in rec.fob_cost_ids:
                        fob_cost.append((0, 0, {
                            'product_id': fob_cost_id.product_id.id,
                            'fob_per': fob_cost_id.fob_per,
                            'total_cost': fob_cost_id.total_cost,
                        }))
                    data.update({"fob_cost_ids": fob_cost})
                if 'storage_cost_ids' in vals.keys():
                    pallets.storage_cost_ids.unlink()
                    for storage_cost_id in rec.storage_cost_ids:
                        storage_cost.append((0, 0, {
                            'name': storage_cost_id.name,
                            'product_id': storage_cost_id.product_id.id,
                            'unit_of_measure': storage_cost_id.unit_of_measure,
                            'total_pallet': storage_cost_id.total_pallet,
                            'total_cubic_feet': storage_cost_id.total_cubic_feet,
                            'unit_price': round(storage_cost_id.unit_price, 4),
                            'total_cost': storage_cost_id.total_cost,
                        }))
                    data.update({"storage_cost_ids": storage_cost})
                if 'vas_cost_ids' in vals.keys():
                    pallets.vas_cost_ids.unlink()
                    for vas_cost_id in rec.vas_cost_ids:
                        vas_cost.append((0, 0, {
                            'name': vas_cost_id.name,
                            'product_id': vas_cost_id.product_id.id,
                            'unit_of_measure': vas_cost_id.unit_of_measure,
                            'total_cost': rec.total_pallet and vas_cost_id.total_cost / rec.total_pallet or 0,
                        }))
                    data.update({"vas_cost_ids": vas_cost})
                if 'markup_import_cost' in vals.keys():
                    data.update({"markup_import_cost": rec.markup_import_cost})
                if data:
                    pallets.write(data)
        return res

    def get_delivery_status(self, status=''):
        if not status:
            return self.env.ref('mc_freight_app.in_transit').id

        status = status.lower().replace(" ", "")

        stages_ids = self.env['freight.stages.data'].search([])

        for stage in stages_ids:
            for status_id in stage.status_ids:
                if status_id.name.lower().replace(" ", "") == status:
                    return stage.freight_stage_id.id

    def generate_invoice(self):

        import_id = self.is_outbound and self.outbound_partner_id.id or (
                self.import_id and self.import_id.id or False)

        if not import_id:
            raise ValidationError("Please add the customer/vendor for invoice!")

        import_cost_product = self.env['product.product'].search([('default_code', '=', 'IMP00100')], limit=1)
        vas_cost_product = self.env['product.product'].search([('default_code', '=', 'HDM00100')], limit=1)
        invoice_end_date = self.env.context.get('end_date')

        default_journal = self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', self.env.company.id)], limit=1)
        invoice = self.env['account.move'].create({
            'partner_id': import_id,
            'invoice_date': invoice_end_date,
            'move_type': 'out_invoice',
            'journal_id': default_journal.id,
        })
        invoice._onchange_partner_id()
        invoice_line_ids = []
        freight_record_ids = self.purchase_orders_ids.freight_record
        pallet_ids = freight_record_ids.mapped('pallet_ids').filtered(lambda p: p.end_date != p.start_date)
        if not pallet_ids:
            raise ValidationError("Pallets are currently not stored in the storage area!")
        if invoice:
            invoice_line = self.env['custom.invoice'].create({
                'partner_id': import_id,
                'invoice_type': 'wfl_inbound',
                'invoice_date': invoice_end_date,
                'invoice_id': invoice.id,
                'transit_app_id': self.id,
                'company_id': invoice.company_id.id
            })
            if invoice_line:
                for freight_record in freight_record_ids:
                    qty = 0.00
                    pallet_ids = freight_record.pallet_ids.filtered(lambda p: p.end_date != p.start_date)
                    if not pallet_ids:
                        continue
                    total_days = 0
                    for rec in freight_record.freight_order_line_ids:
                        line_id = self.env['custom.invoice.line'].search(
                            [('invoice_id', '=', invoice_line.id), ('product_id', '=', rec.goods.id),
                             ('qty', '=', round(rec.total_quantity, 2))])
                        if line_id:
                            qty_mrg = round(rec.total_quantity, 2) + line_id.qty
                            price_mrg = rec.value + line_id.price
                            line_id.write({
                                'invoice_id': invoice_line.id,
                                'product_id': rec.goods.id,
                                'qty': qty_mrg,
                                'unit_price': round(rec.base_cost, 8),
                                'price': price_mrg,
                                'is_exclude': True,
                                'uom_id': rec.goods.uom_id.id
                            })
                        else:
                            invoice_line.order_lines.create({
                                'invoice_id': invoice_line.id,
                                'product_id': rec.goods.id,
                                'qty': round(rec.total_quantity, 2),
                                'unit_price': round(rec.base_cost, 8),
                                'price': rec.value,
                                'is_exclude': True,
                                'uom_id': rec.goods.uom_id.id
                            })
                        name_line = "Product: {name}   | Quantity: {qty}   | Unit Price: ${s_price}   | Total FOB Price: ${total}".format(
                            name=rec.goods.name.ljust(20),
                            qty=round(rec.total_quantity, 2),
                            s_price=round(rec.base_cost, 8),
                            total=rec.value)
                        invoice_line_ids.append((0, 0, {
                            'name': name_line,
                            'display_type': 'line_section'
                        }))
                        qty += rec.total_quantity
                    total_import_cost = sum(freight_record.fob_cost_ids.mapped('total_cost'))
                    total_import_cost += freight_record.import_cost
                    invoice_line.order_lines.create({
                        'invoice_id': invoice_line.id,
                        'product_id': import_cost_product.id,
                        'name': "Import Cost",
                        'qty': qty,
                        'unit_price': round(total_import_cost / qty, 8),
                        'uom_id': import_cost_product.uom_id.id
                    })
                    invoice_line_ids.append((0, 0, {
                        'name': "Import Cost",
                        'product_id': import_cost_product.id,
                        'price_unit': round(total_import_cost / qty, 8),
                        'quantity': qty,
                        'month_qty': 1,
                        'discount': 0.0,
                        'product_uom_id': import_cost_product.uom_id.id
                    }))
                    total_cost = sum(freight_record.vas_cost_ids.mapped('total_cost'))
                    invoice_line.order_lines.create({
                        'invoice_id': invoice_line.id,
                        'name': vas_cost_product.name or 'Handling and Materials',
                        'product_id': vas_cost_product.id,
                        'qty': qty,
                        'unit_price': round(total_cost / qty, 8),
                        'uom_id': vas_cost_product.uom_id.id
                    })
                    invoice_line_ids.append((0, 0, {
                        'name': vas_cost_product.name or 'Handling and Materials',
                        'product_id': vas_cost_product.id,
                        'price_unit': round(total_cost / qty, 8),
                        'quantity': qty,
                        'month_qty': 1,
                        'discount': 0.0,
                        'product_uom_id': vas_cost_product.uom_id.id
                    }))
            self.invoice_ids = [(4, invoice_line.id)]
            self.invoice_count += 1
            level2_invoice = self.generate_inbound_invoice_level_b(invoice)
            invoice_line.write({'l2_invoice_id': level2_invoice.id})

            level3_invoice = self.generate_inbound_invoice_level_c(invoice)
            self.invoice_count += 1

            invoice_line.write({'l3_invoice_id': level3_invoice.id})
            level2_invoice.write({'l3_invoice_id': level3_invoice.id})
        invoice.write({'invoice_line_ids': invoice_line_ids})

    def generate_inbound_invoice_level_b(self, invoice_id=False):
        import_id = self.import_id
        invoice_end_date = self.env.context.get('end_date')
        if not import_id:
            raise ValidationError("Vendor is not set in this freight record!")
        custom_invoice_line = []
        import_cost_product = self.env['product.product'].search([('default_code', '=', 'IMP00100')], limit=1)
        vas_cost_product = self.env['product.product'].search([('default_code', '=', 'HDM00100')], limit=1)
        current_date = self.env.context.get('end_date') or fields.date.today()
        invoice_line = False
        freight_record_ids = self.purchase_orders_ids.freight_record
        pallet_ids = freight_record_ids.mapped('pallet_ids').filtered(lambda p: p.end_date != p.start_date)
        if not pallet_ids:
            raise ValidationError("Pallets are currently not stored in the storage area!")
        if invoice_id:
            invoice_line = self.env['custom.invoice'].with_context(level_invoice="Level 2 Inbound Invoice").create({
                'partner_id': import_id.id,
                'invoice_type': 'wfl_inbound',
                'invoice_date': invoice_end_date,
                'invoice_id': invoice_id.id,
                'transit_app_id': self.id,
                'company_id': invoice_id.company_id.id
            })
            if invoice_line:
                for freight_record in freight_record_ids:
                    qty = 0.00
                    pallet_ids = freight_record.pallet_ids.filtered(lambda p: p.end_date != p.start_date)
                    if not pallet_ids:
                        continue
                    total_days = 0
                    for rec in freight_record.freight_order_line_ids:
                        invoice_line.order_lines.create({
                            'invoice_id': invoice_line.id,
                            'product_id': rec.goods.id,
                            'unit_price': round(rec.base_cost, 8),
                            'qty': rec.total_quantity,
                            'is_exclude': True,
                            'uom_id': rec.goods.uom_id.id
                        })
                        qty += rec.total_quantity
                    total_import_cost = sum(freight_record.fob_cost_ids.mapped('total_cost'))
                    total_import_cost += freight_record.import_cost
                    invoice_line.order_lines.create({
                        'invoice_id': invoice_line.id,
                        'product_id': import_cost_product.id,
                        'name': "Import Cost",
                        'qty': qty,
                        'unit_price': round(total_import_cost / qty, 8),
                        'is_exclude': True,
                        'uom_id': import_cost_product.uom_id.id
                    })
                    total_cost = sum(freight_record.vas_cost_ids.mapped('total_cost'))
                    invoice_line.order_lines.create({
                        'invoice_id': invoice_line.id,
                        'name': vas_cost_product.name or 'Handling and Materials',
                        'product_id': vas_cost_product.id,
                        'qty': qty,
                        'unit_price': round(total_cost / qty, 8),
                        'is_exclude': True,
                        'uom_id': vas_cost_product.uom_id.id
                    })
                    for pallet_id in pallet_ids:
                        pallet_qty = pallet_id.product_ids and sum(pallet_id.product_ids.mapped('product_qty')) or 0
                        if pallet_qty:
                            for product_id in pallet_id.product_ids:
                                product_id = product_id.product_id
                                name = "In: {} - Out: {}".format(pallet_id.start_date + timedelta(days=1) or '',
                                                                 pallet_id.end_date or '')
                                freight_order_line_id = freight_record.freight_order_line_ids.filtered(
                                    lambda l: l.goods.id == product_id.id)
                                freight_order_line_id = freight_order_line_id and freight_order_line_id[
                                    0] or freight_order_line_id
                                custom_invoice_line.append((0, 0, {
                                    'product_id': product_id.id,
                                    'name': name,
                                    'pallet_name': pallet_id.name or '',
                                    'unit_price': round(freight_order_line_id.base_cost, 8),
                                    'uom_id': product_id.uom_id.id,
                                    'qty': pallet_qty,
                                    'is_exclude': True,
                                }))
                            price_per_pallet = total_import_cost / len(freight_record.pallet_ids)
                            unit_price = price_per_pallet / pallet_qty
                            custom_invoice_line.append((0, 0, {
                                'product_id': import_cost_product.id,
                                'name': import_cost_product.name or 'Import Cost',
                                'unit_price': unit_price,
                                'qty': pallet_qty,
                                'uom_id': import_cost_product.uom_id.id
                            }))
                            total_cost = sum(freight_record.vas_cost_ids.mapped('total_cost'))
                            material_cost_pallet = total_cost / len(freight_record.pallet_ids)
                            unit_price = material_cost_pallet / pallet_qty
                            custom_invoice_line.append((0, 0, {
                                'product_id': vas_cost_product.id,
                                'name': vas_cost_product.name or 'Handling and Materials',
                                'unit_price': unit_price,
                                'qty': pallet_qty,
                                'uom_id': vas_cost_product.uom_id.id
                            }))
            if custom_invoice_line:
                invoice_line.write({'order_lines': custom_invoice_line})

        return invoice_line

    def generate_inbound_invoice_level_c(self, invoice_id=False):
        import_id = self.import_id
        invoice_end_date = self.env.context.get('end_date')
        if not import_id:
            raise ValidationError("Vendor is not set in this freight record!")
        custom_invoice_line = []
        import_cost_product = self.env['product.product'].search([('default_code', '=', 'IMP00100')], limit=1)
        vas_cost_product = self.env['product.product'].search([('default_code', '=', 'HDM00100')], limit=1)
        if not self.pallet_ids:
            raise ValidationError(
                "Pallets are currently not stored in the storage area!\nPlease first move it on storage area!")
        invoice_line = False

        if invoice_id:
            invoice_line = self.env['custom.invoice'].with_context(level_invoice="Level 3 Inbound Invoice").create({
                'partner_id': import_id.id,
                'invoice_type': 'wfl_inbound',
                'invoice_date': invoice_end_date,
                'invoice_id': invoice_id.id,
                'transit_app_id': self.id,
                'company_id': invoice_id.company_id.id
            })
            freight_record_ids = self.purchase_orders_ids.freight_record
            pallet_ids = freight_record_ids.mapped('pallet_ids').filtered(lambda p: p.end_date != p.start_date)
            if not pallet_ids:
                raise ValidationError("Pallets are currently not stored in the storage area!")
            if invoice_line:
                for freight_record in freight_record_ids:
                    qty = 0.00
                    pallet_ids = freight_record.pallet_ids.filtered(lambda p: p.end_date != p.start_date)
                    if not pallet_ids:
                        continue
                    total_days = 0
                    product_cost_data = {}
                    for rec in freight_record.freight_order_line_ids:
                        product_cost_data.update({rec.goods.id: rec.base_cost})
                        invoice_line.order_lines.create({
                            'invoice_id': invoice_line.id,
                            'product_id': rec.goods.id,
                            'unit_price': round(rec.base_cost, 8),
                            'qty': rec.total_quantity,
                            'is_exclude': True,
                            'uom_id': rec.goods.uom_id.id
                        })
                        qty += rec.total_quantity
                    total_import_cost = sum(freight_record.fob_cost_ids.mapped('total_cost'))
                    total_import_cost += freight_record.import_cost
                    invoice_line.order_lines.create({
                        'invoice_id': invoice_line.id,
                        'product_id': import_cost_product.id,
                        'name': "Import Cost",
                        'qty': qty,
                        'unit_price': round(total_import_cost / qty, 8),
                        'is_exclude': True,
                        'uom_id': import_cost_product.uom_id.id
                    })

                    total_cost = sum(freight_record.vas_cost_ids.mapped('total_cost'))
                    invoice_line.order_lines.create({
                        'invoice_id': invoice_line.id,
                        'name': vas_cost_product.name or 'Handling and Materials',
                        'product_id': vas_cost_product.id,
                        'qty': qty,
                        'unit_price': round(total_cost / qty, 8),
                        'is_exclude': True,
                        'uom_id': vas_cost_product.uom_id.id
                    })
                    total_pallet = len(pallet_ids)
                    vas_total_cost = sum(freight_record.vas_cost_ids.mapped('total_cost'))
                    for pallet_id in pallet_ids:
                        pallet_qty = pallet_id.product_ids and sum(pallet_id.product_ids.mapped('product_qty')) or 0
                        if pallet_qty:
                            for product_id in pallet_id.product_ids:
                                product_id = product_id.product_id
                                name = "In: {} - Out: {}".format(pallet_id.start_date + timedelta(days=1) or '',
                                                                 pallet_id.end_date or '')
                                custom_invoice_line.append((0, 0, {
                                    'product_id': product_id.id,
                                    'name': name,
                                    'pallet_name': pallet_id.name or '',
                                    'unit_price': round(product_cost_data.get(product_id.id), 8),
                                    'uom_id': product_id.uom_id.id,
                                    'qty': pallet_qty,
                                    'is_exclude': True,
                                }))
                            price_per_pallet = total_import_cost / total_pallet
                            unit_price = price_per_pallet / pallet_qty
                            custom_invoice_line.append((0, 0, {
                                'product_id': import_cost_product.id,
                                'name': import_cost_product.name or 'Import Cost',
                                'unit_price': unit_price,
                                'qty': pallet_qty,
                                'is_exclude': True,
                                'uom_id': import_cost_product.uom_id.id
                            }))
                            for import_cost_id in freight_record.import_cost_ids:
                                total_cost = import_cost_id.total_cost
                                price = round(total_cost / total_pallet, 8)
                                qty = total_cost and round(price / total_cost, 8) or 0
                                custom_invoice_line.append((0, 0, {
                                    'product_id': import_cost_id.product_id.id,
                                    'name': import_cost_id.product_id.name or 'Import Cost',
                                    'unit_price': total_cost,
                                    'qty': qty,
                                    'uom_id': import_cost_id.product_id.uom_id.id
                                }))

                            for fob_cost_id in freight_record.fob_cost_ids:
                                total_cost = fob_cost_id.total_cost
                                price = round(total_cost / total_pallet, 8)
                                qty = total_cost and round(price / total_cost, 8) or 0
                                custom_invoice_line.append((0, 0, {
                                    'product_id': fob_cost_id.product_id.id,
                                    'name': fob_cost_id.product_id.name,
                                    'unit_price': total_cost,
                                    'qty': qty,
                                    'uom_id': fob_cost_id.product_id.uom_id.id
                                }))

                            material_cost_pallet = vas_total_cost / total_pallet
                            unit_price = material_cost_pallet / pallet_qty
                            custom_invoice_line.append((0, 0, {
                                'product_id': vas_cost_product.id,
                                'name': vas_cost_product.name or 'Handling and Materials',
                                'unit_price': unit_price,
                                'qty': pallet_qty,
                                'is_exclude': True,
                                'uom_id': vas_cost_product.uom_id.id,
                            }))

                            for vas_cost_id in freight_record.vas_cost_ids:
                                total_cost = vas_cost_id.total_cost
                                price = round(total_cost / total_pallet, 8)
                                qty = total_cost and round(price / total_cost, 8) or 0
                                custom_invoice_line.append((0, 0, {
                                    'product_id': vas_cost_id.product_id.id,
                                    'name': vas_cost_id.product_id.name or 'Handling and Materials',
                                    'unit_price': total_cost,
                                    'qty': qty,
                                    'uom_id': vas_cost_product.uom_id.id
                                }))
            if custom_invoice_line:
                invoice_line.write({'order_lines': custom_invoice_line})

        return invoice_line

    def generate_broker_invoice(self):
        import_id = self.import_id
        if not import_id:
            raise ValidationError("Vendor is not set in this freight record!")
        # logistic_company = self.env["res.company"].search([('is_logistics', '=', True)], limit=1)
        import_cost_product = self.env['product.product'].search([('default_code', '=', 'IMP00100')], limit=1)
        invoice = self.env['account.move'].create({
            'partner_id': import_id.id,
            'invoice_date': date.today(),
            'move_type': 'out_invoice',
            # "company_id": logistic_company.id
        })
        invoice._onchange_partner_id()
        invoice_line_ids = []
        if invoice:
            invoice_line = self.env['custom.invoice'].create({
                'partner_id': self.partner_id.ids[0],
                'invoice_type': 'broker_invoice',
                'invoice_date': date.today(),
                'invoice_id': invoice.id,
                'transit_app_id': self.id
            })
            invoice_line.order_lines.create({
                'invoice_id': invoice_line.id,
                'product_id': import_cost_product.id,
                'name': "Import Cost",
                'qty': 1,
                'unit_price': round(self.import_cost, 8),
            })
            invoice_line_ids.append((0, 0, {
                'name': "Import Cost",
                'product_id': import_cost_product.id,
                'price_unit': self.import_cost,
                'quantity': 1,
                'month_qty': 1,
                'discount': 0.0,
            }))
            self.invoice_ids = [(4, invoice_line.id)]
            self.invoice_count += 1
        invoice.write({'invoice_line_ids': invoice_line_ids})

    def generate_wfl_level_a_invoice(self):
        import_id = self.import_id
        if not import_id:
            raise ValidationError("Vendor is not set in this freight record!")
        default_journal = self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', self.env.company.id)], limit=1)
        invoice_line_ids = []
        custom_invoice_line = []
        total_days = 0
        total_quantity = 0
        current_date = self.env.context.get('end_date')
        pallet_total_cost = sum(self.storage_cost_ids.mapped("total_cost"))
        storage_product_id = self.storage_cost_ids and self.storage_cost_ids[0].product_id
        pallet_ids = self.pallet_ids.filtered(lambda p: p.end_date != p.start_date)
        if not pallet_ids:
            raise ValidationError(
                "Pallets are currently not stored in the storage area!\nPlease first move it on storage area!")
        # pallet_total_cost = pallet_total_cost * len(pallet_ids)
        invoice_id = self.env['account.move'].create({
            'partner_id': import_id.id,
            'move_type': 'out_invoice',
            'invoice_date': current_date,
            'journal_id': default_journal.id,
        })
        freight_record_ids = self.purchase_orders_ids.freight_record
        pallet_ids = freight_record_ids.mapped('pallet_ids').filtered(lambda p: p.end_date != p.start_date)
        if not pallet_ids:
            raise ValidationError("Pallets are currently not stored in the storage area!")
        if invoice_id:
            invoice_line = self.env['custom.invoice'].create({
                'partner_id': import_id.id,
                'invoice_type': 'wfl_storage',
                'invoice_date': current_date,
                'invoice_id': invoice_id.id,
                'transit_app_id': self.id,
                'company_id': invoice_id.company_id.id
            })
            if invoice_line:
                for freight_record in freight_record_ids:
                    pallet_ids = freight_record.pallet_ids.filtered(lambda p: p.end_date != p.start_date)
                    if not pallet_ids:
                        continue
                    total_days = 0
                    for rec in freight_record.freight_order_line_ids:
                        line_id = self.env['custom.invoice.line'].search(
                            [('invoice_id', '=', invoice_line.id), ('product_id', '=', rec.goods.id)])
                        if line_id:
                            qty_mrg = round(rec.total_quantity, 2) + line_id.qty
                            line_id.write({
                                'qty': qty_mrg,
                                'unit_price': round(rec.base_cost, 8),
                                'is_exclude': True
                            })
                        else:
                            invoice_line.order_lines.create({
                                'invoice_id': invoice_line.id,
                                'product_id': rec.goods.id,
                                'unit_price': round(rec.base_cost, 8),
                                'qty': rec.total_quantity,
                                'is_exclude': True,
                                'uom_id': rec.goods.uom_id.id
                            })

                        name_line = "Product: {name}   | Quantity: {qty}   | Unit Price: ${s_price}   | Total FOB Price: ${total}".format(
                            name=rec.goods.name.ljust(20),
                            qty=round(rec.total_quantity, 2),
                            s_price=round(rec.base_cost, 8),
                            total=rec.value)
                        invoice_line_ids.append((0, 0, {
                            'name': name_line,
                            'display_type': 'line_section'
                        }))
                        total_quantity += rec.total_quantity
                    for pallet_id in pallet_ids:
                        today_date = current_date
                        days = today_date - pallet_id.start_date
                        if pallet_id.end_date:
                            today_date = pallet_id.end_date
                            days = pallet_id.end_date - pallet_id.start_date
                        total_days += (days and days.days + 1 or 0)
                    invoice_line_ids.append((0, 0, {
                        'name': storage_product_id.name,
                        'product_id': storage_product_id.id,
                        'price_unit': pallet_total_cost,
                        'quantity': total_days,
                        'month_qty': 1,
                        'discount': 0.0,
                        'product_uom_id': storage_product_id.uom_id.id
                    }))
                    invoice_line.order_lines.create({
                        'invoice_id': invoice_line.id,
                        'product_id': storage_product_id.id,
                        'unit_price': pallet_total_cost,
                        'qty': total_days,
                        'is_exclude': False,
                        'uom_id': storage_product_id.uom_id.id
                    })
            if custom_invoice_line:
                invoice_line.write({'order_lines': custom_invoice_line})
            if invoice_line_ids and invoice_id:
                invoice_id.write({'invoice_line_ids': invoice_line_ids})

            self.invoice_ids = [(4, invoice_line.id)]
            self.invoice_count += 1
            custom_invoice_l2_id = self.generate_wfl_level_b_invoice(invoice_id)
            custom_invoice_l3_id = self.generate_wfl_level_c_invoice(invoice_id)
            invoice_line.write({'l2_invoice_id': custom_invoice_l2_id.id, 'l3_invoice_id': custom_invoice_l3_id.id})

    def generate_wfl_level_b_invoice(self, invoice_id=False):
        import_id = self.import_id
        if not import_id:
            raise ValidationError("Vendor is not set in this freight record!")
        custom_invoice_line = []
        pallet_total_cost = sum(self.storage_cost_ids.mapped("total_cost"))
        storage_product_id = self.storage_cost_ids and self.storage_cost_ids[0].product_id.id
        current_date = self.env.context.get('end_date')
        pallet_ids = self.pallet_ids.filtered(lambda p: p.end_date != p.start_date)
        if not pallet_ids:
            raise ValidationError(
                "Pallets are currently not stored in the storage area!\nPlease first move it on storage area!")
        invoice_line = False
        if invoice_id:
            invoice_line = self.env['custom.invoice'].with_context(level_invoice="Level 2 Storage Invoice").create({
                'partner_id': import_id.id,
                'invoice_type': 'wfl_storage',
                'invoice_date': date.today(),
                'invoice_id': invoice_id.id,
                'transit_app_id': self.id,
                'company_id': invoice_id.company_id.id
            })
            freight_record_ids = self.purchase_orders_ids.freight_record
            pallet_ids = freight_record_ids.mapped('pallet_ids').filtered(lambda p: p.end_date != p.start_date)
            if not pallet_ids:
                raise ValidationError("Pallets are currently not stored in the storage area!")
            if invoice_line:
                for freight_record in freight_record_ids:
                    pallet_ids = freight_record.pallet_ids.filtered(lambda p: p.end_date != p.start_date)
                    if not pallet_ids:
                        continue
                    for rec in freight_record.freight_order_line_ids:
                        invoice_line.order_lines.create({
                            'invoice_id': invoice_line.id,
                            'product_id': rec.goods.id,
                            'unit_price': round(rec.base_cost, 8),
                            'qty': rec.total_quantity,
                            'is_exclude': True
                        })
                    for pallet_id in pallet_ids:
                        end_date = pallet_id.end_date
                        pallet_qty = pallet_id.product_ids and sum(pallet_id.product_ids.mapped('product_qty')) or 0
                        if pallet_qty:
                            for product_id in pallet_id.product_ids:
                                product_id = product_id.product_id
                                name = "In: {} - Out: {}".format(pallet_id.start_date + timedelta(days=1) or '',
                                                                 pallet_id.end_date or '')
                                freight_order_line_id = self.freight_order_line_ids.filtered(
                                    lambda l: l.goods.id == product_id.id)
                                freight_order_line_id = freight_order_line_id and freight_order_line_id[
                                    0] or freight_order_line_id
                                custom_invoice_line.append((0, 0, {
                                    'product_id': product_id.id,
                                    'name': name,
                                    'pallet_name': pallet_id.name or '',
                                    'unit_price': round(freight_order_line_id.base_cost, 8),
                                    'uom_id': product_id.uom_id.id,
                                    'qty': pallet_qty,
                                    'is_exclude': True
                                }))
                            for storage_cost in pallet_id.storage_cost_ids:
                                today_date = current_date
                                days = today_date - pallet_id.start_date
                                if pallet_id.end_date:
                                    today_date = pallet_id.end_date
                                    days = pallet_id.end_date - pallet_id.start_date
                                days = days and days.days + 1 or 0
                                # days = days.days
                                total_cost = storage_cost.total_cost * days
                                unit_price = round(total_cost / pallet_qty, 8)
                                custom_invoice_line.append((0, 0, {
                                    'product_id': storage_cost.product_id.id,
                                    'name': storage_cost.product_id.name or 'Storage Cost',
                                    'unit_price': unit_price,
                                    'qty': pallet_qty,
                                }))
                                # pallet_id.start_date = today_date
            if custom_invoice_line:
                invoice_line.write({'order_lines': custom_invoice_line})

        return invoice_line

    def generate_wfl_level_c_invoice(self, invoice_id=False):
        invoice_end_date = self.env.context.get('end_date')
        onetime = False
        import_id = self.import_id
        if not import_id:
            raise ValidationError("Vendor is not set in this freight record!")
        custom_invoice_line = []
        pallet_total_cost = sum(self.storage_cost_ids.mapped("total_cost"))
        storage_product_id = self.storage_cost_ids and self.storage_cost_ids[0].product_id.id
        monthly_storage_id = self.env['product.product'].search([('default_code', '=', 'STG00102')], limit=1)
        pallet_ids = self.pallet_ids.filtered(lambda p: p.end_date != p.start_date)
        if not pallet_ids:
            raise ValidationError(
                "Pallets are currently not stored in the storage area!\nPlease first move it on storage area!")
        current_date = fields.date.today()
        invoice_line = False
        if invoice_id:
            invoice_line = self.env['custom.invoice'].with_context(level_invoice="Level 3 Storage Invoice").create({
                'partner_id': import_id.id,
                'invoice_type': 'wfl_storage',
                'invoice_date': invoice_end_date,
                'invoice_id': invoice_id.id,
                'transit_app_id': self.id,
                'company_id': invoice_id.company_id.id
            })
            freight_record_ids = self.purchase_orders_ids.freight_record
            pallet_ids = freight_record_ids.mapped('pallet_ids').filtered(lambda p: p.end_date != p.start_date)
            if not pallet_ids:
                raise ValidationError("Pallets are currently not stored in the storage area!")
            if invoice_line:
                for freight_record in freight_record_ids:
                    pallet_ids = freight_record.pallet_ids.filtered(lambda p: p.end_date != p.start_date)
                    if not pallet_ids:
                        continue
                    for rec in freight_record.freight_order_line_ids:
                        invoice_line.order_lines.create({
                            'invoice_id': invoice_line.id,
                            'product_id': rec.goods.id,
                            'unit_price': round(rec.base_cost, 8),
                            'qty': rec.total_quantity,
                            'is_exclude': True
                        })
                    for pallet_id in pallet_ids:
                        end_date = pallet_id.end_date
                        pallet_qty = pallet_id.product_ids and sum(pallet_id.product_ids.mapped('product_qty')) or 0
                        if pallet_qty:
                            for product_id in pallet_id.product_ids:
                                product_id = product_id.product_id
                                name = "In: {} - Out: {}".format(pallet_id.start_date + timedelta(days=1) or '',
                                                                 pallet_id.end_date or '')
                                freight_order_line_id = self.freight_order_line_ids.filtered(
                                    lambda l: l.goods.id == product_id.id)
                                freight_order_line_id = freight_order_line_id and freight_order_line_id[
                                    0] or freight_order_line_id
                                custom_invoice_line.append((0, 0, {
                                    'product_id': product_id.id,
                                    'name': name,
                                    'pallet_name': pallet_id.name or '',
                                    'unit_price': round(freight_order_line_id.base_cost, 8),
                                    'uom_id': product_id.uom_id.id,
                                    'qty': pallet_qty,
                                    'is_exclude': True
                                }))
                            for storage_cost in pallet_id.storage_cost_ids:
                                today_date = invoice_end_date
                                days = today_date - pallet_id.start_date
                                if pallet_id.end_date:
                                    today_date = pallet_id.end_date
                                    days = pallet_id.end_date - pallet_id.start_date
                                days = days and days.days + 1 or 0
                                # days = days.days
                                total_cost = storage_cost.total_cost * days
                                unit_price = round(total_cost / pallet_qty, 8)
                                custom_invoice_line.append((0, 0, {
                                    'product_id': storage_cost.product_id.id,
                                    'name': storage_cost.product_id.name or 'Storage Cost',
                                    'unit_price': unit_price,
                                    'qty': pallet_qty,
                                }))
                                pallet_id.start_date = today_date
                                unit_price = days and round(total_cost / days, 8) or 0
                                custom_invoice_line.append((0, 0, {
                                    'product_id': monthly_storage_id.id,
                                    'name': monthly_storage_id.name,
                                    'unit_price': unit_price,
                                    'uom_id': '',
                                    'qty': days,
                                    'is_exclude': True
                                }))
            if custom_invoice_line:
                invoice_line.write({'order_lines': custom_invoice_line})

        return invoice_line

    def create_po_lines(self):
        for order in self.purchase_orders_ids:
            if order:
                for rec in order.order_line:
                    product = rec.product_id
                    freight_line = self.freight_order_line_ids.create({
                        'goods': product.id,
                        'freight_id': self.id,
                        'value': rec.price_unit,
                        'total_pallet': product.product_per_pallet,
                        'total_quantity': rec.product_qty,
                        'sale_price': product.lst_price,
                    })
                    freight_line.base_cost = rec.price_unit

                for lines in self.freight_order_line_ids:
                    lines.set_gross_weight()
                    lines.total_value()
                    lines.onchange_required_pallet()

    def create_so_lines(self, order_id=None):
        if not order_id:
            return False
        purchase_order_id = order_id.edi_po_number
        for rec in order_id.order_line.filtered(lambda l: l.product_id.detailed_type != 'service'):
            product = rec.product_id
            pack_size = rec.edi_pack_size or 1
            freight_line = self.freight_order_line_ids.create({
                'goods': product.id,
                'freight_id': self.id,
                'value': rec.price_unit,
                'total_pallet': product.product_per_pallet,
                'total_quantity': rec.product_uom_qty * pack_size,
                'qty_carton': rec.product_uom_qty,
                'sale_price': product.lst_price,
                'po_number': purchase_order_id
            })
            freight_line.base_cost = rec.price_unit

        for lines in self.freight_order_line_ids:
            lines.set_gross_weight()
            lines.total_value()
            lines.onchange_required_pallet()

    def _generate_logistic_storage_invoice(self):
        today_date = fields.date.today()
        today_day = monthrange(fields.date.today().year, fields.date.today().month)[1]
        if today_date.day != today_day:
            return False
        freight_ids = self.search([])
        purchase_ids = freight_ids.mapped('purchase_orders_ids')
        for rec in purchase_ids:
            try:
                rec.freight_record[0].with_context(end_date=today_date).generate_wfl_level_a_invoice()
            except Exception as e:
                _logger.error("Unable to generate storage invoice: {}".format(e))
        return True

    def transfer_inventory_with_pallets_wizard(self):
        """
        Return the inventory transfer wizard
        :return:
        """
        action = self.env["ir.actions.actions"]._for_xml_id("warefor_3pl_tus.action_inventory_transfer_wizard")
        action['context'] = {'default_freight_id': self.id}
        return action

    def transfer_inventory_outbound_wizard(self):
        """
        Return the inventory transfer outbound wizard
        :return:
        """
        action = self.env["ir.actions.actions"]._for_xml_id("warefor_3pl_tus.action_inventory_transfer_outbound_wizard")
        action['context'] = {'default_freight_id': self.id}
        return action

    def transfer_inventory_with_pallets(self, destination_location_id=False):
        if not destination_location_id:
            raise ValidationError("Please select the location for transfer the inventory!")
        # location_id = destination_location_id.search([('is_inventory_adjustment_location', '=', True),
        #                                               ('company_id', '=', destination_location_id.company_id.id),
        #                                               ], limit=1)
        if not self.freight_order_line_ids:
            raise ValidationError("Products lines not found in Project Logistic record!")
        picking_type = self.env['stock.picking.type'].search(
            [
                ('is_inventory_adjustment', '=', True),
                ('warehouse_id', '=', self.warehouse_id.id),
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
            'freight_record_id': self.id,
            'origin': self.name,
        })
        for freight_order_line in self.freight_order_line_ids:
            move_id = self.env['stock.move'].create({
                'name': freight_order_line.goods.name,
                'location_id': picking_id.location_id.id,
                'location_dest_id': picking_id.location_dest_id.id,
                'picking_id': picking_id.id,
                'product_id': freight_order_line.goods.id,
                'product_uom': freight_order_line.goods.uom_id.id,
                'quantity_done': freight_order_line.total_quantity,
                'product_uom_qty': freight_order_line.total_quantity,
                'company_id': picking_id.company_id.id,
                'no_of_pallets': freight_order_line.required_pallet
            })
            picking_id.location_dest_id.outbound_stored_pallet = picking_id.location_dest_id.outbound_stored_pallet + freight_order_line.required_pallet
            if freight_order_line.lot_id:
                move_id.move_line_ids.lot_id = freight_order_line.lot_id.id
        picking_id.write({'partner_id': False})
        move_ids_without_package = picking_id.move_ids_without_package
        for move_id in move_ids_without_package:
            move_id.picking_type_id = picking_id.picking_type_id.id
        self.picking_ids = [(4, picking_id.id)]
        self.transferred_date = fields.Date.today()
        # stage_id = self.env.ref('mc_freight_app.inventory_received_at_brw', False)
        # if stage_id:
        #     self.write({'stage_id': stage_id.id})
        # self.create_receipt_pallets_for_transfer_inventory()
        # self.pallet_ids.write({
        #     'start_date': fields.Date.today(),
        #     'billing_from': fields.Date.today(),
        #     'is_enabled': True,
        #     'state': 'in_progress',
        #     'location_id': destination_location_id.id,
        #     'current_location_id': destination_location_id.id
        # })

    def transfer_inventory_outbound(self, destination_location_id=False):
        if not destination_location_id:
            raise ValidationError("Please select the location for transfer the inventory!")
        # destination_location_id = location_id.search([('is_outbound_location', '=', True),
        #                                               ('company_id', '=', False)], limit=1)
        # if not destination_location_id:
        #     raise ValidationError("Destination location is not configured!")

        if not self.freight_order_line_ids:
            raise ValidationError("Products lines not found in Project Logistic record!")
        data = {}
        freight_order_line_ids = self.freight_order_line_ids
        stock_quant = self.env['stock.quant']
        company_ids = self.env["res.company"].search([('is_logistics', '=', True)])
        for freight_order_line_id in freight_order_line_ids:
            left_quantity = freight_order_line_id.total_quantity
            added_qty = 0
            quant_ids = stock_quant.search(
                [('product_id', '=', freight_order_line_id.goods.id), ('company_id', 'in', company_ids.ids),
                 ('location_id.usage', '=', 'internal')], order='lot_id')
            for quant_id in quant_ids:
                if left_quantity <= 0:
                    break
                added_qty = min(left_quantity, quant_id.quantity)
                left_quantity = left_quantity - quant_id.quantity
                location_id = quant_id.location_id
                picking_type = self.env['stock.picking.type'].search(
                    [
                        ('code', '=', 'outgoing'),
                        ('warehouse_id', '=', self.warehouse_id.id),
                        ('warehouse_id.company_id', '=', quant_id.location_id.company_id.id)
                    ],
                    limit=1)
                if picking_type:
                    picking_id = self.env['stock.picking'].create({
                        'location_id': location_id.id,
                        'location_dest_id': destination_location_id.id,
                        'move_type': 'direct',
                        'immediate_transfer': True,
                        'picking_type_id': picking_type.id,
                        'is_locked': True,
                        'company_id': location_id.company_id.id,
                        'freight_record_id': self.id,
                        'partner_id': self.outbound_partner_id.id
                    })
                    move_id = self.env['stock.move'].create({
                        'name': freight_order_line_id.goods.name,
                        'location_id': picking_id.location_id.id,
                        'location_dest_id': picking_id.location_dest_id.id,
                        'picking_id': picking_id.id,
                        'product_id': freight_order_line_id.goods.id,
                        'product_uom': freight_order_line_id.goods.uom_id.id,
                        'quantity_done': added_qty,
                        'product_uom_qty': added_qty,
                        'company_id': picking_id.company_id.id
                    })
                    move_id.move_line_ids.lot_id = quant_id.lot_id.id
                    move_ids_without_package = picking_id.move_ids_without_package
                    for move_id in move_ids_without_package:
                        move_id.picking_type_id = picking_id.picking_type_id.id
                    self.write({'picking_ids': [(4, picking_id.id)], 'transferred_date': fields.Date.today()})
                else:
                    raise ValidationError('Unable to found the internal transfer in company of destination location')

    def open_wizard_for_storage_invoice(self):
        if self.is_outbound:
            partner_id = self.partner_id and self.partner_id[0].id
            partner_shipping_id = self.outbound_partner_id.id

        else:
            partner_id = self.partner_id and self.partner_id.id or False
            partner_shipping_id = self.warehouse_id and self.warehouse_id.partner_id and self.warehouse_id.partner_id.id or partner_id

        if not partner_id:
            raise ValidationError("Please add the customer/vendor for invoice!")

        default_journal = self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', self.env.company.id)], limit=1)
        total_storage_cost = sum(self.storage_cost_ids.mapped("total_cost"))

        invoice_line_ids = []
        invoice_date = fields.Date.today()
        if self.is_outbound:
            invoice_date = self.loading_end_date_local
        else:
            invoice_date = self.unload_end_date_local

        # invoice = self.env['account.move']
        invoice = self.env['account.move'].create({
            'partner_id': partner_id,
            'partner_shipping_id': partner_shipping_id,
            'invoice_date': invoice_date,
            'move_type': 'out_invoice',
            'journal_id': default_journal.id,
            'freight_id': self.id,
        })

        invoice._onchange_partner_id()
        invoice.partner_shipping_id = partner_shipping_id
        for import_cost_id in self.import_cost_ids:
            total_cost = import_cost_id.total_cost
            invoice_line_ids.append((0, 0, {
                'name': import_cost_id.name or import_cost_id.product_id.name or '',
                'product_id': import_cost_id.product_id.id,
                'price_unit': total_cost,
                'quantity': 1,
                'month_qty': 1,
                'discount': 0.0,
                'product_uom_id': import_cost_id.product_id.uom_id.id,
            }))

        for fob_cost_id in self.fob_cost_ids:
            total_cost = fob_cost_id.total_cost
            invoice_line_ids.append((0, 0, {
                'name': fob_cost_id.display_name or fob_cost_id.product_id.name or '',
                'product_id': fob_cost_id.product_id.id,
                'price_unit': total_cost,
                'quantity': 1,
                'month_qty': 1,
                'discount': 0.0,
                'product_uom_id': fob_cost_id.product_id.uom_id.id,
            }))

        vas_lines = {}
        for vas_cost_id in self.vas_cost_ids:
            total_cost = vas_cost_id.total_cost
            vas_name = vas_cost_id.product_id
            if vas_cost_id.unit_of_measure:
                value = dict(vas_cost_id._fields['unit_of_measure']._description_selection(vas_cost_id.env)).get(
                    vas_cost_id.unit_of_measure)
            else:
                value = ""
            if vas_name in vas_lines.keys():
                vas_lines[vas_name] = {
                    'name': vas_name.name or '',
                    'product_id': vas_cost_id.product_id.id,
                    'price_unit': vas_cost_id.unit_price or total_cost,
                    'quantity': vas_lines[vas_name]['quantity'] + vas_cost_id.total_unit or 1,
                    'month_qty': 1,
                    'discount': 0.0,
                    'cost_uom': value,
                    'product_uom_id': vas_cost_id.product_id.uom_id.id,
                }
            else:
                vas_lines[vas_name] = {
                    'name': vas_name.name or '',
                    'product_id': vas_cost_id.product_id.id,
                    'price_unit': vas_cost_id.unit_price or total_cost,
                    'quantity': vas_cost_id.total_unit or 1,
                    'month_qty': 1,
                    'discount': 0.0,
                    'cost_uom': value,
                    'product_uom_id': vas_cost_id.product_id.uom_id.id,
                }
        for vas_cost_id in vas_lines.values():
            invoice_line_ids.append((0, 0, vas_cost_id))

        if self.transferred_date:
            days = fields.Date.today() - self.transferred_date
            total_days = (days and days.days + 1 or 0)
        else:
            total_days = 1

        for storage_cost_id in self.storage_cost_ids:
            total_cost = storage_cost_id.total_cost
            invoice_line_ids.append((0, 0, {
                'name': storage_cost_id.name or storage_cost_id.product_id.name or '',
                'product_id': storage_cost_id.product_id.id,
                'price_unit': total_cost,
                'quantity': total_days,
                'month_qty': 1,
                'discount': 0.0,
                'product_uom_id': storage_cost_id.product_id.uom_id.id,
            }))

        invoice.write({'invoice_line_ids': invoice_line_ids})
        self.account_move_ids = [(4, invoice.id)]

        # if self.is_outbound:
        #     self.outbound_stage_id = self.env.ref('mc_freight_app.complete_outbound').id
        # else:
        #     self.stage_id = self.env.ref('mc_freight_app.closed').id
        # return True

    def create_receipt_pallets_for_transfer_inventory(self):
        """
        Create the Pallet as per the configuration and incoming shipment products with qty
        :return: True
        """
        _logger.info("********** Method: create_receipt_pallets_for_transfer_inventory**************")
        product_development = self.env['product.development']
        pickings_len = 0
        for freight in self:
            pallet_prefix = freight.name[-3:]
            partner_id = freight.import_id and freight.import_id
            freight = freight.with_context(transit_app=freight)
            picking_ids = freight.picking_ids
            for picking in picking_ids:
                _logger.info("********** Processing total pickings: {} **************".format(picking.ids))
                pickings_len += 1
                _logger.info("********** Processing picking: {} **************".format(picking.ids))
                pallet_item = 0
                pallet_number = 0
                for move_line in picking.move_ids:
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
                            lambda l: l.package_id.id == packaging_id)
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
                            name = "{}/{}/0{}-{}".format(partner_id.vendor_identifier or "", pallet_prefix,
                                                         pickings_len, pallet_number)
                            picking = picking.with_context(is_split=False)
                            picking.create_shipment_pallet(name, move_line.product_id, product_uom_qty,
                                                           pallet_cost_id)
                        else:
                            other_qty = product_uom_qty % packaging_qty if product_uom_qty > packaging_qty else 0
                            total_pallet = int(product_uom_qty / packaging_qty)
                            if other_qty:
                                total_pallet += 1
                            picking = picking.with_context(is_split=total_pallet)
                            for pallet_seq in range(0, total_pallet):
                                pallet_number += 1
                                name = "{}/{}/0{}-{}".format(partner_id.vendor_identifier or "", pallet_prefix,
                                                             pickings_len, pallet_number)
                                _logger.info(
                                    "********** Creating Pallet: {} **************".format(name))
                                if pallet_number == 1 and other_qty:
                                    picking.create_shipment_pallet(name, move_line.product_id, other_qty,
                                                                   pallet_cost_id)
                                else:
                                    picking.create_shipment_pallet(name, move_line.product_id, packaging_qty,
                                                                   pallet_cost_id)
            if freight:
                freight.total_pallet = len(freight.pallet_ids)
        return True

    def button_freight_transfers(self):
        picking_ids = self.picking_ids.ids
        return {
            'name': _('Transfers'),
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', picking_ids)],
        }

    # =============================================================================================================

    def _action_launch_stock_rule(self):
        """
        Launch procurement group run method with required/custom fields generated by a
        freight order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the freight order line product rule.
        """
        if self._context.get("skip_procurement"):
            return True
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        procurements = []

        partner_id = self.partner_id
        if self.is_outbound:
            partner_id = self.outbound_partner_id or partner_id

        group_data = {
            'name': self.name,
            'move_type': 'direct',
            'partner_id': partner_id.id,
        }
        group_id = self.env['procurement.group'].create(group_data)

        for line in self.freight_order_line_ids:
            if line.goods.type not in ('consu', 'product'):
                continue
            qty = line.total_quantity
            if qty == 0:
                continue

            if self.fulfillment_method == 'bulk_orders':
                route_id = self.warehouse_id.bulk_route_id
            else:
                route_id = self.warehouse_id.ecommerce_route_id

            if not route_id:
                raise UserError("Unable to found route, please contact the administrator!" + self.warehouse_id)

            values = {
                'group_id': group_id,
                'route_ids': route_id,
                'partner_id': partner_id.id,
                'company_id': self.env.company,
                'freight_id': self.id,
                'move_type': 'direct'
            }

            procurements.append(self.env['procurement.group'].Procurement(
                line.goods, qty, line.goods.uom_id,
                partner_id.property_stock_customer,
                line.goods.display_name, self.name, self.env.company, values))
        if procurements:
            procurement_group = self.env['procurement.group']
            if self.env.context.get('import_file'):
                procurement_group = procurement_group.with_context(import_file=False)
            data = procurement_group.with_context(is_freight_process=True).run(procurements)

        return True

    # =============================================================================================================

    def do_3_step_process(self):
        """
            Create transfers based on the freight order lines based on the configured route.
        """
        if not self._context.get('skip_access_process') and not self.env.user.has_group('mc_freight_app.group_freight_administrator'):
            return True
        sale_obj = self.env['sale.order'].sudo()
        for rec in self:
            if rec.picking_ids and self._context.get('skip_access_process'):
                continue
            if not self._context.get('skip_access_process') and rec.picking_ids and rec.picking_ids.filtered(lambda x: x.state in ['draft', 'confirmed', 'assigned']):
                raise ValidationError("Please validate first remaining transfers!")
            try:
                _logger.info("*********Creating Transfers********** {}".format(rec.id))
                is_available_stock = rec.check_stock_availalibility()
                if not is_available_stock:
                    _logger.info("*********Stock is not available********** {}".format(rec.id))
                    if not self._context.get('skip_access_process'):
                        raise UserError("Stock is not available for added products!")
                    continue
                rec.sudo()._action_launch_stock_rule()
                sale_id = sale_obj.search([('freight_id', '=', rec.id)])
                if sale_id:
                    for pick in sale_id.sudo().picking_ids:
                        picking_ids = []
                        if pick.picking_type_code == 'internal':
                            picking_ids = rec.picking_ids.filtered(
                                lambda p: 'PICK' in p.name and 'PICK' in pick.name)
                            if not picking_ids:
                                picking_ids = rec.picking_ids.filtered(
                                    lambda p: 'PACK' in p.name and 'PACK' in pick.name)
                        elif pick.picking_type_code == 'outgoing':
                            picking_ids = rec.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing')
                        if picking_ids:
                            picking_ids = picking_ids[0]
                            pick.freight_picking_id = picking_ids.id
                            picking_ids.freight_picking_id = pick.id
                _logger.info("*********Transfers Created********** {}".format(rec.id))
            except Exception as e:
                raise UserError("Unable to create transfer, please contact the administrator! \n{}".format(e))
        return {
            'type': 'ir.actions.client',
            'tag': 'soft_reload',
            'params': {
                'title': _('Success'),
                'message': 'Transfers created successfully...',
                'type': 'success',
            }
        }

    def check_stock_availalibility(self):
        stock_quant = self.env['stock.quant']
        company_ids = self.env["res.company"].search([('is_logistics', '=', True)])
        for rec in self:
            for line in rec.freight_order_line_ids:
                qty_available = line.goods.qty_available
                quant_ids = stock_quant.search(
                    [('product_id', '=', line.goods.id),
                     ('lot_id', '=', line.lot_id.id),
                     ('company_id', 'in', company_ids.ids),
                     ('location_id.is_omit_on_source_location', '=', True),
                     ('location_id.usage', '=', 'internal')])
                another_warehouse_quant_ids = stock_quant.search(
                    [('product_id', '=', line.goods.id),
                     ('lot_id', '=', line.lot_id.id),
                     ('company_id', 'in', company_ids.ids),
                     ('location_id.warehouse_id', '!=', rec.warehouse_id.id),
                     ('location_id.is_omit_on_source_location', '=', False),
                     ('location_id.usage', '=', 'internal')])
                total_quants = quant_ids + another_warehouse_quant_ids
                qty_available = qty_available - sum(total_quants.mapped('quantity'))
                if qty_available < line.total_quantity:
                    return False
        return True

    def button_freight_osd_transfers(self):
        picking_ids = self.osd_picking_ids.ids
        return {
            'name': _('Transfers'),
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', picking_ids)],
        }

    def action_inbound_osd_report(self):
        """
        :return:
        """
        inbound_logistic_ids = self

        dict_data = []
        header_name = ""

        if not inbound_logistic_ids:
            raise ValidationError("No record found to generate the report!")

        try:
            ###########################################
            header_columns = ["Container #", "PO #", "SKU #", "Description", "Tenders \nScheduled \nfor KATY DC",
                              "Container \nRecived @ \n KATY DC", "Unloaded Date", "Receiving LOS",
                              "EMPTY \nPick Up Date",
                              "Number \n Of Cartons\n Received", "Selling Unit \n Per Cartons",
                              "Number of \n Selling Units \nReceived",
                              "OS&D"]
            # header_columns = [ "Reference #","Ship From","Transport" , "Item #", "Lot #", "BL",
            #                   "Description", "Quantity", "Total \nPallets", "Units \nPer Pallet",
            #                   "Total \nWeight", "Weight \nPallet", "Received \nDate", "WH \nLocation", "REMARKS:"]
            header_name = 'INBOUND RELEASE ORDERS LOG'
            if self[0].is_outbound:
                header_name = 'OUTBOUND RELEASE ORDERS LOG'

            # if self.customer_id.name:
            #     header_name = "{} RELEASE ORDERS LOG".format(self.customer_id.name).upper()

            xlsx_file = "Inbound_osd_Report_{}.xlsx".format(fields.Date.today())
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            v_common_bg_style = workbook.add_format(
                {'bold': True, 'align': 'vcenter', 'valign': 'center', 'border': 0, 'center_across': 'center',
                 'font_size': 24})
            left_common_bg_style = workbook.add_format(
                {'bold': False, 'valign': 'vcenter', 'align': 'center', 'border': 0})
            left_common_style_number = workbook.add_format(
                {'bold': False, 'align': 'left', 'border': 0})
            date_common_bg_style = workbook.add_format(
                {'bold': True, 'valign': 'vcenter', 'align': 'center', 'border': 0, 'color': '#0d00ff'})

            header_common_bg_style = workbook.add_format(
                {'valign': 'vcenter', 'align': 'center', 'border': 1, 'bg_color': '#b8b8b8', 'font_size': 10,
                 'text_wrap': True})
            data_style_1 = workbook.add_format(
                {'valign': 'vcenter', 'align': 'center', 'border': 1, 'font_size': 10})
            data_style_2 = workbook.add_format(
                {'valign': 'vcenter', 'align': 'left', 'border': 1, 'font_size': 10, 'indent': 1})
            sheet = workbook.add_worksheet("Sheet1")
            sheet.set_column(0, 0, 12)
            sheet.set_column(1, 1, 12)
            sheet.set_column(2, 2, 12)
            sheet.set_column(3, 3, 30)
            sheet.set_column(4, 4, 12)
            sheet.set_column(5, 5, 12)
            sheet.set_column(6, 6, 12)
            sheet.set_column(7, 7, 12)
            sheet.set_column(8, 8, 12)
            sheet.set_column(9, 9, 12)
            sheet.set_column(10, 10, 12)
            sheet.set_column(11, 11, 12)
            sheet.set_column(12, 12, 12)
            # sheet.set_column(13, 13, 18)
            # sheet.set_column(14, 14, 25)
            # logo = base64.b64decode(self.env.company.logo)
            # logo = BytesIO(logo)

            # company_logo = Image.open(logo).resize((220, 60), Image.ANTIALIAS)
            # company_logo.save('/tmp/company_logo.png')

            # sheet.insert_image('A1:A2', '/tmp/company_logo.png')

            col = 0
            row = 0
            sheet.set_row(row, 50)
            sheet.merge_range(row, col, row, col + 12, header_name, v_common_bg_style)
            row += 1
            col = 0
            sheet.write(row, col, 'Date', left_common_bg_style)
            col += 1
            sheet.write(row, col + 1, "{} {} {}".format(
                datetime.today().day, calendar.month_name[datetime.today().month], datetime.today().year),
                        date_common_bg_style)
            col += 2
            sheet.write(row, col, '', left_common_bg_style)
            col += 1
            sheet.write(row, col, 'Time', left_common_bg_style)
            col += 1
            user_tz = self.env.user.tz
            if user_tz:
                local = pytz.timezone(user_tz)
                header_date = datetime.strftime(pytz.utc.localize(datetime.today()).astimezone(local), '%I:%M %p')
            sheet.write(row, col + 1, str(header_date), date_common_bg_style)

            # for temp in range(9):
            #     col += 1
            #     sheet.write(row, col, '', date_common_bg_style)
            #
            row += 1
            col = 0
            # ##################### Header ######################
            # sheet.set_row(row, 50)
            for header in header_columns:
                sheet.set_row(row, 60)
                sheet.write(row, col, header, header_common_bg_style)
                col += 1
            row += 1

            ###########################################
            for ibl_id in inbound_logistic_ids:
                osd_ids = ibl_id.osd_ids
                for osd_line in osd_ids:
                    data = {
                        "Container #": ibl_id.vessel or "N/A",
                        "PO #": ibl_id.customer_po or "N/A",
                        "SKU #": osd_line.sku_id.default_code or "N/A",
                        "Description": osd_line.sku_id.name or "N/A",
                        "Tenders Scheduled for KATY DC": "N/A",
                        "Container Received @ KATY DC": ibl_id.check_in_truck_yard and ibl_id.check_in_truck_yard.strftime(
                            '%m/%d/%Y') or "N/A",
                        "Unloaded Date": ibl_id.unload_start_date and ibl_id.unload_start_date.strftime(
                            '%m/%d/%Y') or "N/A",
                        "Receiving LOS": "N/A",
                        "EMPTY Pick Up Date": ibl_id.unload_end_date and ibl_id.unload_end_date.strftime(
                            '%m/%d/%Y') or "N/A",
                        "Number of Cartons Received": "N/A",
                        "Selling Units Per Carton": "N/A",
                        "Number of Selling Units Received": "N/A",
                        "OS&D": "N/A",
                    }
                    data = data.values()
                    col = 0
                    size = 12
                    for val in data:
                        sheet.write(row, col, val, data_style_2)
                        col += 1
                    row += 1
            ###########################################

            workbook.close()
            output.seek(0)

            output = base64.encodestring(output.read())
            ##########################################

            new_attach = {
                'name': xlsx_file,
                'type': "binary",
                'mimetype': 'application/zip',
                'datas': output,
            }
            attachment_id = self.env["ir.attachment"].create(new_attach)
            download_url = '/web/content/?model=ir.attachment&id={}&filename_field=name&field=datas&download=true&name={}'.format(
                attachment_id.id, attachment_id.name)
            action = {
                'type': 'ir.actions.act_url',
                'url': download_url,
                'target': 'new',
            }
            return action

        except Exception as e:
            _logger.error(
                "Warning : Unable to generate report. Please contact your administrator. **** {}".format(e))
            raise ValidationError("Warning : Unable to generate report. Please contact your administrator.")

    @api.onchange('freight_order_line_ids', 'partner_id', 'warehouse_id', 'check_in_truck_yard')
    def generate_pallet_config_ids(self):
        if not self._context.get('import_file'):
            self.vas_cost_ids = False
        is_outbound = self.is_outbound
        if is_outbound:
            self.create_vas_cost_lines()
        else:
            order_line_ids = self.freight_order_line_ids.filtered(lambda x: x.goods and x.required_pallet != 0)
            domain = [('warehouse_id', '=', self.warehouse_id.id), ('partner_id', '=', self.partner_id.id)]
            if self.check_in_truck_yard:
                if self.check_in_truck_yard.date().day <= 15:
                    domain += ['|', ('received_date', '=', 'day_1_to_15'), ('is_storage_fee', '=', False)]
                else:
                    domain += ['|', ('received_date', '=', 'day_16_to_31'), ('is_storage_fee', '=', False)]
            domain.append(('received_date', '=', False))
            if order_line_ids and self.partner_id and self.warehouse_id:
                pallet_config_ids = self.env['pallet.config.ibl'].search(domain)
                vals = []
                if pallet_config_ids:
                    for order_line in order_line_ids:
                        product_domain = [('id', 'in', pallet_config_ids.ids), ('product_ids', '=', order_line.goods.id)]
                        pallet_config_products = pallet_config_ids.search(product_domain)
                        if pallet_config_products:
                            for pallet in pallet_config_products:
                                total_unit = math.ceil(order_line.required_pallet)
                                if pallet.service_uom.name == "Load":
                                    total_unit = 1.0
                                if pallet.service_uom.name in ['ft³', 'CuFt']:
                                    amount = order_line._compute_product_volume()
                                    if not amount:
                                        amount = 0
                                    total_unit = math.ceil(amount)
                                if pallet.service_uom.name == 'Carton':
                                    amount = order_line._compute_qty_carton()
                                    if not amount:
                                        amount = 0
                                    total_unit = math.ceil(amount)

                                vals.append({
                                    'product_id': pallet.service_fee.id,
                                    'total_unit': total_unit,
                                    'product_uom': pallet.service_uom.id,
                                    'unit_price': pallet.cost,
                                    'transit_app_id': self.id,
                                })
                        else:
                            pallet_config = pallet_config_ids.filtered(lambda x: not x.product_ids)
                            for pallet in pallet_config:
                                total_unit = math.ceil(order_line.required_pallet)
                                if pallet.service_uom.name == "Load":
                                    total_unit = 1.0
                                if pallet.service_uom.name in ['ft³', 'Cu Ft (ft³)']:
                                    order_line._compute_product_volume()
                                    amount = order_line.product_volume
                                    if not amount:
                                        amount = 0
                                    total_unit = amount
                                if pallet.service_uom.name == 'Carton':
                                    amount = order_line._compute_qty_carton()
                                    if not amount:
                                        amount = 0
                                    total_unit = math.ceil(amount)
                                vals.append({
                                    'product_id': pallet.service_fee.id,
                                    'total_unit': total_unit,
                                    'product_uom': pallet.service_uom.id,
                                    'unit_price': pallet.cost,
                                    'transit_app_id': self.id,
                                })
                    if vals:
                        self.env['pallet.vas.cost'].create(vals)

    def unlink(self):
        # if not self._context.get('deletion_approved'):
        #     action = self.env["ir.actions.actions"]._for_xml_id("warefor_3pl_tus.act_custom_invoice_wizard_1")
        #     return action
        #     # raise UserError("Sorry, You can't delete this Record.")
        # else:
        if self.env.user.has_group('warefor_3pl_tus.group_ibl_obl_delete_access') or self.env.user.has_group(
                'warefor_3pl_tus.group_ibl_obl_multi_record_delete_access'):
            return super(FreightFreight, self).unlink()
        else:
            raise UserError("Sorry, You can't delete this Record.")

    def create_vas_cost_lines(self):
        self.vas_cost_ids = False
        pallet_config_obl = self.env['pallet.config.obl']
        pallet_vas_cost = self.env['pallet.vas.cost']
        for rec in self:
            carton_data = {}
            volume_data = {}
            weight_data = {}
            pallet_data = {}
            load_data = {}
            # sale_id = self.env['sale.order'].sudo().search([('name', '=', rec.reference)], limit=1)
            for line in rec.freight_order_line_ids.filtered(lambda f: f.goods.detailed_type != 'service'):
                # cb_fr_cost = pallet_config_obl.search([('warehouse_id', '=', rec.warehouse_id.id), ('is_cbft', '=', True)], limit=1)
                # if cb_fr_cost:
                #     pallet_vas_cost.create({
                #         'product_id': cb_fr_cost.service_fee.id,
                #         'total_unit': line.volume_by_ft,
                #         'product_uom': cb_fr_cost.service_uom.id,
                #         'unit_price': cb_fr_cost.cost,
                #         'transit_app_id': rec.id,
                #     })
                # if sale_id.edi_po_number:
                #     is_edi = pallet_config_obl.search(
                #         [('warehouse_id', '=', rec.warehouse_id.id), ('partner_id', '=', rec.partner_id.id),
                #          ('edi_store_id', '=', rec.edi_store_id.id)], limit=1)
                #     if is_edi:
                #         edi_vas_data = {
                #             'product_id': is_edi.service_fee.id,
                #             'total_unit': edi_vas_data.get('total_unit', 0) + line.required_pallet,
                #             'product_uom': is_edi.service_uom.id,
                #             'unit_price': is_edi.cost,
                #             'transit_app_id': rec.id,
                #         }
                #         continue
                is_carton = pallet_config_obl.search([('warehouse_id', '=', rec.warehouse_id.id),
                                                      ('partner_id', '=', rec.partner_id.id),
                                                      ('is_carton', '=', True)], limit=1)
                if is_carton:
                    carton_data = {
                        'product_id': is_carton.service_fee.id,
                        'total_unit': carton_data.get('total_unit', 0) + line.qty_carton,
                        'product_uom': is_carton.service_uom.id,
                        'unit_price': is_carton.cost,
                        'transit_app_id': rec.id,
                    }

                is_volume = pallet_config_obl.search(
                    [('warehouse_id', '=', rec.warehouse_id.id), ('partner_id', '=', rec.partner_id.id),
                    ('is_volume', '=', True)], limit=1)
                if is_volume:
                    volume_data = {
                        'product_id': is_volume.service_fee.id,
                        'total_unit': volume_data.get('total_unit', 0) + line.product_volume,
                        'product_uom': is_volume.service_uom.id,
                        'unit_price': is_volume.cost,
                        'transit_app_id': rec.id,
                    }

                is_weight = pallet_config_obl.search(
                    [('warehouse_id', '=', rec.warehouse_id.id), ('partner_id', '=', rec.partner_id.id),
                    ('is_weight', '=', True)], limit=1)
                if is_weight:
                    weight_data = {
                        'product_id': is_weight.service_fee.id,
                        'total_unit': weight_data.get('total_unit', 0) + line.net_weight,
                        'product_uom': is_weight.service_uom.id,
                        'unit_price': is_weight.cost,
                        'transit_app_id': rec.id,
                    }

                is_pallet = pallet_config_obl.search(
                    [('warehouse_id', '=', rec.warehouse_id.id), ('partner_id', '=', rec.partner_id.id),
                    ('is_pallet', '=', True)], limit=1)
                if is_pallet:
                    pallet_data = {
                        'product_id': is_pallet.service_fee.id,
                        'total_unit': pallet_data.get('total_unit', 0) + line.required_pallet,
                        'product_uom': is_pallet.service_uom.id,
                        'unit_price': is_pallet.cost,
                        'transit_app_id': rec.id,
                    }

                is_load = pallet_config_obl.search(
                    [('warehouse_id', '=', rec.warehouse_id.id), ('partner_id', '=', rec.partner_id.id),
                    ('is_load', '=', True)], limit=1)
                if is_load:
                    load_data = {
                        'product_id': is_load.service_fee.id,
                        'total_unit': load_data.get('total_unit', 0) + 1,
                        'product_uom': is_load.service_uom.id,
                        'unit_price': is_load.cost,
                        'transit_app_id': rec.id,
                    }

            if carton_data:
                pallet_vas_cost.create(carton_data)
            if volume_data:
                pallet_vas_cost.create(volume_data)
            if weight_data:
                pallet_vas_cost.create(weight_data)
            if pallet_data:
                pallet_vas_cost.create(pallet_data)
            if load_data:
                pallet_vas_cost.create(load_data)

    def action_generate_multi_record_invoice(self):
        """
        Generate a single invoice for multi-records.
        """
        if not self:
            raise ValidationError("Please select at-least one record!")

        record = self[0]

        inbound_record = self.filtered(lambda s: not s.is_outbound)
        if inbound_record:
            raise UserError("Please select only Outbound records!")

        partner_id = record.partner_id.id
        partner_shipping_id = record.outbound_partner_id.id

        if not partner_id:
            raise ValidationError("Please add the customer/vendor for invoice!")

        default_journal = self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', self.env.company.id)], limit=1)
        total_storage_cost = sum(self.mapped("storage_cost_ids.total_cost"))

        invoice_line_ids = []
        invoice_date = fields.Date.today()

        invoice_date = record.loading_end_date_local

        invoice = self.env['account.move'].create({
            'partner_id': partner_id,
            'partner_shipping_id': partner_shipping_id,
            'invoice_date': invoice_date,
            'move_type': 'out_invoice',
            'journal_id': default_journal.id,
            'is_merged_invoice': True,
            'freight_id': record.id,
        })

        invoice._onchange_partner_id()
        invoice.partner_shipping_id = partner_shipping_id

        invoice_lines = []

        for import_cost_id in self.import_cost_ids:
            total_cost = import_cost_id.total_cost
            product_line = list(filter(
                lambda line: line['product_id'] == import_cost_id.product_id.id and line[
                    'price_unit'] == total_cost, invoice_lines)) or []
            if product_line:
                product_line.update({'quantity': product_line.get('quantity') + 1})
            else:
                invoice_lines.append({
                    'name': import_cost_id.name or import_cost_id.product_id.name or '',
                    'product_id': import_cost_id.product_id.id,
                    'freight_uom_id': import_cost_id.product_id.uom_id.id,
                    'price_unit': total_cost,
                    'quantity': 1,
                    'month_qty': 1,
                    'discount': 0.0,
                    'product_uom_id': import_cost_id.product_id.uom_id.id,
                })

        for fob_cost_id in self.fob_cost_ids:
            total_cost = fob_cost_id.total_cost
            product_line = list(filter(
                lambda line: line['product_id'] == fob_cost_id.product_id.id and line['price_unit'] == total_cost,
                invoice_lines)) or []
            if product_line:
                product_line[0].update({'quantity': product_line[0].get('quantity') + 1})
            else:
                invoice_lines.append({
                    'name': fob_cost_id.display_name or fob_cost_id.product_id.name or '',
                    'product_id': fob_cost_id.product_id.id,
                    'freight_uom_id': fob_cost_id.product_id.uom_id.id,
                    'price_unit': total_cost,
                    'quantity': 1,
                    'month_qty': 1,
                    'discount': 0.0,
                    'product_uom_id': fob_cost_id.product_id.uom_id.id,
                })

        for vas_cost_id in self.vas_cost_ids:
            total_cost = vas_cost_id.unit_price or vas_cost_id.total_cost
            if vas_cost_id.unit_of_measure:
                value = dict(vas_cost_id._fields['unit_of_measure']._description_selection(vas_cost_id.env)).get(
                    vas_cost_id.unit_of_measure)
            else:
                value = ""
            freight_uom_id = vas_cost_id.product_uom.id or vas_cost_id.product_id.uom_id.id
            product_line = list(filter(
                lambda line: line['product_id'] == vas_cost_id.product_id.id and line[
                    'freight_uom_id'] == freight_uom_id and line['price_unit'] == total_cost,
                invoice_lines)) or []
            if product_line:
                product_line[0].update({'quantity': product_line[0].get('quantity') + vas_cost_id.total_unit or 1})
            else:
                invoice_lines.append({
                    'name': vas_cost_id.name or vas_cost_id.product_id.name or '',
                    'product_id': vas_cost_id.product_id.id,
                    'price_unit': total_cost,
                    'freight_uom_id': freight_uom_id,
                    'quantity': vas_cost_id.total_unit or 1,
                    'month_qty': 1,
                    'discount': 0.0,
                    'cost_uom': value,
                    'product_uom_id': vas_cost_id.product_id.uom_id.id,
                })

        total_days = 0
        for rec in self:
            if rec.transferred_date:
                days = fields.Date.today() - rec.transferred_date
                total_days += (days and days.days + 1 or 0)
            else:
                total_days += 1

        for storage_cost_id in self.storage_cost_ids:
            total_cost = storage_cost_id.total_cost
            product_line = list(filter(
                lambda line: line['product_id'] == storage_cost_id.product_id.id and line['price_unit'] == total_cost,
                invoice_lines)) or []
            if product_line:
                product_line[0].update({'quantity': product_line[0].get('quantity') + 1})
            else:
                invoice_lines.append({
                    'name': storage_cost_id.name or storage_cost_id.product_id.name or '',
                    'product_id': storage_cost_id.product_id.id,
                    'price_unit': total_cost,
                    'freight_uom_id': storage_cost_id.product_id.uom_id.id,
                    'quantity': total_days,
                    'month_qty': 1,
                    'discount': 0.0,
                    'product_uom_id': storage_cost_id.product_id.uom_id.id,
                })

        invoice_line_ids = [(0, 0, line) for line in invoice_lines]

        invoice.write({'invoice_line_ids': invoice_line_ids})
        self.write({'account_move_ids': [(4, invoice.id)]})

    def get_rate_obl(self):
        """
        Get the rate for the delivery order
        :return:
        """
        sale_id = self.env['sale.order'].sudo().search([('freight_id', '=', self.id)])

        # picking_id = self.picking_ids.filtered(
        #     lambda p: p.picking_type_code == 'outgoing' and p.state in ['confirmed', 'assigned', 'done'])
        if len(sale_id) != 1:
            raise UserError("Unable to find the related sale order of this OBL record!")
        return sale_id.sudo().with_company(sale_id.sudo().company_id).action_open_delivery_wizard()

    def generate_label_from_shipstation_obl(self):
        sale_id = self.env['sale.order'].sudo().search([('freight_id', '=', self.id)])

        # picking_id = self.picking_ids.filtered(
        #     lambda p: p.picking_type_code == 'outgoing' and p.state in ['confirmed', 'assigned', 'done'])
        if len(sale_id) != 1:
            raise UserError("Unable to find the related sale order of this OBL record!")
        pick_id = sale_id.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing')
        return pick_id.sudo().with_company(pick_id.sudo().company_id).generate_label_from_shipstation()

    def update_obl_for_missing_first_scan(self):
        filter_date = datetime.now() - timedelta(days=14)
        current_date = datetime.now() - timedelta(hours=4)
        mfc_stage_id = self.env.ref('mc_freight_app.missing_first_scan').id
        obl_ids = self.env['freight.freight'].search(
            [('create_date', '>=', filter_date), ('create_date', '<=', current_date), ('first_scann', '=', False),
             ('fulfillment_method', '=', 'e-commerce'), ('is_outbound', '=', True)])
        skip_obl_ids = obl_ids.filtered(lambda l: not l.picking_ids or l.picking_ids.filtered(
            lambda p: p.picking_type_code == 'outgoing' and p.state != 'done'))
        obl_ids = obl_ids - skip_obl_ids
        obl_ids.write({'outbound_stage_id': mfc_stage_id})
        return True


class FreightOrderLineInherit(models.Model):
    _inherit = 'freight.order.line'
    _description = 'Order line for Transit'

    total_pallet = fields.Float(string="QTY on Pallet",
                                help="This is the product quantity or a package quantity if the packaging line is "
                                     "created for this product")
    required_pallet = fields.Float(string="# of Pallets", help="Required pallet for product quantities or number "
                                                               "of package quantities.")
    lot_id = fields.Many2one(
        'stock.lot', 'Lot #',
        domain="[('product_id', '=', goods)]", check_company=True)
    warehouse_id = fields.Many2one(related="freight_id.warehouse_id")
    product_description = fields.Char(related="goods.name", string="Product", store=True)
    customer_po = fields.Char(related="freight_id.customer_po", string="PO #")
    pickup_schedule_date = fields.Datetime(related="freight_id.pickup_schedule_date",
                                           string="Pick-up Scheduled Date/Time", store=True, readonly=False)
    unload_start_date = fields.Datetime(related="freight_id.unload_start_date", string="Unload Start", store=True,
                                        readonly=False)
    unload_end_date = fields.Datetime(related="freight_id.unload_end_date", string="Unload Stop", store=True,
                                      readonly=False)

    cartons_per_container = fields.Text(related="goods.cartons_per_container", string="Cartons per Container")
    cartons_per_pallet = fields.Text(related="goods.cartons_per_pallet", string="Cartons per Pallet")
    cases_per_carton = fields.Text(related="goods.cases_per_carton", string="Cases per Carton")
    units_per_case = fields.Text(related="goods.units_per_case", string="Units per Case")
    pallet_stacking = fields.Text(related="goods.pallet_stacking", string="Pallet Stacking")
    warehouse_stacking = fields.Text(related="goods.warehouse_stacking", string="Warehouse Stacking")
    check_in_truck_yard = fields.Datetime(related="freight_id.check_in_truck_yard",
                                          string="Container / Trailer Check-In", store=True, readonly=False)
    container_check_out_date = fields.Datetime(string="Container / Trailer Check-Out",
                                               related="freight_id.check_out_truck_yard", tracking=True, store=True,
                                               readonly=False)
    loading_start_date = fields.Datetime(string="Loading Start Date/Time", related="freight_id.loading_start_date",
                                         tracking=True, store=True, readonly=False)
    loading_end_date = fields.Datetime(string="Loading End Date/Time", related="freight_id.loading_end_date",
                                       store=True, readonly=False)
    loading_time = fields.Char(string="Loading Time", related="freight_id.loading_time", tracking=True, store=True)
    receiving_level_of_service = fields.Float(related="freight_id.receiving_level_of_service", string="LOS (Days)")
    qty_received = fields.Integer(string="QTY Received", compute="_compute_received_quantity")
    qty_staged = fields.Integer(string="QTY Staged", compute="_compute_received_quantity")
    qty_shipped = fields.Integer(string="QTY Shipped", compute="_compute_received_quantity")
    freight_line_color = fields.Char(string="Color", required=False, copy=False, compute="_compute_received_quantity")
    display_qty_widget = fields.Boolean(compute='_compute_qty_to_deliver')
    storage_type_id = fields.Many2one(string="Storage Type", related="freight_id.storage_type_id",
                                      tracking=True, store=True, readonly=False)
    qty_carton = fields.Float(string="Carton QTY", compute="_compute_qty_carton", digits='Stock Weight')
    product_volume = fields.Float(string="Volume", compute="_compute_product_volume", digits='Stock Weight')
    forecasted_issue = fields.Boolean(compute='_compute_forecasted_issue')
    po_number = fields.Char("PO #", store=True)
    sub_pallet = fields.Char(string="Sub Pallet")

    def name_get(self):
        result = []
        for rec in self:
            name = super(FreightOrderLineInherit, rec).name_get()[0][1]
            if self._context.get('is_ops_model'):
                name = rec.po_number or rec.id
            result.append((rec.id, name))
        return result

    @api.model
    def create(self, vals):
        res = super(FreightOrderLineInherit, self).create(vals)
        if res and res.is_outbound:
            osd_line_obj = self.env['osd.freight.transfer.line']
            vals = {
                'sku_id': res.goods.id,
                'quantity': res.total_quantity or 1,
                'po_number': res.id,
                'freight_id': res.freight_id.id,
                'pallet_type': res.pallet_type,
                'sub_pallet': res.sub_pallet,
                'freight_order_line_id': res.id,
            }
            osd_line_obj.create(vals)
        return res

    def write(self, vals):
        res = super(FreightOrderLineInherit, self).write(vals)
        for record in self:
            osd_line_obj = self.env['osd.freight.transfer.line'].search(['|', ('po_number', '=', record.id),
                                                                         ('freight_order_line_id', '=', record.id)])
            if osd_line_obj:
                update_vals = {
                    'pallet_type': record.pallet_type,
                    'sub_pallet': record.sub_pallet,
                }
                if osd_line_obj.quantity != record.total_quantity:
                    update_vals['quantity'] = record.total_quantity
                if osd_line_obj.sku_id.id != record.goods.id:
                    update_vals['sku_id'] = record.goods.id
                osd_line_obj.write(update_vals)
        return res

    def unlink(self):
        for record in self:
            osd_line = self.env['osd.freight.transfer.line'].search(['|', ('po_number', '=', record.id),
                                                                    ('freight_order_line_id', '=', record.id)])
        if osd_line:
            osd_line.unlink()
        return super(FreightOrderLineInherit, self).unlink()

    @api.depends('total_quantity', 'goods.cases_per_carton', 'goods.units_per_case')
    def _compute_qty_carton(self):
        for rec in self:
            if rec.qty_carton:
                rec.qty_carton = rec.qty_carton
                continue
            if rec.total_quantity and rec.goods.cases_per_carton and rec.goods.units_per_case:
                rec.qty_carton = rec.total_quantity / float(rec.goods.cases_per_carton) / float(
                    rec.goods.units_per_case)
            else:
                rec.qty_carton = 0

    @api.depends('total_quantity', 'goods.volume')
    def _compute_product_volume(self):
        for rec in self:
            rec.product_volume = rec.total_quantity * rec.goods.volume

    def action_product_forecast_report(self):
        self.ensure_one()
        action = self.goods.action_product_forecast_report()
        action['context'] = {
            'active_id': self.goods.id,
            'active_model': 'product.product',
        }
        if self.warehouse_id:
            action['context']['warehouse'] = self.warehouse_id.id
        return action

    @api.depends('total_quantity')
    def _compute_forecasted_issue(self):
        for order in self:
            warehouse = order.warehouse_id
            order.forecasted_issue = False
            if order.goods:
                virtual_available = order.goods.with_context(warehouse=warehouse.id).virtual_available
                if virtual_available < order.total_quantity:
                    order.forecasted_issue = True

    def _compute_qty_to_deliver(self):
        for rec in self:
            rec.display_qty_widget = True

    @api.depends('total_quantity')
    def _compute_received_quantity(self):
        for rec in self:
            rec.qty_staged = 0
            rec.qty_shipped = 0
            rec.qty_received = 0
            rec.freight_line_color = 'false'
            if rec.freight_id.is_outbound:
                ops_line_ids = rec.freight_id.osd_transfer_ids.filtered(lambda x: x.sku_id.id == rec.goods.id)
                if ops_line_ids:
                    ops_line_ids = ops_line_ids.filtered(
                        lambda x: x.lot_id == rec.lot_id) if rec.lot_id else ops_line_ids
                    stagged_transfer_ids = ops_line_ids.mapped('pick_picking_id').filtered(
                        lambda x: x.state in ['done'])
                    ship_transfer_ids = ops_line_ids.mapped('ship_picking_id').filtered(lambda x: x.state in ['done'])
                    if stagged_transfer_ids:
                        rec.qty_staged = sum(stagged_transfer_ids.move_ids_without_package.mapped('quantity_done'))
                    if ship_transfer_ids:
                        rec.qty_shipped = sum(ship_transfer_ids.move_ids_without_package.mapped('quantity_done'))
            elif not rec.freight_id.is_outbound:
                transfer_product = rec.freight_id.picking_ids.move_ids_without_package.filtered(lambda x: x.state in [
                    'done'] and x.picking_id.picking_type_code == 'incoming' and 'Return' not in x.picking_id.origin and x.product_id.id == rec.goods.id)
                return_product = rec.freight_id.picking_ids.move_ids_without_package.filtered(lambda x: x.state in [
                    'done'] and x.picking_id.picking_type_code == 'incoming' and 'Return' in x.picking_id.origin and x.product_id.id == rec.goods.id)
                if transfer_product or return_product:
                    if rec.lot_id:
                        transfer_product = transfer_product and transfer_product.filtered(
                            lambda x: x.lot_ids == rec.lot_id) or transfer_product
                        return_product = return_product and return_product.filtered(
                            lambda x: x.lot_ids == rec.lot_id) or return_product
                    rec.qty_received = sum(transfer_product.mapped('quantity_done')) - sum(
                        return_product.mapped('quantity_done'))
                if rec.total_quantity != rec.qty_received:
                    rec.freight_line_color = 'true'

    def open_freight_record(self):
        view_id = self.env.ref('warefor_3pl_tus.freight_freights_ibl_form_view').id
        context = self._context.copy()
        return {
            'name': 'freight_freight_obl',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_model': 'freight.freight',
            'type': 'ir.actions.act_window',
            'res_id': self.freight_id.id,
            'target': 'self',
            'context': context,
        }

    def open_freight_record_obl(self):
        view_id = self.env.ref('warefor_3pl_tus.freight_freights_obl_form_view').id
        context = self._context.copy()
        return {
            'name': 'freight_freight',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_model': 'freight.freight',
            'type': 'ir.actions.act_window',
            'res_id': self.freight_id.id,
            'target': 'self',
            'context': context,
        }

    @api.onchange('goods', 'total_quantity', 'total_pallet')
    def onchange_required_pallet(self):
        for rec in self:
            product_per_pallet = rec.goods.product_per_pallet
            rec.total_pallet = product_per_pallet
            qty = 0
            if rec.total_quantity > 0:
                qty = rec.total_quantity
            if rec.total_pallet > 0 and qty:
                rec.required_pallet = math.ceil(qty / rec.total_pallet)
            else:
                rec.required_pallet = 0


class FinalDestination(models.Model):
    _name = 'final.destination'
    _description = 'Final Destination'

    name = fields.Char(string="Name")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Destination Partner")


class FreightOSDStage(models.Model):
    _name = 'freight.osd.stage'
    _description = 'Freight OSD Stage'
    _order = 'sequence'

    is_fold = fields.Boolean(string="Folded in Pipeline", )
    name = fields.Char(string="Name")
    sequence = fields.Integer(string="Sequence", )
    is_shipment_confirmation = fields.Boolean(string="Is Shipment Confirmation Stage?")


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if self._context.get('import_file') and self._context.get('is_outbound') and self._name == 'res.partner':
            limit = 1
        res = super().name_search(name=name, args=args, operator=operator, limit=limit)
        return res


class StockQuant(models.AbstractModel):
    _inherit = 'stock.quant'

    def write(self, vals):
        res = super(StockQuant, self).write(vals)
        review_id = self.env.ref('mc_freight_app.shipped_review').id
        scheduled_id = self.env.ref('mc_freight_app.scheduled_outbound').id
        for rec in self:
            obl_line_ids = self.env['freight.order.line'].search([('goods', '=', rec.product_id.id), ('freight_id.outbound_stage_id', '=', review_id)])
            if obl_line_ids:
                freight_ids = obl_line_ids.freight_id
                for freight_id in freight_ids:
                    is_available_stock = freight_id.check_stock_availalibility()
                    if is_available_stock:
                        freight_id.outbound_stage_id = scheduled_id
        return res

    @api.model
    def create(self, vals):
        res = super(StockQuant, self).create(vals)
        review_id = self.env.ref('mc_freight_app.shipped_review').id
        scheduled_id = self.env.ref('mc_freight_app.scheduled_outbound').id
        for rec in res:
            obl_line_ids = self.env['freight.order.line'].search([('goods', '=', rec.product_id.id), ('freight_id.outbound_stage_id', '=', review_id)])
            if obl_line_ids:
                freight_ids = obl_line_ids.freight_id
                for freight_id in freight_ids:
                    is_available_stock = freight_id.check_stock_availalibility()
                    if is_available_stock:
                        freight_id.outbound_stage_id = scheduled_id
        return res
