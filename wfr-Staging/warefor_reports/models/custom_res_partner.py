# -*- coding: utf-8 -*-
from docutils.nodes import field_name

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError, UserError
from datetime import date
import zipfile
import io
from io import BytesIO
import base64
import math
from collections import defaultdict


class ProductTemplate(models.Model):
    _inherit = 'res.partner'

    gdc = fields.Char('GDC')
    gln = fields.Char('GLN')
    final_destination_code = fields.Char(string="Final Destination Code")


class FreightFreightInherit(models.Model):
    _inherit = 'freight.freight'

    type = fields.Char('Type')
    department = fields.Char('Department')
    commodity_desc_note = fields.Char('Commodity Description')
    ltl_nmfc = fields.Char('NMFC')
    ltl_class = fields.Char('Class')
    scac = fields.Char('SCAC')
    po_type = fields.Char('PO Type')
    event_code = fields.Char('Event Code')
    is_quantity_check_load = fields.Boolean('Quantity Check')
    is_qc_check_load = fields.Boolean("QC Check", default=True)
    order_loaded_name_load = fields.Char('Order Picked and Loaded By')
    order_loaded_sign_load = fields.Binary('Order Picked and Loaded Signature')
    duty_supervisor_name_load = fields.Char('Name of Supervisor')
    duty_supervisor_sign_load = fields.Binary('Signature of Supervisor')
    # master and house bill of lading fields
    is_fr_prepaid = fields.Boolean('Is Freight Prepaid')
    is_fr_collect = fields.Boolean('Is Freight Collect')
    is_fr_3rd_party = fields.Boolean('Is Freight 3rd Party')
    cod_amount = fields.Char('COD Amount')
    is_fee_prepaid = fields.Boolean('Is Fee Prepaid')
    is_fee_collect = fields.Boolean('Is Fee Collect')
    is_customer_check = fields.Boolean('Is Customer Check Acceptable')
    date = fields.Date('Date')
    pickup_date = fields.Date('Pickup Date')
    is_by_shipper_trai = fields.Boolean('Is By Shipper')
    is_by_driver_trai = fields.Boolean('Is By Driver')
    is_by_shipper_freight = fields.Boolean('Is By Shipper')
    is_by_driver_freight = fields.Boolean('Is By Driver/ Pallets Said to Contain')
    is_by_pieces = fields.Boolean('Is By Driver/ Pieces')
    shipper_sign = fields.Binary('Signature of Shipper', required=True)
    carrier_sign = fields.Binary('Signature of Carrier', required=True)

    # house bill of lading fields
    is_fr_prepaid_h = fields.Boolean('Is Freight Prepaid(HBOL)')
    is_fr_collect_h = fields.Boolean('Is Freight Collect(HBOL)')
    is_fr_3rd_party_h = fields.Boolean('Is Freight 3rd Party(HBOL)')
    cod_amount_h = fields.Char('COD Amount(HBOL)')
    is_fee_prepaid_h = fields.Boolean('Is Fee Prepaid(HBOL)')
    is_fee_collect_h = fields.Boolean('Is Fee Collect(HBOL)')
    is_customer_check_h = fields.Boolean('Is Customer Check Acceptable(HBOL)')
    date_h = fields.Date('Date(HBOL)')
    pickup_date_h = fields.Date('Pickup Date(HBOL)')
    is_by_shipper_trai_h = fields.Boolean('Is By Shipper(HBOL)')
    is_by_driver_trai_h = fields.Boolean('Is By Driver(HBOL)')
    is_by_shipper_freight_h = fields.Boolean('Is By Shipper(HBOL)')
    is_by_driver_freight_h = fields.Boolean('Is By Driver/ Pallets Said to Contain(HBOL)')
    is_by_pieces_h = fields.Boolean('Is By Driver/ Pieces(HBOL)')
    shipper_sign_h = fields.Binary('Signature of Shipper(HBOL)', required=True)
    carrier_sign_h = fields.Binary('Signature of Carrier(HBOL)', required=True)
    shipping_document_line_ids = fields.One2many('shipping.document.line','freight_id')
    gdc = fields.Char('GDC')
    shipping_point = fields.Char('Shipping Point')
    number_of_cases = fields.Integer(string="# of Cases", compute="_compute_number_of_cases", store=True)
    freeze = fields.Boolean('Read Only')
    final_destination = fields.Many2one('res.partner', string="Final Destination")
    final_destination_code = fields.Char(string="Final Destination Code", related='final_destination.final_destination_code')
    actual_req_items = fields.One2many('actual.freight.items','freight_id')

    def write(self, vals):
        res = super(FreightFreightInherit, self).write(vals)
        if 'freight_order_line_ids' in vals:
            report_service = self.env['ir.actions.report']
            full_name = self.name + '_' + 'House_Bill_Of_Lading.pdf'
            get = self.env['shipping.document.line'].search([('report_name', '=', full_name), ('freight_id', '=', self.id)])
            if get:
                get.unlink()
            pdf_data = \
            report_service._get_report_from_name('warefor_reports.report_HouseBillOfLading')._render_qweb_pdf(
                'warefor_reports.report_HouseBillOfLading', res_ids=[self.id])[0]
            self.create_shipping_document_line_item(base64.b64encode(pdf_data), full_name, self)

        if self.actual_req_items:
            product = set(self.freight_order_line_ids.mapped('goods'))
            for each in product:
                actual_qty = sum(self.actual_req_items.filtered(lambda l:l.product_id.id == each.id).mapped('case_qty'))
                qty_in_line = sum(self.freight_order_line_ids.filtered(lambda l:l.goods.id == each.id).mapped('qty_carton'))
                if qty_in_line != actual_qty:
                    raise ValidationError("Quantity is no matching with the Actual Requested Qty for the Product - %s"%(each.name))
        return res

    @api.model
    def create(self, vals):
        res = super(FreightFreightInherit, self).create(vals)
        if 'freight_order_line_ids' in vals:
            report_service = res.env['ir.actions.report']
            full_name = res.name + '_' + 'House_Bill_Of_Lading.pdf'
            pdf_data = report_service._get_report_from_name('warefor_reports.report_HouseBillOfLading')._render_qweb_pdf(
                    'warefor_reports.report_HouseBillOfLading', res_ids=[res.id])[0]
            res.create_shipping_document_line_item(base64.b64encode(pdf_data), full_name, res)
        return res


    def action_print_bol_report(self):
        bol_no = set(self.mapped('bol_number'))
        ship_to_id = self.mapped('outbound_partner_id')
        ship_from_id = self.mapped('ship_from_partner_id')
        ship_from = set(ship_from_id.mapped('name'))
        ship_to = set(ship_to_id.mapped('name'))

        if len(bol_no) > 1:
            raise ValidationError("Bol# must be Same selected records")
        if len(ship_from) > 1:
            raise ValidationError("Ship From Address must be same for selected records")
        if len(ship_to) > 1:
            raise ValidationError("Ship From Address must be same for selected records")

        report_service = self.env['ir.actions.report']
        zip_buffer = BytesIO()

        with (zipfile.ZipFile(zip_buffer, 'w') as zf):
            pdf_data = report_service._get_report_from_name('warefor_reports.report_MasterBillOfLading_new')._render_qweb_pdf(
                'warefor_reports.report_MasterBillOfLading_new', res_ids=self.ids)[0]

            attachment = self.env['ir.attachment'].create({
                'name': "Master_Bill_Of_Lading.zip",
                'type': 'binary',
                'datas': base64.b64encode(pdf_data),
                'res_model': self._name,
                'mimetype': 'application/pdf',
            })

            zf.writestr('Master_Bill_Of_Lading.pdf', pdf_data)
            for rec in self:
                shipping_line = rec.mapped('shipping_document_line_ids')

                if shipping_line:
                    master_doc_item = shipping_line.filtered(lambda l: 'Master_Bill_Of_Lading.pdf' in l.report_name)
                    house_doc_item = shipping_line.filtered(lambda l: 'House_Bill_Of_Lading.pdf' in l.report_name)

                    if master_doc_item:
                        for doc in master_doc_item:
                            doc.unlink()
                        rec.create_shipping_document_line_item(pdf_data, 'Master_Bill_Of_Lading.pdf', rec)

                    if not master_doc_item:
                        rec.create_shipping_document_line_item(pdf_data, 'Master_Bill_Of_Lading.pdf', rec)

                    if house_doc_item:
                        attachment_content = base64.b64decode(house_doc_item.attachment_id.datas)
                        zf.writestr(house_doc_item.report_name, attachment_content)

                    if not house_doc_item:
                        pdf_data = report_service._get_report_from_name('warefor_reports.report_HouseBillOfLading')._render_qweb_pdf(
                            'warefor_reports.report_HouseBillOfLading', res_ids=[rec.id])[0]
                        attachment_content = base64.b64encode(pdf_data)
                        report_name = rec.name + "_" + "House_Bill_Of_Lading.pdf"
                        zf.writestr(report_name, pdf_data)
                        rec.create_shipping_document_line_item(attachment_content,report_name, rec)

                if not shipping_line:
                    rec.create_shipping_document_line_item(base64.b64encode(pdf_data),
                                                           'Master_Bill_Of_Lading.pdf', rec)

                    pdf_data = report_service._get_report_from_name('warefor_reports.report_HouseBillOfLading')._render_qweb_pdf(
                        'warefor_reports.report_HouseBillOfLading', res_ids=[rec.id])[0]
                    report_name = rec.name + "_" + "House_Bill_Of_Lading.pdf"
                    zf.writestr(report_name, pdf_data)
                    rec.create_shipping_document_line_item(base64.b64encode(pdf_data), report_name, rec)



        zip_buffer.seek(0)
        zip_data = zip_buffer.read()

        zip_attachment = self.env['ir.attachment'].create({
            'name': 'Bills_Of_Lading.zip',
            'type': 'binary',
            'datas': base64.b64encode(zip_data),
            'mimetype': 'application/zip',
        })

        return {
        'type': 'ir.actions.act_url',
        'url': f'/web/content/{zip_attachment.id}?download=true',
        'target': 'new',
    }


    def grouped_lines_list(self, docs):
        grouped_lines = {}
        sub_pallet = list(set(int(x.sub_pallet) for x in docs if x.sub_pallet))
        sub_pallet.sort()
        line_no = 0
        for sub_p in sub_pallet:
            values = []
            for line in docs:
                if sub_p == int(line.sub_pallet):
                     values.append({
                            'sscc_18_char': line.sscc_18_char,
                            'pallet_type': line.pallet_type,
                            'sub_pallet': line.sub_pallet,
                            'qty_case': int(line.qty_carton or 0),
                            'default_code': line.goods.default_code,
                            'item_customer_number': line.goods.item_customer_number,
                            'qty_unit': round(line.total_quantity or 0),
                            'product_volume': round(line.product_volume or 0, 2),
                            'net_weight': round(line.net_weight or 0, 2),
                        })
            grouped_lines[sub_p] = values
            line_no = int(sub_p)
        line_no += 1
        for no_sub_p in docs:
            if not no_sub_p.sub_pallet:
                grouped_lines[line_no] = [{
                    'sscc_18_char': no_sub_p.sscc_18_char,
                    'pallet_type': no_sub_p.pallet_type,
                    'sub_pallet': no_sub_p.sub_pallet,
                    'qty_case': int(no_sub_p.qty_carton or 0),
                    'default_code': no_sub_p.goods.default_code,
                    'item_customer_number': no_sub_p.goods.item_customer_number,
                    'qty_unit': round(no_sub_p.total_quantity or 0),
                    'product_volume': round(no_sub_p.product_volume or 0, 2),
                    'net_weight': round(no_sub_p.net_weight or 0, 2),
                }]
                line_no += 1

        return grouped_lines


    @api.depends('freight_order_line_ids.required_case')
    def _compute_number_of_cases(self):
        for rec in self:
            if rec.freight_order_line_ids:
                cases = rec.freight_order_line_ids.mapped('required_case')
                rec.number_of_cases = sum(cases)
            else:
                rec.number_of_cases = 0

    def _line_po_batch(self):
        for rec in self:
            grouped_lines = defaultdict(list)
            grouped_data = []
            for line in rec.freight_order_line_ids:
                if line.po_number:
                    grouped_lines[line.po_number].append(line)
            for po_number, lines in grouped_lines.items():
                grouped_data.append((po_number,lines))
            return grouped_data


    def total_subpallet_type(self):
        for recs in self:
            data = []
            non_mixed_data = recs.freight_order_line_ids.filtered(lambda l: not l.sub_pallet)
            mixed_data = list(set(int(x.sub_pallet) for x in recs.freight_order_line_ids if x.sub_pallet))
            mixed_data.sort()
            total_items = int(sum(non_mixed_data.mapped('required_pallet'))) + mixed_data[-1] if mixed_data else 0
            count = 0
            for mix_item in mixed_data:
                mix_item_data = {}
                if mix_item:
                    rec_data = recs.freight_order_line_ids.filtered(lambda l:int(l.sub_pallet) == mix_item)
                    mix_item_data['no_cases'] = int(sum(rec_data.mapped('qty_carton')))
                    mix_item_data['wm_item_no'] = rec_data[0].goods.item_customer_number if len(rec_data) > 1 else rec_data.goods.item_customer_number
                    mix_item_data['vendor_item_no'] = rec_data[0].goods.default_code if len(rec_data) > 1 else rec_data.goods.default_code
                    ssc_code = recs.freight_order_line_ids.filtered(lambda l:int(l.sub_pallet) == mix_item).mapped('sscc_18_char')
                    mix_item_data['ssc_code'] = ssc_code[0] if ssc_code else False
                    mix_item_data['po_number'] = rec_data[0].po_number if len(rec_data) > 1 else rec_data.po_number
                    mix_item_data['pallet_type'] = rec_data[0].pallet_type if len(rec_data) > 1 else rec_data.pallet_type
                    count = int(mix_item)
                    mix_item_data['count_no'] = str(count) + " of " + str(total_items)
                    data.append(mix_item_data)
                    mix_copy_item = mix_item_data.copy()
                    mix_copy_item['count_no'] = "Copy of " + str(count) + ' of ' + str(total_items)
                    data.append(mix_copy_item)
            for each in non_mixed_data:
                data_value = each._get_quantity_values()
                for sub_value in data_value:
                    item_data = {}
                    item_data['no_cases'] = int(sub_value[5])
                    item_data['wm_item_no'] = each.goods.item_customer_number
                    item_data['vendor_item_no'] = each.goods.default_code
                    item_data['ssc_code'] = each.sscc_18_char if each.sscc_18_char else False
                    item_data['po_number'] = each.po_number
                    item_data['pallet_type'] = each.pallet_type
                    count += 1
                    item_data['count_no'] = str(count)+" of "+str(total_items)
                    data.append(item_data)
                    copy_item = item_data.copy()
                    copy_item['count_no'] = "Copy of " + str(count) + ' of ' + str(total_items)
                    data.append(copy_item)
        return data
    # def remove_existing_attachment(self, name):
    #     existing_attachment = self.shipping_document_line_ids.filtered(lambda att: att.report_name == name)
    #     if existing_attachment:
    #         existing_attachment.unlink()

    def create_shipping_document_line_item(self, data, file_name, freight_id):
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': data,
            'mimetype': 'application/pdf',
        })
        freight_id.shipping_document_line_ids.create(
            {
                'freight_id': freight_id.id,
                'report_name': file_name,
                'attachment_id': attachment.id
            }
        )

    #
    def call_bill_of_lading(self):
        if self.fulfillment_method != 'bulk_orders':
            raise ValidationError("The fulfillment method must be 'Bulk' to proceed with batch printing.")

        report_service = self.env['ir.actions.report']

        report_mapping = {
            'Master_Bill_Of_Lading': 'warefor_reports.report_MasterBillOfLading',
            'House_Bill_Of_Lading': 'warefor_reports.report_HouseBillOfLading',
        }

        for keyword, report_name_ in report_mapping.items():
            if keyword in report_mapping:
                # Call the wizard for "Loaded_With_Pride"
                if keyword == 'Loaded_With_Pride':
                    return {
                        'type': 'ir.actions.act_window',
                        'name': 'Loaded With Pride',
                        'res_model': 'loaded.pride.wizard',
                        'view_mode': 'form',
                        'context': {'default_freight_record': self.id},
                        'target': 'new',
                    }

                elif keyword == 'Master_Bill_Of_Lading':
                    return {
                        'type': 'ir.actions.act_window',
                        'name': 'Master Bill of Lading',
                        'res_model': 'master.bol.wizard',
                        'view_mode': 'form',
                        'context': {'default_freight_record': self.id},
                        'target': 'new',
                    }

                doc_name = f'{self.report_name}.pdf'

                self.env['ir.attachment'].search([
                    ('res_model', '=', self._name),
                    ('res_id', '=', self.id),
                    ('name', '=', doc_name)
                ]).unlink()

                pdf_data = report_service._get_report_from_name(report_name_) \
                    ._render_qweb_pdf(report_name_, res_ids=[self.id])[0]

                attachment = self.env['ir.attachment'].create({
                    'name': doc_name,
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_data),
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/pdf',
                })

                self.write({
                    'attachment_id': attachment.id,
                })

                return {
                    'type': 'ir.actions.act_url',
                    'url': f'/web/content/{attachment.id}?download=true',
                    'target': 'new',
                }

    def combine_bill_of_lading(self):
        mbl_attachment = self.batch_print_pdf(self, 'Master_Bill_Of_Lading.pdf')

        hbl_attachment = self.batch_print_pdf(self, 'House_Bill_Of_Lading.pdf')

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('Master_Bill_Of_Lading.pdf', base64.b64decode(mbl_attachment.datas))
            zf.writestr('House_Bill_Of_Lading.pdf', base64.b64decode(hbl_attachment.datas))

        zip_buffer.seek(0)
        zip_data = zip_buffer.read()

        zip_attachment = self.env['ir.attachment'].create({
            'name': 'Bills_Of_Lading.zip',
            'type': 'binary',
            'datas': base64.b64encode(zip_data),
            'mimetype': 'application/zip',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{zip_attachment.id}?download=true',
            'target': 'new',
        }

    def shipment_manifest(self):
        zip_attachment = self.batch_print_pdf(self, 'Shipment_Manifest.pdf')

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{zip_attachment.id}?download=true',
            'target': 'new',
        }
    def loaded_with_pride(self):
        if self.fulfillment_method != 'bulk_orders':
            raise ValidationError("The fulfillment method must be 'Bulk' to proceed with batch printing.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Loaded With Pride',
            'res_model': 'loaded.pride.wizard',
            'view_mode': 'form',
            'context': {'default_freight_record': self.id},
            'target': 'new',
        }

    def pallet_label(self):
        zip_attachment = self.batch_print_pdf(self, 'PalletLabels_new.pdf')

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{zip_attachment.id}?download=true',
            'target': 'new',
        }

    def batch_print_pdf(self, rec, filename=None):
        report_service = self.env['ir.actions.report']

        zip_buffer = io.BytesIO()

        # List of report names and corresponding PDF filenames
        reports = [
            ('warefor_reports.report_ShipmentManifest', 'Shipment_Manifest.pdf'),
            ('warefor_reports.report_HouseBillOfLading', 'House_Bill_Of_Lading.pdf'),
            ('warefor_reports.report_LoadedWithPride', 'Loaded_With_Pride.pdf'),
            ('warefor_reports.report_MasterBillOfLading', 'Master_Bill_Of_Lading.pdf'),
            ('warefor_reports.report_PalletLabels_new', 'PalletLabels_new.pdf'),
        ]
        # Set zip file name based on the length of rec
        if len(rec) > 1:
            zip_file_name = "Combined_Shipping_Documents.zip"
        else:
            zip_file_name = f'{rec[0].name}_Shipping_Documents.zip'

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Loop over reports to generate PDFs and add them to the zip file
            for each in rec:
                if each.fulfillment_method != 'bulk_orders':
                    raise ValidationError("The fulfillment method must be 'Bulk' to proceed with batch printing.")
                for report_name, pdf_filename in reports:
                    if filename and filename != pdf_filename:
                        continue
                    if filename:
                        full_name = rec.name + '_' + filename
                        get = rec.env['shipping.document.line'].search([('report_name', '=', full_name),('freight_id','=',rec.id)])
                        if get:
                            get.unlink()
                        pdf_data = report_service._get_report_from_name(report_name)._render_qweb_pdf(
                            report_name, res_ids=[rec.id])[0]
                        rec.create_shipping_document_line_item(
                            base64.b64encode(pdf_data), f'{rec.name}_{pdf_filename}', rec)

                        pdf_attachment = self.env['ir.attachment'].create({
                            'name': f'{rec.name}_{pdf_filename}',
                            'type': 'binary',
                            'datas': base64.b64encode(pdf_data),
                            'mimetype': 'application/pdf',
                        })

                        return pdf_attachment
                    pdf_data = \
                    report_service._get_report_from_name(report_name)._render_qweb_pdf(report_name, res_ids=[each.id])[
                        0]

                    # Create shipping document line item (encoding to base64)
                    each.create_shipping_document_line_item(base64.b64encode(pdf_data), f'{each.name}_{pdf_filename}',
                                                            each)

                    # Add PDF to the zip file
                    zip_file.writestr(f'{each.name}_{pdf_filename}', pdf_data)

        # Read the contents of the zip file from the buffer
        zip_buffer.seek(0)
        zip_data = zip_buffer.read()

        # Create the attachment for the zip file
        zip_attachment = self.env['ir.attachment'].create({
            'name': zip_file_name,
            'type': 'binary',
            'datas': base64.b64encode(zip_data),  # Encoding the binary zip data to base64 for attachment
            'mimetype': 'application/zip',
        })

        return zip_attachment

    def action_download_pdfs(self):

        if self.shipping_document_line_ids:
            self.shipping_document_line_ids.unlink()

        zip_attachment = self.batch_print_pdf(self)

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{zip_attachment.id}?download=true',
            'target': 'new',
        }

    def action_download_batch_pdfs(self):
        prev_rec = self.mapped('shipping_document_line_ids')
        if prev_rec:
            prev_rec.unlink()
        zip_attachment = self.batch_print_pdf([x for x in self])
        return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{zip_attachment.id}?download=true',
                'target': 'new',
            }

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
                    existing_rec = rec.osd_transfer_ids.filtered(lambda l:l.freight_order_line_id.id == line.id)
                    if existing_rec.quantity != line.total_quantity:
                        existing_rec.quantity = line.total_quantity
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
                                {'sku_id': line.goods.id, 'quantity': line.total_quantity, 'lot_id': line.lot_id.id, 'freight_order_line_id': line.id}))
            if data:
                rec.osd_ids = data
            if transfer_line:
                rec.osd_transfer_ids = transfer_line

