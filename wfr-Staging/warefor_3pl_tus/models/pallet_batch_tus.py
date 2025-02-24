# -*- coding: utf-8 -*-
import base64
import functools
import io
import logging
import re
from base64 import b64encode

import qrcode
from odoo.exceptions import ValidationError

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

ALGORITHM = 'sha1'
DIGITS = 6
compress = functools.partial(re.sub, r'\s', '')

shipping_code = '011'


class PalletBatchTus(models.Model):
    _name = 'pallet.batch.tus'
    _inherit = 'mail.thread'
    _description = 'Pallet Batches'

    name = fields.Char(_("Name"), default="New")
    company_id = fields.Many2one('res.company', _('Company'), index=True)
    pallet_company_id = fields.Many2one('res.company', string=_('Company'), compute='compute_company_id')
    is_enabled = fields.Boolean(_('Enabled?'), default=False, help="Once enabled the pallet, start the price counting.")
    is_transferred = fields.Boolean(_('Is Transferred?'), default=False,
                                    help="Once transfer the pallet inventory, marked this automatically.")
    # First created start_date fields and did the development so as per the new requirements just changed the string
    # and created new field for billing date
    billing_from = fields.Date(string="Start Date")
    start_date = fields.Date(string="Billing From")
    end_date = fields.Date(string="End Date")
    active = fields.Boolean(_('Active'), default=True)
    warehouse_id = fields.Many2one('stock.warehouse', string=_('Warehouse'), compute='_compute_warehouse_id')
    product_box_ids = fields.One2many(comodel_name="pallet.box.items", inverse_name="pallet_id", string=_("Box"))
    import_cost_ids = fields.One2many(comodel_name="pallet.import.cost", inverse_name="pallet_id",
                                      string=_("Import Cost"))
    storage_cost_ids = fields.One2many(comodel_name="pallet.storage.cost", inverse_name="pallet_id",
                                       string=_("Storage Fees"))
    fob_cost_ids = fields.One2many(comodel_name="pallet.fob.cost", inverse_name="pallet_id",
                                   string=_("Calculated against FOB"))
    vas_cost_ids = fields.One2many(comodel_name="pallet.vas.cost", inverse_name="pallet_id",
                                   string=_("Value Added Service"))
    picking_id = fields.Many2one(comodel_name="stock.picking", string=_("Transfer"))

    stock_location_place_ids = fields.One2many(comodel_name="stock.location.pallet", inverse_name="pallet_batch_id",
                                               string=_("Pallet Location"))

    picking_count = fields.Integer('# Transfers', compute="_compute_picking_count")

    box_ids = fields.One2many(comodel_name="pallet.box.line", inverse_name="pallet_id", string="Box Lines")
    product_ids = fields.One2many(comodel_name="pallet.product.line", inverse_name="pallet_id", string="Product Lines")

    max_weight = fields.Float("Max Weight")
    min_weight = fields.Float("Min Weight")
    max_qty = fields.Float("Max Quantity")
    min_qty = fields.Float("Min Quantity")
    total_weight = fields.Float("Total Weight", compute="_compute_total_weight_qty")
    total_qty = fields.Float("Total Qty", compute="_compute_total_weight_qty")

    sale_order_id = fields.Many2one(comodel_name='sale.order', string="Sale Order", domain="[('state', '=', 'sale')]")

    import_cost = fields.Float(string=_("Import Cost"), compute="_compute_import_cost")
    fob_cost = fields.Float(string=_("FOB"), compute="_compute_fob_cost")
    storage_cost = fields.Float(string=_("Storage"), compute="_compute_storage_cost", help="Billing date to end date")
    total_storage_cost = fields.Float(string=_("Total Storage Cost"), compute="_compute_storage_cost",
                                      help="Start date to end date")
    service_cost = fields.Float(string=_("Handling & Materials"), compute="_compute_vas_cost")
    total_price = fields.Float(string=_("Total Price"), help=_("Total Price"))
    potd_price = fields.Float(string=_("Current Unit Cost"), help=_("Current Unit Cost"))

    invoice_ids = fields.One2many(comodel_name="account.move", inverse_name="pallet_id", string="Invoices")
    payment_ids = fields.One2many(comodel_name="account.payment", inverse_name="pallet_id", string="Payments")
    potd_ids = fields.One2many(comodel_name="pallet.potd", inverse_name="pallet_id", string="POTD")

    store_type = fields.Selection(string="Store Type", default='order',
                                  selection=[('order', 'Delivery Order'), ('box', 'Box'), ('product', 'Product')])
    edi_data_file = fields.Binary('EDI File')
    edi_data_file_name = fields.Char('EDI File Data')

    location_id = fields.Many2one(
        'stock.location', 'Source Location',
        check_company=True,
        help="Sets a location if you produce at a fixed location. "
             "This can be a partner location if you subcontract the manufacturing operations.")

    pallet_product_batch = fields.Integer(string="Pallet Product Batch", compute='_compute_pallet_product_batch')
    pallet_number = fields.Integer(string="Pallet Number", compute='_compute_pallet_product_batch')

    purchase_reference = fields.Char(string="PO Number")

    @api.depends('transit_app_id')
    def _compute_pallet_product_batch(self):
        """
        """
        for rec in self:
            rec.pallet_product_batch = 1
            rec.pallet_number = 1
        transit_app_ids = self.mapped('transit_app_id')
        for rec in transit_app_ids:
            for product_id in rec.pallet_ids.mapped("product_ids.product_id"):
                pallet_ids = rec.pallet_ids.filtered(lambda p: product_id.id in p.product_ids.mapped('product_id').ids)
                pallet_ids.pallet_product_batch = len(pallet_ids)
                pallet_number = 1
                for pallet in pallet_ids:
                    pallet.pallet_number = pallet_number
                    pallet_number += 1

    def _domain_location_dest_id(self):
        company_ids = self.env['res.company'].search([('is_logistics', '!=', True)])
        location_ids = self.env['stock.location'].search(
            [
                ('company_id', 'in', company_ids.ids),
                # ('is_rack', '=', True)
            ]
        )
        return [('id', 'in', location_ids.ids)]

    location_dest_id = fields.Many2one(
        'stock.location', 'Destination Location',
        check_company=True,
        domain=_domain_location_dest_id,
        help="Location where the system will stock the finished products.")

    description = fields.Text(_("Description"))

    state = fields.Selection(
        selection=[('draft', 'Draft'), ('in_progress', 'In Progress'), ('done', 'Done'), ('cancel', 'Cancelled')],
        string='Status', tracking=True, default='draft')

    moved_inventory_picking_ids = fields.Char(string="Orders")
    current_location_id = fields.Many2one(comodel_name="stock.location", string="Current Pallet Stock")
    storage_duration = fields.Char("Storage Duration", compute="_compute_storage_duration")
    is_invoice_created = fields.Boolean("Is Invoice Created?", default=False)
    transit_app_id = fields.Many2one("freight.freight", string="Freight Record")
    sscc_18_barcode_char = fields.Char(string="SSCC-18 Barcode Number")
    base_url = fields.Char(string="Base URL", compute="_compute_base_url")
    total_cube = fields.Char(string="Cube", compute="_compute_total_weight_qty")

    markup_import_cost = fields.Float(string="MU (%)", default=10.0)

    @api.depends('company_id')
    def compute_company_id(self):
        """
        Set Company WFS
        """
        for rec in self:
            company_id = self.env['res.company'].search([('company_code', '=', 'WFS')])
            rec.pallet_company_id = company_id.id

    @api.depends('current_location_id')
    def _compute_warehouse_id(self):
        """
        Select the warehouse in pallet from pallet current location
        """
        for rec in self:
            rec.warehouse_id = rec.current_location_id.warehouse_id.id

    @api.depends('product_ids')
    def _compute_total_weight_qty(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        for rec in self:
            pallet_configuration_id = rec.transit_app_id.pallet_configuration_id
            total_qty = 0
            compute_weight = 0
            total_cube = pallet_configuration_id.cube
            to_uom = self.env.ref('uom.product_uom_lb', False)
            if not to_uom:
                rec.total_weight = compute_weight
                rec.total_qty = total_qty
                rec.total_cube = round(total_cube, 2)
            else:
                for product_line in rec.product_ids:
                    product_id = product_line.product_id
                    if product_line.product_id:
                        weight = product_id.weight
                        uom_name = product_id.weight_uom_name
                        if uom_name == 'kg':
                            product_qty_weight = weight * to_uom.factor
                            compute_weight += (product_line.product_qty * product_qty_weight)
                        else:
                            compute_weight += (product_line.product_qty * weight)
                    total_qty += product_line.product_qty
                if rec.box_ids:
                    compute_weight = sum([n.box_qty * n.box_id.max_weight for n in rec.box_ids])
                rec.total_weight = round(compute_weight, 3)
                rec.total_qty = total_qty
                rec.total_cube = round(total_cube, 2)

    def _compute_base_url(self):
        for rec in self:
            rec.base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

    @api.depends("start_date", "end_date")
    def _compute_storage_duration(self):
        for record in self:
            if record and record.start_date:
                end_date = record.end_date or fields.Date.today()
                start_date = record.start_date
                num_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                num_days = end_date.day - start_date.day
                record.storage_duration = "Month: {} | Days: {}".format(num_months, abs(num_days))
            else:
                record.storage_duration = "-"

    @api.model
    def create(self, val):
        # Inherit: To add sequence in the pallet batch
        if not val.get("name") or val.get("name") == "New":
            sequence = self.env['ir.sequence'].next_by_code('pallet.batch.tus')
            val["name"] = sequence
        res = super(PalletBatchTus, self).create(val)

        res.generate_sscc_code()

        return res

    def generate_sscc_code(self):
        """
        Generate Pallet SSCC barcode
        :return:
        """
        for rec in self:
            """
            Document Reference: for generating pallet SSCC barcodes
            https://www.gs1us.org/DesktopModules/Bring2mind/DMX/Download.aspx?Command=Core_Download&EntryId=177&language=en-US&PortalId=0&TabId=134  
            """
            app_identifier = "(00)"
            extension_digit = len("{}".format(rec.id))
            gs1_code = rec.picking_id.company_id.gs1_company_prefix or "0000000"
            gs_code_length = 16 - len(gs1_code)
            serial_number = "{}{}".format(("0" * (gs_code_length - extension_digit)), rec.id)
            check_digit = "0"

            rec.sscc_18_barcode_char = "{app_identifier}{extension_digit}{gs1_code}{serial_number}{check_digit}".format(
                app_identifier=app_identifier,
                extension_digit=extension_digit,
                gs1_code=gs1_code,
                serial_number=serial_number,
                check_digit=check_digit
            )

    @api.depends('product_box_ids', 'stock_location_place_ids')
    def _compute_qrcode(self):
        for pallet in self:
            product_details = ""
            location_details = ""
            next_location = ""

            if pallet.store_type == 'product':
                for product_line in pallet.product_ids.filtered(lambda p: p.product_id):
                    if product_details:
                        product_details += "\nName: " + product_line.product_id.name if product_line.product_id else ""
                        product_details += "\nPackage QTY: " + str(
                            product_line.product_qty) if product_line.product_qty else ""
                        product_details += "\nTotal QTY: " + str(
                            product_line.product_qty) if product_line.product_qty else ""
                        # product_details += "\nPrice: " + str(
                        #     product_line.product_id.lst_price) if product_line.product_id.lst_price else ""
                    else:
                        product_details = "\nProduct Details:"
                        product_details += "\nName: " + product_line.product_id.name if product_line.product_id else ""
                        product_details += "\nPackage QTY: " + str(
                            product_line.product_qty) if product_line.product_qty else ""
                        product_details += "\nTotal QTY: " + str(
                            product_line.product_qty) if product_line.product_qty else ""
                        # product_details += "\nPrice: " + str(
                        #     product_line.product_id.lst_price) if product_line.product_id.lst_price else ""
            if pallet.current_location_id:
                location_details = "\nCurrent Location: {}".format(pallet.current_location_id.name or "")
            if pallet.location_dest_id:
                next_location = "\nNext Location: {}".format(pallet.location_dest_id.name or "")
            import_cost = "\nImport Cost: " + str(pallet.import_cost) if pallet.import_cost else ""
            storage_cost = "\nStorage Cost: " + str(pallet.storage_cost) if pallet.storage_cost else ""
            service_cost = "\nService Cost: " + str(pallet.service_cost) if pallet.service_cost else ""

            weight_details = "\nWeight: " + (pallet.total_weight and str(pallet.total_weight) or "")

            data = io.BytesIO()
            input_data = "Pallet: " + pallet.name + "\nEnabled: " + str(
                pallet.is_enabled) + product_details + import_cost + storage_cost + service_cost + weight_details + \
                         location_details + next_location
            qr = qrcode.QRCode(version=1, box_size=4, border=5)
            qr.add_data(input_data)
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            img.save(data, optimise=True, format='PNG')
            pallet.qrcode = base64.b64encode(data.getvalue()).decode()

    qrcode = fields.Binary(string="Barcode", compute='_compute_qrcode')

    @api.constrains('start_date', 'end_date')
    def _check_pallet_date(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_('Added date is incorrect! \n \nEnd date is always grater then start date.'))
            if not record.start_date and record.start_date and record.start_date > fields.Date.today():
                raise ValidationError(_('Added date is incorrect! \n \nStart date is always less then the today date.'))

    def write(self, values):
        if values.get('is_enabled'):
            if not values.get('start_date') and not self.start_date:
                raise ValidationError(_("Please add the start date for enable the pallet."))
            else:
                values.update({'state': 'in_progress'})

        return super(PalletBatchTus, self).write(values)

    @api.depends('storage_cost_ids')
    def _compute_storage_cost(self):
        today_date = fields.date.today()
        for pallet in self:
            if not all([pallet.start_date, pallet.billing_from]):
                pallet.storage_cost = 0
                pallet.total_storage_cost = 0
                continue
            if pallet.end_date:
                days = pallet.end_date - pallet.start_date
                total_days = pallet.end_date - pallet.billing_from
            else:
                days = today_date - pallet.start_date
                total_days = today_date - pallet.billing_from

            days = days and days.days + 1 or 0
            total_days = total_days and total_days.days + 1 or 0
            storage_cost = pallet.storage_cost_ids and sum(pallet.storage_cost_ids.mapped('total_cost')) or 0
            pallet.storage_cost = storage_cost * days
            pallet.total_storage_cost = storage_cost * total_days
            pallet.cal_total()

    @api.depends('vas_cost_ids')
    def _compute_vas_cost(self):
        for record in self:
            record.service_cost = record.vas_cost_ids and sum(record.vas_cost_ids.mapped('total_cost')) or 0
            record.cal_total()

    def cal_total(self):
        for rec in self:
            rec.total_price = sum(
                [rec.import_cost or 0.00, rec.total_storage_cost or 0.00, rec.service_cost or 0.00, rec.fob_cost or 0.00])
            product_qty = rec.product_ids.mapped('product_qty')
            total_pallet_qty = product_qty and sum(product_qty) or 0
            rec.potd_price = total_pallet_qty and rec.total_price / total_pallet_qty or 0

    @api.depends('import_cost_ids', 'fob_cost_ids')
    def _compute_import_cost(self):
        for record in self:
            import_cost_ids = record.import_cost_ids
            fob_cost_ids = record.fob_cost_ids
            import_cost_total = import_cost_ids and sum(import_cost_ids.mapped('total_cost')) or 0
            fob_cost_total = fob_cost_ids and sum(fob_cost_ids.mapped('total_cost')) or 0
            record.import_cost = import_cost_total + fob_cost_total
            record.cal_total()

    @api.depends('product_ids')
    def _compute_fob_cost(self):
        for record in self:
            record.fob_cost = 0
            freight_order_line_ids = record.transit_app_id.freight_order_line_ids
            for product_line in record.product_ids:
                product_qty = product_line.product_qty or 0
                freight_order_line = freight_order_line_ids.filtered(lambda x: x.goods.id == product_line.product_id.id)
                cost = freight_order_line and freight_order_line.base_cost or 0
                record.fob_cost = product_qty * cost

    @api.depends('product_box_ids')
    def _compute_picking_count(self):
        for record in self:
            picking_ids = []
            if self.moved_inventory_picking_ids:
                picking_ids = self.env["stock.picking"].search(
                    [('name', 'in', self.moved_inventory_picking_ids.split("|"))])
            record.picking_count = len(record.product_box_ids) or len(picking_ids)
            for pallet_item in record.product_box_ids:
                pallet_item.picking_id.pallet_id = record._origin.id

    def _process_rate_calculation(self):
        """
        Calculate the pallets rate as per the added price rate per day
        :return: True
        """
        try:
            _logger.info("Start cron execution: _process_rate_calculation")
            pallet_ids = self.search(
                [('end_date', '>=', fields.date.today()), ('start_date', '<=', fields.date.today())])
            _logger.info("Total {} Pallet in execution".format(pallet_ids.ids))
            for pallet in pallet_ids:
                total_amount = 0
                total_month = (fields.date.today().year - pallet.start_date.year) * 12 + (
                        fields.date.today().month - pallet.start_date.month)
                # total_month = (pallet.end_date.year - pallet.start_date.year) * 12 + (pallet.end_date.month - pallet.start_date.month)
                # _logger.info("Total {} month.".format(pallet.total_month))
                storage_cost_ids = pallet.storage_cost_ids.filtered(
                    lambda x: x.unit_of_measure == 'per_pallet_per_month')
                if storage_cost_ids:
                    total_amount = total_amount + sum(storage_cost_ids.mapped('total_cost'))
                    # if total_month > 0:
                    #     pallet.total_price = sum([total_month * total_amount, pallet.import_cost, pallet.service_cost])
                    # else:
                    storage_cost_ids = pallet.storage_cost_ids.filtered(
                        lambda x: x.unit_of_measure != 'per_pallet_per_month')
                    total_amount = total_amount + sum(storage_cost_ids.mapped('total_cost'))
                # For VAS cost
                per_month_vas_cost_ids = pallet.vas_cost_ids.filtered(lambda x: x.unit_of_measure == 'per_month')
                total_amount = total_amount + sum(per_month_vas_cost_ids.mapped('total_cost'))
                if total_month > 0:
                    total_amount = total_amount * total_month
                wo_per_month_vas_cost_ids = pallet.vas_cost_ids.filtered(lambda x: x.unit_of_measure != 'per_month')
                total_amount = total_amount + sum(wo_per_month_vas_cost_ids.mapped('total_cost'))
                # pallet.total_price = sum([total_amount, pallet.import_cost])
            _logger.info("Done cron execution: _process_rate_calculation")
            return True
        except Exception as e:
            return False

    def button_pallet_transfers(self):
        picking_ids = self.product_box_ids.mapped('picking_id').ids
        if not picking_ids and self.moved_inventory_picking_ids:
            picking_ids = self.env["stock.picking"].search(
                [('name', 'in', self.moved_inventory_picking_ids.split("|"))]).ids
        return {
            'name': _('Transfers'),
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', picking_ids)],
        }

    def action_state_done(self):
        for rec in self:
            rec.state = 'done'
            rec.write({
                'state': 'done',
                'is_enabled': False,
                'end_date': fields.date.today()
            })
            if rec.company_id.pallet_batch_email_validation:
                pallet_batch_template_id = self.env.ref('warefor_3pl_tus.mail_template_pallet_batch')
                if rec.invoice_ids:
                    rec.invoice_ids.action_invoice_print()
                    invoice_attachment = self.env['ir.attachment'].search(
                        [('res_model', '=', 'account.move'), ('res_id', 'in', rec.invoice_ids.ids)])
                    if invoice_attachment:
                        pallet_batch_template_id.attachment_ids = [(4, invoice_attachment.id)]
                rec.with_context(force_send=True).message_post_with_template(pallet_batch_template_id.id,
                                                                             email_layout_xmlid='mail.mail_notification_light')
                pallet_batch_template_id.attachment_ids.unlink()

    def action_reset_draft(self):
        for rec in self:
            rec.write({
                'state': 'draft',
                'is_enabled': False,
                'start_date': None,
                'end_date': None
            })

    def action_state_cancel(self):
        for rec in self:
            rec.write({
                'state': 'cancel',
                'is_enabled': False,
                'start_date': None,
                'end_date': None
            })

    def create_pallet_invoice(self):
        """ Call wizard to select partner before creating invoice from pallet batch.
        """
        res = {
            'name': "Create Pallet Invoice",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.pallet.invoice',
            'view_id': self.env.ref('warefor_3pl_tus.view_create_pallet_invoice_form').id,
            'target': 'new'
        }
        return res

    def transfer_inventory(self):
        """
        :return:
        """
        # Check the location and destination location is added in pallet or not
        pallet_location = self.location_id
        pallet_destination_location = self._context.get('pallet_location_id')
        if not pallet_destination_location:
            pallet_destination_location = self.location_dest_id
        if not all([pallet_location, pallet_destination_location]):
            raise ValidationError(_(
                'Please add the source location and destination location for creating internal transfer.'))
        pallet_in_location = pallet_destination_location.company_id.pallet_in_location
        if pallet_in_location and pallet_destination_location.stored_pallet >= pallet_in_location:
            raise ValidationError(_(
                'The selected location has no space to store new pallet.'))

        # If product lines is added in pallet then only start the pallet inventory movement
        if self.product_ids:
            first_picking_type = self.env["stock.picking.type"].search(
                [('company_id', '=', pallet_location.company_id.id), ('code', '=', 'internal'),
                 ('default_location_dest_id.usage', '=', 'transit')], limit=1)
            second_picking_type = self.env["stock.picking.type"].search(
                [('company_id', '=', pallet_destination_location.company_id.id), ('code', '=', 'internal'),
                 ('default_location_src_id.usage', '=', 'transit')], limit=1)

            # Check the configured picking operations for Pallet inventory movement
            if not first_picking_type or not second_picking_type:
                raise ValidationError("Please configure the Operation type for internal transfer from pallet.")
            transit_picking = first_picking_type.env['stock.picking'].create({
                'location_id': pallet_location.id,
                'location_dest_id': first_picking_type.default_location_dest_id.id,
                'picking_type_id': first_picking_type.id,
                'pallet_id': self.id,
                'company_id': first_picking_type.company_id.id
            })

            for product_line in self.product_ids:
                first_picking_type.env['stock.move'].create({
                    'name': product_line.product_id.name,
                    'location_id': pallet_location.id,
                    'location_dest_id': first_picking_type.default_location_dest_id.id,
                    'picking_id': transit_picking.id,
                    'product_id': product_line.product_id.id,
                    'product_uom': product_line.product_id.uom_id.id,
                    'product_uom_qty': product_line.product_qty,
                    'company_id': first_picking_type.company_id.id
                })
            transit_picking.action_confirm()
            transit_picking.action_assign()
            res = transit_picking.button_validate()
            default_pick_ids = res['context']['button_validate_picking_ids'] and \
                               res['context']['button_validate_picking_ids'][0] or []
            if default_pick_ids:
                vals = {
                    "pick_ids": res['context']['default_pick_ids'],
                    "immediate_transfer_line_ids": [(0, 0, {'picking_id': default_pick_ids, 'to_immediate': True})]
                }
                wizard_process = self.env[res['res_model']].create(vals)
                wizard_process.with_context(button_validate_picking_ids=default_pick_ids).process()

            transferred_picking = second_picking_type.env['stock.picking'].create({
                'location_id': second_picking_type.default_location_src_id.id,
                'location_dest_id': pallet_destination_location.id,
                'picking_type_id': second_picking_type.id,
                'pallet_id': self.id,
                'company_id': second_picking_type.company_id.id
            })
            for product_line in self.product_ids:
                second_picking_type.env['stock.move'].create({
                    'name': product_line.product_id.name,
                    'location_id': second_picking_type.default_location_src_id.id,
                    'location_dest_id': pallet_destination_location.id,
                    'picking_id': transferred_picking.id,
                    'product_id': product_line.product_id.id,
                    'product_uom': product_line.product_id.uom_id.id,
                    'product_uom_qty': product_line.product_qty,
                    'company_id': second_picking_type.company_id.id
                })
            transferred_picking.action_confirm()
            transferred_picking.action_assign()
            res = transferred_picking.button_validate()
            default_pick_ids = res['context']['button_validate_picking_ids'] and \
                               res['context']['button_validate_picking_ids'][0] or []
            if default_pick_ids:
                vals = {
                    "pick_ids": res['context']['default_pick_ids'],
                    "immediate_transfer_line_ids": [(0, 0, {'picking_id': default_pick_ids, 'to_immediate': True})]
                }
                wizard_process = self.env[res['res_model']].create(vals)
                wizard_process.with_context(button_validate_picking_ids=default_pick_ids).process()

            self.write({
                'is_transferred': True,
                'state': 'done',
                'is_enabled': False,
                'end_date': fields.date.today(),
                'moved_inventory_picking_ids': "{}|{}".format(transit_picking.name, transferred_picking.name),
                'current_location_id': second_picking_type.default_location_dest_id.id
            })
            pallet_location.stored_pallet -= 1
            # pallet_destination_location.stored_pallet += 1
            return second_picking_type

        return False

    def generate_edi_document(self):
        filename = 'EDI Pallet.edi'
        purchase_order = self.transit_app_id.purchase_orders_ids[0]
        create_date = self.create_date and self.create_date.strftime('%Y%m%d') or ''
        shipping_date = self.end_date and self.end_date.strftime('%Y%m%d') or ''
        po_date = purchase_order and purchase_order.date_planned.strftime('%Y%m%d') or ''
        create_time = self.create_date and self.create_date.strftime('%H%M') or ''
        shipping_time = self.end_date and self.end_date.strftime('%H%M') or ''
        partner_id = self.transit_app_id.import_id
        partner_shipping_id = self.transit_app_id.partner_id
        td1_data = ''
        td5_data = ''
        td3_data = ''
        sln_data = ''
        po4_data = ''
        n1_vn_data = ''
        n1_st_data = ''
        n3_vn_data = ''
        n3_st_data = ''
        n4_vn_data = ''
        n4_st_data = ''
        ref_data = ''
        ref_ao_data = ''
        prf_data = ''
        line_data = ''
        pid_data = ''
        sn1_data = ''

        environment = self.env['edi.environment'].search([])
        if environment.mode == 'testing':
            code = 'T'
        else:
            code = 'P'
        # HL for Price mart
        isa_data = 'ISA*00*          *00*          *01*012345678912345*01*176766905899   *151113*0807*U*00401*0000000' \
                   '01*0*' + code + '*^~'
        gs_data = 'GS*SH*012345678912345*176766905899*20160714*0807*000000001*X*004010~'
        st_data = 'ST*856*000000001~'
        bsn_data = 'BSN*00*' + (self.name or '') + '*' + create_date + '*' + create_time + '*0001~'
        dtm_data = 'DTM*' + shipping_code + '*' + shipping_date + '*' + shipping_time + '*' + 'ET~HL*1**S*1~'
        count_1 = 0

        for rec in self.product_ids:
            count_1 += 1
            # TODo: assigned the Carrier detail dynamically TD1
            td1_data = 'TD1*PLT*' + (str(int(rec.product_qty)) or '') + '****G*' + (
                    str(rec.product_id.weight) or '') + '*LB~'
            td5_data = 'TD5*B*1*HECI~'
            # ToDo: Give pallet number for TD302, Give unique shipment code on TD309
            td3_data = "TD3*{td301}*{td302}*{td303}*{td304}*{td305}*{td306}*{td307}*{td308}*{td309}~".format(
                td301="CN",
                td302="PA",
                td303="PAL1",
                td304="",
                td305="",
                td306="",
                td307="",
                td308="",
                td309="UPS"
            )
            # ToDo: Give value if lot number, IMEI number
            sln_data = "SLN*{sln01}*{sln02}*{sln03}*{sln04}*{sln05}*{sln06}*{sln07}*{sln08}*{sln09}*{sln010}*" \
                       "{sln011}*{sln012}*{sln013}*{sln014}*{sln015}*{sln016}~".format(
                sln01=str(count_1),
                sln02=str(count_1),
                sln03='I',
                sln04=str(rec.product_qty) or '',
                sln05='EA',
                sln06='',
                sln07='',
                sln08='',
                sln09='SN',
                sln010=str(rec.product_id.default_code) or '',
                sln011='LT',
                sln012='',
                sln013='AX',
                sln014='',
                sln015='',
                sln016='',
            )
            po4_data = "PO4*{po401}*{po402}*{po403}*{po404}*{po405}*{po406}*{po407}*{po408}*{po409}*{po4010}*" \
                       "{po4011}*{po4012}*{po4013}*{po4014}*{po4015}*{po4016}~".format(
                po401='1',
                po402='',
                po403='',
                po404='',
                po405='G',
                po406=str(rec.product_id.weight) or '',
                po407='LB',
                po408=str(rec.product_id.volume) or '',
                po409='CM',
                po4010=rec.product_id.product_length or '',
                po4011=rec.product_id.product_width or '',
                po4012=rec.product_id.product_height or '',
                po4013='IN',
                po4014='',
                po4015='',
                po4016='',
            )
        if partner_id:
            n1_vn_data = 'N1*VN*' + (partner_id.name or '') + '*92*' + (partner_id.ref or '') + '~'
        if partner_id.street:
            n3_vn_data = 'N3*' + (partner_id.street or '') + '~'
        if partner_id.city or partner_id.state_id or partner_id.country_id or partner_id.zip:
            n4_vn_data = 'N4*' + (partner_id.city or '') + '*' + (partner_id.state_id.code or '') + \
                         '*' + (partner_id.zip or '') + '*' + (partner_id.country_id.code or '') + '~'

        if partner_shipping_id:
            n1_st_data = 'N1*ST*' + (partner_shipping_id.name or '') + '~'
        if partner_shipping_id.street:
            n3_st_data = 'N3*' + (partner_shipping_id.street or '') + '~'
        if partner_shipping_id.city or partner_shipping_id.state_id or partner_shipping_id.country_id \
                or partner_shipping_id.zip:
            n4_st_data = 'N4*' + (partner_shipping_id.city or '') + '*' + (
                    partner_shipping_id.state_id.code or '') + \
                         '*' + (partner_shipping_id.zip or '') + '*' + (
                                 partner_shipping_id.country_id.code or '') + '~HL*3**P*1~'
        if self.picking_id:
            ref_data = "REF*{ref01}*{ref02}~".format(
                ref01="2I",
                ref02=str(self.picking_id.name),
            )

        # ToDo: this data came from price mart

        if self.name:
            ref_ao_data = "REF*{ref01}*{ref02}~HL*2**O*1~".format(
                ref01="AO",
                ref02=str(self.name),
            )
        if purchase_order:
            prf_data = "PRF*{prf01}***{prf04}~".format(
                prf01=purchase_order.name,
                prf04=po_date,
            )
        if not self.sscc_18_barcode_char:
            raise ValidationError(_('SSCC 18 is not set.'))
        man_data = "MAN*{man01}*{man02}**{man04}*{man05}~HL*4**I*1~".format(
            man01='GM',
            man02=self.sscc_18_barcode_char or '',
            man04='W',
            man05=self.name[-5:]
        )

        if self.transit_app_id.freight_order_line_ids:
            count = 0
            # Todo: need to check value of item number lin03
            for po_line in self.transit_app_id.freight_order_line_ids:
                if not po_line.goods.upc:
                    raise ValidationError(_('UPC Code is not set.'))
                if not po_line.goods.vendor_no:
                    raise ValidationError(_('Vendor No is not set.'))
                if not po_line.goods.hs_code:
                    raise ValidationError(_('HS Code is not set.'))
                if not po_line.goods.brand:
                    raise ValidationError(_('Brand is not set.'))
                if not po_line.goods.manufacturer:
                    raise ValidationError(_('Manufacturer is not set.'))
                if not po_line.goods.description:
                    raise ValidationError(_('Description is not set.'))

                count += 1
                line_data = "LIN*{lin01}*{lin02}*{lin03}*{lin04}*{lin05}*{lin06}*{lin07}*{lin08}*{lin09}*{lin010}*" \
                            "{lin011}*{lin012}*{lin013}*{lin014}*{lin015}~".format(
                    lin01=str(count),
                    lin02='IN',
                    lin03=po_line.goods.item_number or '',
                    lin04='UP',
                    lin05=po_line.goods.upc or '',
                    lin06='VN',
                    lin07=po_line.goods.vendor_no or '',
                    lin08='CH',
                    lin09=str(partner_id.country_id.code) or '',
                    lin010='HD',
                    lin011=po_line.goods.hs_code or '',
                    lin012='BL',
                    lin013=po_line.goods.brand or '',
                    lin014='MF',
                    lin015=po_line.goods.manufacturer or '',
                )
                sn1_data = "SN1*{sn101}*{sn102}*{sn103}~".format(
                    sn101=str(count),
                    sn102=po_line.total_quantity or '',
                    sn103=po_line.goods.uom_id.name[:2].upper() or '',
                )
                pid_data = "PID*{pid01}*{pid02}*{pid03}*{pid04}*{pid05}~HL*5**P*1~".format(
                    pid01='F',
                    pid02='',
                    pid03='',
                    pid04='',
                    pid05=po_line.goods.description or '',
                )
        ctt_data = 'CTT*4~'

        file_data = "{isa_data}{gs_data}{st_data}{bsn_data}{dtm_data}{td1_data}{td5_data}{td3_data}{n1_vn_data}" \
                    "{n3_vn_data}{n4_vn_data}{ref_data}{ref_ao_data}{prf_data}{n1_st_data}{n3_st_data}{n4_st_data}" \
                    "{man_data}{line_data}{sn1_data}{sln_data}{po4_data}{pid_data}{ctt_data}".format(
            isa_data=isa_data,
            gs_data=gs_data,
            st_data=st_data,
            bsn_data=bsn_data,
            dtm_data=dtm_data,
            td1_data=td1_data,
            td5_data=td5_data,
            td3_data=td3_data,
            sn1_data=sn1_data,
            sln_data=sln_data,
            po4_data=po4_data,
            n1_vn_data=n1_vn_data,
            n3_vn_data=n3_vn_data,
            n4_vn_data=n4_vn_data,
            n1_st_data=n1_st_data,
            n3_st_data=n3_st_data,
            n4_st_data=n4_st_data,
            ref_data=ref_data,
            ref_ao_data=ref_ao_data,
            prf_data=prf_data,
            man_data=man_data,
            line_data=line_data,
            pid_data=pid_data,
            ctt_data=ctt_data,
        )
        total_segment = file_data.count('~') - 1
        file_data = file_data + 'SE*' + str(total_segment) + '*000000001~GE*1*000000001~IEA*1*000000001~'

        file_data = file_data.encode('utf-8')
        file = b64encode(file_data)

        self.edi_data_file = file
        self.edi_data_file_name = filename

    def _calculte_product_potd(self):
        pallet_ids = self.search([('is_enabled', '=', True)])
        pallet_ids._compute_storage_cost()
        date = fields.Date.today()
        potd_data = []
        pallet_potd_obj = self.env['pallet.potd']
        product_ids = self.env['product.product'].search([('active', '=', True), ('type', '!=', 'service')])
        for product_id in product_ids:
            product_line_ids = pallet_ids.product_ids.filtered(lambda p: p.product_id.id == product_id.id)
            if product_line_ids:
                cost = sum(product_line_ids.pallet_id.mapped('potd_price'))
                pallets = product_line_ids.pallet_id.__len__()
                cost = cost / pallets
                potd_data.append(
                    {
                        'date': date,
                        'cost': cost,
                        'product_id': product_id.id
                    }
                )
        if potd_data:
            pallet_potd_obj.create(potd_data)


class PalletPOTD(models.Model):
    _name = 'pallet.potd'
    _description = 'Product price of the day for pallet'
    _rec_name = 'product_id'

    pallet_id = fields.Many2one(comodel_name='pallet.batch.tus', string='Pallet')
    date = fields.Date(string="Date")
    cost = fields.Float(string="Current Unit Cost", help='Current Unit Cost')
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