class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    pallet_type = fields.Char('Pallet Type')

class FreightOrderLine(models.Model):
    _inherit = 'freight.order.line'

    sscc_18_char = fields.Char(string="SSCC-18 Barcode Number")
    base_url = fields.Char(string="Base URL", compute="_compute_base_url")
    pallet_type = fields.Char('Pallet Type')
    required_case = fields.Float('Required Case', compute='_compute_required_case', store=True)
    sub_pallet = fields.Char(string="Sub Pallet")
    ref_id = fields.Char(string="Ref ID", help="It is usefull when splitting the records based on the Pallet and Carton per case quantity")
    is_full_pallet = fields.Boolean()
    is_processed = fields.Boolean()


    @api.onchange('total_quantity')
    def _onchange_qty(self):
        # Recalculate pallets on qty change
        self.is_processed = False
        # self.calculate_pallets()

    @api.depends('qty_carton','cartons_per_pallet')
    def _compute_required_case(self):
        for rec in self:
            qty_carton = rec.qty_carton
            cartons_per_pallet = rec.goods.cartons_per_pallet
            if qty_carton and cartons_per_pallet:
                rec.required_case = qty_carton / float(cartons_per_pallet)

    def _compute_base_url(self):
        for rec in self:
            rec.base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')



    # def generate_sscc_code_for_freight(self):
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
    #         def calculate_check_digit(number):
    #             total = sum(int(d) * (3 if (i % 2 == 0) else 1) for i, d in enumerate(reversed(number)))
    #             return (10 - (total % 10)) % 10
    #         def extract_serial_no(barcodes,gs1code):
    #             gs1_length = len(gs1code) + 5
    #             start = len(barcodes) - gs1_length
    #             serial_end = 21
    #             str_serial_no = str(barcodes[gs1_length:serial_end])
    #             return str_serial_no
    #         def generate_new_barcode(barcodes, gs1):
    #             str_serial_number = extract_serial_no(barcodes,gs1)
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
    #                 gs1_code = gs1_code,
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
    #                     already_exist = rec.env['sscc18.barcode'].sudo().search([('sscc18_barcode', '=', generated_sscc_code),('company_id', '=', company_id.id)])
    #                     if already_exist:
    #                         highest_rec = rec.env['sscc18.barcode'].sudo().search([
    #                             ('company_id', '=', company_id.id)
    #                         ], order="sscc18_barcode desc", limit=1)
    #                         barcode = highest_rec.sscc18_barcode
    #                         generated_sscc_code = generate_new_barcode(barcode, gs1_code)
    #                         str_serial_number = extract_serial_no(generated_sscc_code,gs1_code)
    #                         rec.env['sscc18.barcode'].sudo().create({
    #                                 'sscc18_barcode': generated_sscc_code,
    #                                 'company_id': company_id.id,
    #                                 'gs1_code': gs1_code,
    #                                 'serial_no': str_serial_number
    #                         })
    #                         rec.sscc_18_char = generated_sscc_code
    #                     else:
    #                         last_serial_number = extract_serial_no(generated_sscc_code,gs1_code)
    #                         rec.env['sscc18.barcode'].sudo().create({
    #                                 'sscc18_barcode': generated_sscc_code,
    #                                 'company_id': company_id.id,
    #                                 'gs1_code': gs1_code,
    #                                 'serial_no': last_serial_number
    #                         })
    #                         rec.sscc_18_char = generated_sscc_code


    # @api.model
    # def create(self, val):
    #     res = super(FreightOrderLine, self).create(val)
    #     # if val.get("goods"):
    #     #     res.generate_sscc_code_for_freight()
    #     total_pallet = val.get("total_pallet")
    #     total_quantity = val.get("total_quantity")
    #     if total_pallet and total_quantity:
    #         if total_quantity < total_pallet:
    #             res.pallet_type = 'Partial'
    #         elif total_quantity % total_pallet != 0:
    #             res.pallet_type = 'Partial'
    #         else:
    #             res.pallet_type = 'Full'
    #     return res

    # @api.model
    # def write(self, vals):
    #     total_pallet = vals.get("total_pallet", self.total_pallet)
    #     total_quantity = vals.get("total_quantity", self.total_quantity)
    #
    #     if total_pallet and total_quantity:
    #         for rec in self:
    #             if total_quantity < total_pallet or total_quantity % total_pallet != 0:
    #                 vals["pallet_type"] = "Partial"
    #             else:
    #                 vals["pallet_type"] = "Full"

        # return super().write(vals)



    def _get_case(self, total_case, quantity_per_case):
        total_case = float(total_case)
        quantity_per_case = float(quantity_per_case)
        case = 0.0
        if total_case >= quantity_per_case:
            case = quantity_per_case
        elif total_case < quantity_per_case and not total_case < 0:
            case = total_case
        return case
    
    def _get_quantity_values(self, **kwargs):
        total_pallet_qty = self.total_quantity
        quantity_per_pallet = self.total_pallet
        num_pallets = self.required_pallet
        weight_single = self.goods.weight
        volume_single = self.goods.volume
        quantity_per_case = self.goods.cartons_per_pallet
        total_case = self.qty_carton
        num_case = 0
        if quantity_per_case and total_case:
            num_case = math.ceil(int(total_case) / int(quantity_per_case))

        max_count = int(num_pallets)
        if max_count < num_case:
            max_count = num_case
        data = []

        for i in range(1, max_count + 1):
            if total_pallet_qty >= quantity_per_pallet:
                weight = quantity_per_pallet * weight_single
                volume = quantity_per_pallet * volume_single

                case = self._get_case(total_case, quantity_per_case)
                total_case -= float(quantity_per_case)

                data.append((i, quantity_per_pallet,'Full',weight,volume, case))
                total_pallet_qty -= quantity_per_pallet
            elif total_pallet_qty < quantity_per_pallet and not total_pallet_qty < 0:
                weight = total_pallet_qty * weight_single
                volume = total_pallet_qty * volume_single

                case = self._get_case(total_case, quantity_per_case)
                total_case -= float(quantity_per_case)

                data.append((i, total_pallet_qty, 'Partial', weight,volume, case))
                total_pallet_qty -= quantity_per_pallet
            elif total_pallet_qty <= 0:
                total_pallet_qty = 0.0
                weight = 0.0
                volume = 0.0
                case = self._get_case(total_case, quantity_per_case)
                total_case -= float(quantity_per_case)
                data.append((i, total_pallet_qty, ' ', weight, float(volume), case))
        return data

class ShippingDocumentLine(models.Model):
    _name = 'shipping.document.line'

    freight_id = fields.Many2one('freight.freight', string="Frieght_id")
    attachment_id = fields.Many2one('ir.attachment', string="Report")
    report_name = fields.Char(string="Report Name")

    def regenerate_document(self):
        report_service = self.env['ir.actions.report']

        if 'Loaded_With_Pride' in self.report_name:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Loaded With Pride',
                'res_model': 'loaded.pride.wizard',
                'view_mode': 'form',
                'context': {'default_freight_record': self.freight_id.id},
                'target': 'new',
            }

        if 'Master_Bill_Of_Lading' in self.report_name:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Master Bill of Lading',
                'res_model': 'master.bol.wizard',
                'view_mode': 'form',
                'context': {'default_freight_record': self.freight_id.id},
                'target': 'new',
            }

        if 'PalletLabels' in self.report_name:
            pdf_data = report_service._get_report_from_name('warefor_reports.report_PalletLabels_new')\
                ._render_qweb_pdf('warefor_reports.report_PalletLabels_new', res_ids=[self.freight_id.id])[0]

        if 'Shipment_Manifest' in self.report_name:
            pdf_data = report_service._get_report_from_name('warefor_reports.report_ShipmentManifest') \
                ._render_qweb_pdf('warefor_reports.report_ShipmentManifest', res_ids=[self.freight_id.id])[0]


        doc_name = f'{self.report_name}'.split('.')[0] + '.pdf'
        self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('name', '=', doc_name)
        ]).unlink()

        attachment = self.env['ir.attachment'].create({
            'name': doc_name,
            'type': 'binary',
            'datas': base64.b64encode(pdf_data),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

        self.write({
            'attachment_id': attachment.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
