# -*- coding: utf-8 -*-

import base64
import logging
import os
import traceback
from datetime import datetime
from datetime import date
from io import BytesIO

from odoo.tools.misc import formatLang
import xlsxwriter
from PIL import Image
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CustomInvoice(models.Model):
    _name = 'custom.invoice'
    _description = 'custom invoice'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner', string='Customer')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    invoice_date = fields.Date(string='Invoice Date')
    due_date = fields.Date(string='Due Date')
    order_lines = fields.One2many('custom.invoice.line', 'invoice_id', string="Lines")
    invoice_type = fields.Selection([('wfl_inbound', 'WFL Invoice Inbound'),
                                     ('wfl_storage', 'WFL Invoice Storage'),
                                     ])
    invoice_id = fields.Many2one('account.move', string="Invoice")
    transit_app_id = fields.Many2one("freight.freight", string="Freight")
    # inbound_count = fields.Integer(string='Inbound Count')
    # storage_count = fields.Integer(string='Storage Count')
    total_cost = fields.Float("Total Price", compute="_compute_total_cost")
    l2_invoice_id = fields.Many2one('custom.invoice', string="Level 2 Invoice")
    l3_invoice_id = fields.Many2one('custom.invoice', string="Level 3 Invoice")

    invoice_months = fields.Integer(compute="_pallet_used_month")

    @api.depends('invoice_months')
    def _pallet_used_month(self):
        """
        Calculating month for invoice
        :return:
        """
        for rec in self:
            start_month = rec.transit_app_id.pallet_ids[0].start_date
            difference_of_months = (rec.invoice_date.year - start_month.year) * 12 + (
                    rec.invoice_date.month - start_month.month) + 1
            rec.write({'invoice_months': difference_of_months})

    @api.depends('order_lines')
    def _compute_total_cost(self):
        """
        Calculate the Total Price from the invoice lines, Sum the service type product is an Total Price
        :return:
        """
        for rec in self:
            order_lines = rec.order_lines.filtered(lambda o: not o.is_exclude)
            rec.total_cost = sum(order_lines.mapped('price'))

    def print_invoice_report(self):
        if self.invoice_type != 'wfl_inbound':
            return False
        # Prepare Excel Report
        try:
            report_file_name = self.prepare_excel_report()
        except Exception as e:
            _logger.error(traceback.print_exc())
            return False

        # Create Attachment
        attachment = self.create_attachment(report_file_name)

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'download',
        }

    def print_invoice_pdf_report(self):
        if self.invoice_type != 'wfl_inbound':
            return False
        # Prepare Excel Report
        try:
            report_file_name = self.prepare_excel_report()
            pdf_command = "soffice --headless --convert-to pdf:'impress_pdf_Export' {} --outdir /tmp/".format(
                report_file_name)
            _logger.info(pdf_command)
            os.system(pdf_command)
            pdf_report_file_name = report_file_name.replace('xlsx', 'pdf')
            # Remove tmp file
            os.remove(report_file_name)
        except Exception as e:
            _logger.error(traceback.print_exc())
            return False

        # Create Attachment
        attachment = self.create_attachment(pdf_report_file_name)
        if self._context.get('is_website_process'):
            return attachment

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'download',
        }

    def prepare_excel_report(self):
        file_name = '/tmp/WFLInvoiceInboundReport.xlsx'
        workbook = xlsxwriter.Workbook(file_name)
        worksheet = workbook.add_worksheet()
        worksheet.screen_gridlines = False

        worksheet.set_landscape()

        worksheet.fit_to_pages(1, 0)
        worksheet.set_zoom(80)

        worksheet.set_column(0, 0, 2)
        worksheet.set_column(1, 2, 30)
        # worksheet.set_column(6, 2, 12)
        # worksheet.set_column(7, 2, 12)

        worksheet.set_row(17, 30)
        worksheet.set_row(18, 30)
        worksheet.set_row(19, 30)
        worksheet.set_row(20, 30)
        worksheet.set_row(21, 30)
        worksheet.set_row(22, 30)

        bold_format = workbook.add_format(
            {'bold': 1, 'align': 'left', 'valign': 'vcenter'})

        border_format = workbook.add_format(
            {'bold': 1, 'align': 'center', 'valign': 'vcenter', 'border': 1})

        border_bottom_format = workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'border': 1, 'top': False, 'bottom': False})

        border_grey_format = workbook.add_format(
            {'bold': 1, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': '#D0CECE'})

        light_grey_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#D0CECE'})

        data_format = workbook.add_format(
            {'align': 'left', 'valign': 'vcenter'})

        data_border_format_1 = workbook.add_format(
            {'border': 1, 'align': 'center', 'valign': 'vcenter'})

        data_border_format = workbook.add_format(
            {'border': 1, 'valign': 'vcenter', 'right': False})

        data_border_format_2 = workbook.add_format(
            {'border': 1, 'left': False, 'right': False, 'align': 'center', 'valign': 'vcenter'})

        logo = base64.b64decode(self.company_id.logo)
        logo = BytesIO(logo)

        company_logo = Image.open(logo).resize((220, 60), Image.ANTIALIAS)
        company_logo.save('/tmp/company_logo.png')

        worksheet.insert_image('A1:C1', '/tmp/company_logo.png')

        worksheet.merge_range('B4:E4', self.company_id.name, bold_format)
        worksheet.merge_range('B5:E5', self.company_id.street, data_format)
        worksheet.merge_range('B6:E6', self.company_id.country_id.name + ', ' + self.company_id.zip, data_format)
        worksheet.merge_range('B7:E7', self.company_id.phone, data_format)
        worksheet.merge_range('B8:D8', self.company_id.email or '', workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'underline': True, 'bg_color': '#B4C7E7', 'color': 'blue'}))

        worksheet.merge_range('F2:I2', 'MONTH ' + str(self.invoice_months) + '- LANDED COSTS', workbook.add_format(
            {'border': 1, 'bottom': False, 'border_color': 'red', 'align': 'center', 'valign': 'vcenter',
             'color': 'red', 'font_size': 15}))
        worksheet.merge_range('F3:I3', 'INVOICED AS SHIPMENTS', workbook.add_format(
            {'border': 1, 'top': False, 'bottom': False, 'border_color': 'red', 'align': 'center', 'valign': 'vcenter',
             'color': 'red', 'font_size': 15}))
        worksheet.merge_range('F4:I4', 'ARE RECEIVED', workbook.add_format(
            {'border': 1, 'top': False, 'border_color': 'red', 'align': 'center', 'valign': 'vcenter', 'color': 'red',
             'font_size': 15}))

        worksheet.merge_range('M2:R2', 'INBOUND SERVICE INVOICE', workbook.add_format(
            {'bold': 1, 'align': 'left', 'valign': 'vcenter', 'font_size': 18}))

        worksheet.merge_range('M4:N4', 'Invoice #', border_format)
        worksheet.merge_range('O4:P4', 'Date', border_format)
        worksheet.merge_range('Q4:R4', 'Due Date', border_format)

        worksheet.merge_range('M5:N5', self.name, data_border_format_1)
        worksheet.merge_range('O5:P5', datetime.strftime(self.invoice_date, "%d-%m-%Y"), data_border_format_1)
        worksheet.merge_range('Q5:R5', datetime.strftime(self.due_date, "%d-%m-%Y") if self.due_date else '',
                              data_border_format_1)

        worksheet.merge_range('B11:H11', 'BILL TO', border_grey_format)
        worksheet.merge_range('B12:H12', self.partner_id.name, workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'border': 1, 'bottom': False}))
        worksheet.merge_range('B13:H13', self.partner_id.street or '', border_bottom_format)
        worksheet.merge_range('B14:H14',
                              "{}, {}".format(self.partner_id.country_id.name or '', self.partner_id.zip or ''),
                              border_bottom_format)
        worksheet.merge_range('B15:H15', self.partner_id.email or '', workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'border': 1, 'top': False,
             'underline': True, 'bg_color': '#B4C7E7', 'color': 'blue'}))

        worksheet.merge_range('B17:C17', 'Your Item #', light_grey_format)
        worksheet.merge_range('D17:E17', 'Warefor #', light_grey_format)
        worksheet.merge_range('F17:G17', 'Charge', light_grey_format)
        worksheet.merge_range('H17:J17', 'Description', light_grey_format)
        worksheet.merge_range('K17:L17', 'Quantity', light_grey_format)
        worksheet.merge_range('M17:N17', 'UOM', light_grey_format)
        worksheet.merge_range('O17:P17', 'Unit Price', light_grey_format)
        worksheet.merge_range('Q17:R17', 'FOB', light_grey_format)
        worksheet.merge_range('S17:T17', 'Amount', light_grey_format)

        target_currency = self.company_id.currency_id
        row = 17
        column = 1
        fees_total = 0
        for rec in self.order_lines:
            qty = rec.qty
            uom = rec.product_id.uom_id.name
            if rec.is_exclude:
                product_price = formatLang(self.env, abs(rec.price), currency_obj=target_currency)
                unit_price = formatLang(self.env, abs(rec.unit_price), currency_obj=target_currency)
                total_price_string = 0
                charge = ''
            else:
                product_price = 0
                unit_price = formatLang(self.env, abs(round(rec.unit_price, 2)), currency_obj=target_currency)
                total_price = rec.price
                total_price_string = formatLang(self.env, abs(total_price), currency_obj=target_currency)
                charge = rec.product_id.default_code or ''
            worksheet.write(row, column, rec.product_id.name if rec.product_id else '', workbook.add_format(
                {'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'right': False}))
            worksheet.write(row, column + 1, '', data_border_format_2)
            worksheet.write(row, column + 2, '', data_border_format)
            worksheet.write(row, column + 3, '', data_border_format_2)
            worksheet.write(row, column + 4, charge, data_border_format)
            worksheet.write(row, column + 5, '', data_border_format_2)
            worksheet.write(row, column + 6, rec.name or rec.product_id.name or '', data_border_format)
            worksheet.write(row, column + 7, '', data_border_format_2)
            worksheet.write(row, column + 8, '', data_border_format_2)
            worksheet.write(row, column + 9, qty if qty else '', data_border_format)
            worksheet.write(row, column + 10, '', data_border_format_2)
            worksheet.write(row, column + 11, uom if uom else '', data_border_format)
            worksheet.write(row, column + 12, '', data_border_format_2)
            worksheet.write(row, column + 13, unit_price, data_border_format)
            worksheet.write(row, column + 14, '', data_border_format_2)
            worksheet.write(row, column + 15, product_price, data_border_format)
            worksheet.write(row, column + 16, '', data_border_format_2)
            worksheet.write(row, column + 17, total_price_string, data_border_format)
            worksheet.write(row, column + 18, '', workbook.add_format(
                {'border': 1, 'align': 'right', 'valign': 'vcenter', 'left': False}))

            row += 1
        fees_total = self.total_cost
        fees_total = formatLang(self.env, abs(fees_total), currency_obj=target_currency)
        total_name = 'M' + str(row + 1) + ':' + 'R' + str(row + 1)
        total = 'S' + str(row + 1) + ':' + 'T' + str(row + 1)

        worksheet.merge_range(total_name, 'Total Net Amount', workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1, 'right': False, 'bg_color': '#D0CECE'}))
        worksheet.merge_range(total, fees_total, workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'border': 1, 'left': False, 'bg_color': '#D0CECE'}))

        last_line = 'B' + str(row + 4) + ':' + 'S' + str(row + 4)
        worksheet.merge_range(last_line, '', workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1}))
        workbook.close()
        return file_name

    @api.model
    def create(self, vals):
        name = self._context.get('level_invoice')
        if not name:
            name = self.env['ir.sequence'].next_by_code('custom.invoice.sequence')
            if self.env.company.company_code:
                _logger.info("Custom invoice name:{}/{}".format(self.env.company.company_code, name))
                name = "{}/{}".format(self.env.company.company_code, name)
        vals['name'] = name
        res = super(CustomInvoice, self).create(vals)

        return res

    def create_attachment(self, file_name):
        """
        Delete file created in tmp dir, Delete old attachment and create attachment for download report
        :param file_name: file name string
        :return: attachment ir.attachment object
        """
        ir_attachment_obj = self.env['ir.attachment']

        # Read File data
        with open(file_name, "rb+") as file:
            file_data = base64.encodebytes(file.read())
            file.close()

        # Remove tmp file
        os.remove(file_name)

        # Delete Old Attachment
        attachments = ir_attachment_obj.search([('name', '=ilike', 'Invoice Report.xlsx'),
                                                ('res_model', '=', 'custom.invoice')])
        attachments and attachments.unlink()

        if "Storage" in file_name:
            file_name = 'Storage Invoice Report.pdf'
        else:
            file_name = 'Inbound Invoice Report.pdf'

        return ir_attachment_obj.create({
            'name': str(file_name),
            'datas': file_data,
            'res_model': 'custom.invoice',
            'type': 'binary'
        })

    # -----------------------------broker invoice ---------------
    def print_broker_invoice_report(self):
        # Prepare Excel Report
        try:
            report_file_name = self.prepare_broker_excel_report()
        except Exception as e:
            _logger.error(traceback.print_exc())
            return False

        # Create Attachment
        attachment = self.create_attachment(report_file_name)

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'download',
        }

    def prepare_broker_excel_report(self):

        file_name = '/tmp/Broker Invoice Report.xlsx'
        workbook = xlsxwriter.Workbook(file_name)
        worksheet = workbook.add_worksheet()
        worksheet.screen_gridlines = False
        transit_app_id = self.transit_app_id

        worksheet.set_landscape()

        worksheet.fit_to_pages(1, 0)
        worksheet.set_zoom(80)

        worksheet.set_column(0, 0, 2)

        worksheet.set_row(17, 40)

        bold_format = workbook.add_format(
            {'bold': 1, 'align': 'left', 'valign': 'vcenter'})

        border_format = workbook.add_format(
            {'bold': 1, 'align': 'center', 'valign': 'vcenter', 'border': 1})

        border_bottom_format = workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'border': 1, 'top': False, 'bottom': False})

        border_grey_format = workbook.add_format(
            {'bold': 1, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': '#D0CECE'})

        light_grey_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#D0CECE'})

        data_format = workbook.add_format(
            {'align': 'left', 'valign': 'vcenter'})

        data_border_format_1 = workbook.add_format(
            {'border': 1, 'align': 'center', 'valign': 'vcenter'})

        data_border_format = workbook.add_format(
            {'border': 1, 'valign': 'vcenter', 'right': False})

        data_border_format_2 = workbook.add_format(
            {'border': 1, 'left': False, 'right': False, 'align': 'center', 'valign': 'vcenter'})

        logo = base64.b64decode(self.company_id.logo)
        logo = BytesIO(logo)

        company_logo = Image.open(logo).resize((220, 60), Image.ANTIALIAS)
        company_logo.save('/tmp/company_logo.png')

        worksheet.insert_image('A1:C1', '/tmp/company_logo.png')

        worksheet.merge_range('B4:E4', self.company_id.name, bold_format)
        worksheet.merge_range('B5:E5', self.company_id.street, data_format)
        worksheet.merge_range('B6:E6', self.company_id.country_id.name + ', ' + self.company_id.zip, data_format)
        worksheet.merge_range('B7:E7', self.company_id.phone, data_format)
        worksheet.merge_range('B8:D8', self.company_id.email or '', workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'underline': True, 'bg_color': '#B4C7E7', 'color': 'blue'}))

        worksheet.merge_range('M2:R2', 'INVOICE', workbook.add_format(
            {'bold': 1, 'align': 'left', 'valign': 'vcenter', 'font_size': 18}))

        worksheet.merge_range('M4:N4', 'Invoice #', border_format)
        worksheet.merge_range('O4:P4', 'Date', border_format)

        worksheet.merge_range('M5:N5', self.name, data_border_format_1)
        worksheet.merge_range('O5:P5', datetime.strftime(self.invoice_date, "%d-%m-%Y") if self.invoice_date else '',
                              data_border_format_1)

        worksheet.merge_range('B11:H11', 'BILL TO', border_grey_format)
        worksheet.merge_range('B12:H12', self.partner_id.name, workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'border': 1, 'bottom': False}))
        worksheet.merge_range('B13:H13', self.partner_id.street or '', border_bottom_format)
        worksheet.merge_range('B14:H14',
                              "{}, {}".format(self.partner_id.country_id.name or '', self.partner_id.zip or ''),
                              border_bottom_format)
        worksheet.merge_range('B15:H15', self.partner_id.email or '', workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'border': 1, 'top': False,
             'underline': True, 'bg_color': '#B4C7E7', 'color': 'blue'}))

        worksheet.merge_range('B17:D17', 'SHIPPER/CONSIGNEE', light_grey_format)
        worksheet.merge_range('E17:G17', 'Entry Number', light_grey_format)
        worksheet.merge_range('H17:J17', 'B/L AWB No.', light_grey_format)
        worksheet.merge_range('K17:M17', 'Carrier/Flight', light_grey_format)
        worksheet.merge_range('N17:P17', 'ETS/ETD', light_grey_format)
        worksheet.merge_range('Q17:R17', 'ETA', light_grey_format)
        worksheet.merge_range('S17:U17', 'Entry Date', light_grey_format)

        row = 17
        column = 1

        shipper_name = transit_app_id.import_id and transit_app_id.import_id.name or ''
        worksheet.write(row, column, '', data_border_format)
        worksheet.write(row, column + 1, shipper_name, data_border_format_2)
        worksheet.write(row, column + 2, '', data_border_format_2)
        worksheet.write(row, column + 3, '', data_border_format)
        worksheet.write(row, column + 4, transit_app_id.entry_number or '', data_border_format_2)
        worksheet.write(row, column + 5, '', data_border_format_2)
        worksheet.write(row, column + 6, '', data_border_format)
        worksheet.write(row, column + 7, transit_app_id.awb_no or '', data_border_format_2)
        worksheet.write(row, column + 8, '', data_border_format_2)
        worksheet.write(row, column + 9, '', data_border_format)
        worksheet.write(row, column + 10, transit_app_id.carrier_flight or '', data_border_format_2)
        worksheet.write(row, column + 11, '', data_border_format_2)
        worksheet.write(row, column + 12, '', data_border_format)
        worksheet.write(row, column + 13, transit_app_id.date_shipping and str(transit_app_id.date_shipping) or '',
                        data_border_format_2)
        worksheet.write(row, column + 14, '', data_border_format_2)
        worksheet.write(row, column + 15,
                        transit_app_id.estimated_arrival_date and str(transit_app_id.estimated_arrival_date) or '',
                        data_border_format_2)
        worksheet.write(row, column + 16, '', data_border_format_2)
        worksheet.write(row, column + 17, '', data_border_format)
        worksheet.write(row, column + 18, transit_app_id.date_landing and str(transit_app_id.date_landing) or '',
                        data_border_format_2)
        worksheet.write(row, column + 19, '', workbook.add_format(
            {'border': 1, 'align': 'right', 'valign': 'vcenter', 'left': False}))

        worksheet.merge_range('B19:D19', 'ORIGIN PORT', light_grey_format)
        worksheet.merge_range('E19:G19', 'DESTINATION PORT', light_grey_format)
        worksheet.merge_range('H19:J19', 'FINAL DESTINATION', light_grey_format)
        worksheet.merge_range('K19:M19', 'NO OF CONTAINERS', light_grey_format)
        worksheet.merge_range('N19:R19', 'NO OF PCS', light_grey_format)
        worksheet.merge_range('S19:U19', '', workbook.add_format(
            {'border': 1, 'align': 'right', 'valign': 'vcenter', 'bottom': False, }))

        row = 19
        column = 1

        total_qty = sum(transit_app_id.purchase_orders_ids.mapped("order_line").mapped('product_uom_qty'))
        worksheet.write(row, column, '', data_border_format)
        worksheet.write(row, column + 1, transit_app_id.port_shipping_id.name or '', data_border_format_2)
        worksheet.write(row, column + 2, '', data_border_format_2)
        worksheet.write(row, column + 3, '', data_border_format)
        worksheet.write(row, column + 4, transit_app_id.port_discharge_id.name or '', data_border_format_2)
        worksheet.write(row, column + 5, '', data_border_format_2)
        worksheet.write(row, column + 6, '', data_border_format)
        worksheet.write(row, column + 7, transit_app_id.final_destination_id.name or '', data_border_format_2)
        worksheet.write(row, column + 8, '', data_border_format_2)
        worksheet.write(row, column + 9, '', data_border_format)
        worksheet.write(row, column + 10, transit_app_id.number_of_containers or '', data_border_format_2)
        worksheet.write(row, column + 11, '', data_border_format_2)
        worksheet.write(row, column + 12, '', data_border_format)
        worksheet.write(row, column + 13, '', data_border_format_2)
        worksheet.write(row, column + 14, total_qty or '', data_border_format_2)
        worksheet.write(row, column + 15, '', data_border_format_2)
        worksheet.write(row, column + 16, '', data_border_format_2)
        worksheet.write(row, column + 17, '', workbook.add_format(
            {'border': 1, 'align': 'right', 'valign': 'vcenter', 'right': False, 'top': False, }))
        worksheet.write(row, column + 18, '', workbook.add_format(
            {'border': 1, 'align': 'right', 'valign': 'vcenter', 'left': False, 'right': False, 'top': False, }))
        worksheet.write(row, column + 19, '', workbook.add_format(
            {'border': 1, 'align': 'right', 'valign': 'vcenter', 'left': False, 'top': False, }))

        worksheet.merge_range('B21:M21', 'DESCRIPTION', light_grey_format)
        worksheet.merge_range('N21:R21', 'WEIGHT', light_grey_format)
        worksheet.merge_range('S17:U17', 'Entry Date', light_grey_format)
        worksheet.merge_range('S21:U21', 'VOLUME', light_grey_format)

        row = 21
        column = 1

        worksheet.write(row, column, '', data_border_format)
        worksheet.write(row, column + 1, transit_app_id.notes or '', data_border_format_2)
        worksheet.write(row, column + 2, '', data_border_format_2)
        worksheet.write(row, column + 3, '', data_border_format_2)
        worksheet.write(row, column + 4, '', data_border_format_2)
        worksheet.write(row, column + 5, '', data_border_format_2)
        worksheet.write(row, column + 6, '', data_border_format_2)
        worksheet.write(row, column + 7, '', data_border_format_2)
        worksheet.write(row, column + 8, '', data_border_format_2)
        worksheet.write(row, column + 9, '', data_border_format_2)
        worksheet.write(row, column + 10, '', data_border_format_2)
        worksheet.write(row, column + 11, '', data_border_format_2)
        worksheet.write(row, column + 12, '', data_border_format)
        worksheet.write(row, column + 13, '', data_border_format_2)
        worksheet.write(row, column + 14, transit_app_id.weight or '', data_border_format_2)
        worksheet.write(row, column + 15, '', data_border_format_2)
        worksheet.write(row, column + 16, '', data_border_format_2)
        worksheet.write(row, column + 17, '', data_border_format)
        worksheet.write(row, column + 18, transit_app_id.volume or '', data_border_format_2)
        worksheet.write(row, column + 19, '', workbook.add_format(
            {'border': 1, 'align': 'right', 'valign': 'vcenter', 'left': False}))

        worksheet.merge_range('B27:C27', 'Code', light_grey_format)
        worksheet.merge_range('D27:M27', 'Description', light_grey_format)
        worksheet.merge_range('N27:O27', 'Amount', light_grey_format)

        row = 27
        column = 1
        total_cost = 0

        for rec in self.order_lines:
            worksheet.write(row, column, rec.product_id.default_code or '', data_border_format)
            worksheet.write(row, column + 1, '', data_border_format_2)
            worksheet.write(row, column + 2, '', data_border_format)
            worksheet.write(row, column + 3, '', data_border_format_2)
            worksheet.write(row, column + 4, '', data_border_format_2)
            worksheet.write(row, column + 5, '', data_border_format_2)
            worksheet.write(row, column + 6, rec.name or rec.product_id.name or '', data_border_format_2)
            worksheet.write(row, column + 7, '', data_border_format_2)
            worksheet.write(row, column + 8, '', data_border_format_2)
            worksheet.write(row, column + 9, '', data_border_format_2)
            worksheet.write(row, column + 10, '', data_border_format_2)
            worksheet.write(row, column + 11, '', data_border_format_2)
            worksheet.write(row, column + 12, rec.price, data_border_format)
            worksheet.write(row, column + 13, '', workbook.add_format(
                {'border': 1, 'align': 'right', 'valign': 'vcenter', 'left': False}))

            row += 1
        total_cost = self.total_cost
        total_name_broker = 'I' + str(row + 1) + ':' + 'M' + str(row + 1)
        total_brok = 'N' + str(row + 1) + ':' + 'O' + str(row + 1)

        worksheet.merge_range(total_name_broker, 'Total Net Amount', workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1, 'right': True, 'bg_color': '#D0CECE'}))
        worksheet.merge_range(total_brok, total_cost, workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1, 'left': False, 'bg_color': '#D0CECE'}))

        worksheet.merge_range('B34:U34', 'PO:', workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'border': 1, 'bottom': False, }))
        worksheet.merge_range('B35:U35', 'INV:', workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'border': 1, 'top': False, }))

        workbook.close()
        return file_name

    # -----------------------------wfl storage invoice ---------------

    def print_wfl_invoice_report(self):
        if self.invoice_type != 'wfl_storage':
            return False
        # Prepare Excel Report
        try:
            report_file_name = self.prepare_wfl_excel_report()
        except Exception as e:
            _logger.error(traceback.print_exc())
            return False

        # Create Attachment
        attachment = self.create_attachment(report_file_name)

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'download',
        }

    def print_wfl_invoice_pdf_report(self):
        if self.invoice_type != 'wfl_storage':
            return False
        # Prepare Excel Report
        try:
            report_file_name = self.prepare_wfl_excel_report()
            pdf_command = """soffice --headless --convert-to pdf:"impress_pdf_Export" {} --outdir /tmp/""".format(
                report_file_name)
            _logger.info("Starting-{}".format(pdf_command))
            os.system(pdf_command)
            _logger.info("Done-{}".format(pdf_command))
            pdf_report_file_name = report_file_name.replace('xlsx', 'pdf')
            # Remove tmp file
            _logger.info("Removing-{}".format(report_file_name))
            os.remove(report_file_name)
            _logger.info("Removed-{}".format(report_file_name))
        except Exception as e:
            _logger.error(traceback.print_exc())
            return False

        # Create Attachment
        attachment = self.create_attachment(pdf_report_file_name)
        if self._context.get('is_website_process'):
            return attachment

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'download',
        }

    def prepare_wfl_excel_report(self):
        file_name = '/tmp/WFLInvoiceStorageReport.xlsx'
        workbook = xlsxwriter.Workbook(file_name)
        worksheet = workbook.add_worksheet()
        worksheet.screen_gridlines = False

        worksheet.set_landscape()

        worksheet.fit_to_pages(1, 0)
        worksheet.set_zoom(80)

        worksheet.set_column(0, 0, 2)
        # worksheet.set_column(3, 3, 15)
        worksheet.set_column(7, 7, 20)
        worksheet.set_column(8, 8, 20)
        worksheet.set_column(10, 10, 2)
        worksheet.set_column(12, 12, 2)
        worksheet.set_column(14, 14, 2)

        worksheet.set_row(17, 30)
        worksheet.set_row(18, 30)

        bold_format = workbook.add_format(
            {'bold': 1, 'align': 'left', 'valign': 'vcenter'})

        border_format = workbook.add_format(
            {'bold': 1, 'align': 'center', 'valign': 'vcenter', 'border': 1})

        border_bottom_format = workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'border': 1, 'top': False, 'bottom': False})

        border_grey_format = workbook.add_format(
            {'bold': 1, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': '#D0CECE'})

        light_grey_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#D0CECE'})

        data_format = workbook.add_format(
            {'align': 'left', 'valign': 'vcenter'})

        data_border_format_1 = workbook.add_format(
            {'border': 1, 'align': 'center', 'valign': 'vcenter'})

        data_border_format = workbook.add_format(
            {'border': 1, 'valign': 'vcenter', 'right': False})

        data_border_format_2 = workbook.add_format(
            {'border': 1, 'left': False, 'right': False, 'align': 'center', 'valign': 'vcenter'})

        logo = base64.b64decode(self.company_id.logo)
        logo = BytesIO(logo)

        company_logo = Image.open(logo).resize((220, 60), Image.ANTIALIAS)
        company_logo.save('/tmp/company_logo.png')

        worksheet.insert_image('A1:C1', '/tmp/company_logo.png')

        worksheet.merge_range('B4:E4', self.company_id.name, bold_format)
        worksheet.merge_range('B5:E5', self.company_id.street, data_format)
        worksheet.merge_range('B6:E6', self.company_id.country_id.name + ', ' + self.company_id.zip, data_format)
        worksheet.merge_range('B7:E7', self.company_id.phone, data_format)
        worksheet.merge_range('B8:D8', self.company_id.email, workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'underline': True, 'bg_color': '#B4C7E7', 'color': 'blue'}))

        worksheet.merge_range('G2:I2', 'MONTH ' + str(self.invoice_months) + '- STORAGE FEES', workbook.add_format(
            {'border': 1, 'border_color': 'red', 'align': 'center', 'valign': 'vcenter',
             'color': 'red', 'font_size': 15}))

        worksheet.merge_range('M2:S2', 'STORAGE SERVICE INVOICE', workbook.add_format(
            {'bold': 1, 'align': 'left', 'valign': 'vcenter', 'font_size': 18}))

        worksheet.merge_range('M4:N4', 'Invoice #', border_format)
        worksheet.merge_range('O4:P4', 'Date', border_format)
        worksheet.merge_range('Q4:R4', 'Due Date', border_format)

        worksheet.merge_range('M5:N5', self.name, data_border_format_1)
        worksheet.merge_range('O5:P5', datetime.strftime(self.invoice_date, "%d-%m-%Y") if self.invoice_date else '',
                              data_border_format_1)
        worksheet.merge_range('Q5:R5', datetime.strftime(self.due_date, "%d-%m-%Y") if self.due_date else '',
                              data_border_format_1)

        worksheet.merge_range('B11:H11', 'BILL TO', border_grey_format)
        worksheet.merge_range('B12:H12', self.partner_id.name, workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'border': 1, 'bottom': False}))
        worksheet.merge_range('B13:H13', self.partner_id.street or '', border_bottom_format)
        worksheet.merge_range('B14:H14',
                              "{}, {}".format(self.partner_id.country_id.name or '', self.partner_id.zip or ''),
                              border_bottom_format)
        worksheet.merge_range('B15:H15', self.partner_id.email or '', workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'border': 1, 'top': False,
             'underline': True, 'bg_color': '#B4C7E7', 'color': 'blue'}))

        worksheet.merge_range('B17:C17', 'Your Item #', light_grey_format)
        worksheet.merge_range('D17:E17', 'Warefor #', light_grey_format)
        worksheet.merge_range('F17:G17', 'Charge', light_grey_format)
        worksheet.merge_range('H17:I17', 'Description', light_grey_format)
        worksheet.merge_range('J17:K17', 'Quantity', light_grey_format)
        worksheet.merge_range('L17:M17', 'UOM', light_grey_format)
        worksheet.merge_range('N17:O17', 'Unit Price', light_grey_format)
        worksheet.merge_range('P17:Q17', 'FOB', light_grey_format)
        worksheet.merge_range('R17:S17', 'Amount', light_grey_format)

        row = 17
        column = 1
        fees_total = 0
        for rec in self.order_lines:
            qty = rec.qty
            uom = rec.product_id.uom_id.name
            if rec.product_id.type != 'service':
                product_price = rec.price
                unit_price = 0
                total_price = 0
                charge = ''
            else:
                product_price = 0
                unit_price = rec.unit_price
                total_price = rec.price
                charge = rec.product_id.default_code or ''
            worksheet.write(row, column, '', workbook.add_format(
                {'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'right': False}))
            worksheet.write(row, column + 1, '', data_border_format_2)
            worksheet.write(row, column + 2, rec.pallet_name or '', data_border_format)
            worksheet.write(row, column + 3, '', data_border_format_2)
            worksheet.write(row, column + 4, charge, data_border_format)
            worksheet.write(row, column + 5, '', data_border_format_2)
            worksheet.write(row, column + 6, rec.name or rec.product_id.name or '', data_border_format)
            worksheet.write(row, column + 7, '', data_border_format_2)
            # worksheet.write(row, column + 8, '', data_border_format_2)
            worksheet.write(row, column + 8, qty if qty else '', data_border_format)
            worksheet.write(row, column + 9, '', data_border_format_2)
            worksheet.write(row, column + 10, uom if uom else '', data_border_format)
            worksheet.write(row, column + 11, '', data_border_format_2)
            worksheet.write(row, column + 12, round(rec.unit_price, 2), data_border_format)
            worksheet.write(row, column + 13, '', data_border_format_2)
            worksheet.write(row, column + 14, product_price, data_border_format)
            worksheet.write(row, column + 15, '', data_border_format_2)
            worksheet.write(row, column + 16, total_price, data_border_format)
            worksheet.write(row, column + 17, '', workbook.add_format(
                {'border': 1, 'align': 'right', 'valign': 'vcenter', 'left': False}))

            row += 1
        fees_total = self.total_cost
        total_name = 'K' + str(row + 1) + ':' + 'P' + str(row + 1)
        total = 'Q' + str(row + 1) + ':' + 'S' + str(row + 1)

        worksheet.merge_range(total_name, 'Total Net Amount', workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1, 'right': False, 'bg_color': '#D0CECE'}))
        worksheet.merge_range(total, round(fees_total, 2), workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1, 'left': False, 'bg_color': '#D0CECE'}))

        last_line = 'B' + str(row + 4) + ':' + 'S' + str(row + 4)
        worksheet.merge_range(last_line, '', workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1}))

        workbook.close()
        return file_name

    def print_wfl_invoice_level_a_report(self):
        if self.invoice_type != 'wfl_storage':
            return False
        # Prepare Excel Report
        try:
            report_file_name = self.prepare_wfl_excel_level_a_report()
        except Exception as e:
            _logger.error(traceback.print_exc())
            return False

        # Create Attachment
        attachment = self.create_attachment(report_file_name)

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'download',
        }

    def prepare_wfl_excel_level_a_report(self):
        file_name = '/tmp/WFLInvoiceStorageReport.xlsx'
        workbook = xlsxwriter.Workbook(file_name)
        worksheet = workbook.add_worksheet()
        worksheet.screen_gridlines = False

        worksheet.set_landscape()

        worksheet.fit_to_pages(1, 0)
        worksheet.set_zoom(80)

        worksheet.set_column(0, 0, 2)
        # worksheet.set_column(3, 3, 15)
        worksheet.set_column(7, 7, 20)
        worksheet.set_column(8, 8, 20)
        worksheet.set_column(10, 10, 2)
        worksheet.set_column(12, 12, 2)
        worksheet.set_column(14, 14, 2)

        worksheet.set_row(17, 30)
        worksheet.set_row(18, 30)

        bold_format = workbook.add_format(
            {'bold': 1, 'align': 'left', 'valign': 'vcenter'})

        border_format = workbook.add_format(
            {'bold': 1, 'align': 'center', 'valign': 'vcenter', 'border': 1})

        border_bottom_format = workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'border': 1, 'top': False, 'bottom': False})

        border_grey_format = workbook.add_format(
            {'bold': 1, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'bg_color': '#D0CECE'})

        light_grey_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#D0CECE'})

        data_format = workbook.add_format(
            {'align': 'left', 'valign': 'vcenter'})

        data_border_format_1 = workbook.add_format(
            {'border': 1, 'align': 'center', 'valign': 'vcenter'})

        data_border_format = workbook.add_format(
            {'border': 1, 'valign': 'vcenter', 'right': False})

        data_border_format_2 = workbook.add_format(
            {'border': 1, 'left': False, 'right': False, 'align': 'center', 'valign': 'vcenter'})

        logo = base64.b64decode(self.company_id.logo)
        logo = BytesIO(logo)

        company_logo = Image.open(logo).resize((220, 60), Image.ANTIALIAS)
        company_logo.save('/tmp/company_logo.png')

        worksheet.insert_image('A1:C1', '/tmp/company_logo.png')

        worksheet.merge_range('B4:E4', self.company_id.name, bold_format)
        worksheet.merge_range('B5:E5', self.company_id.street, data_format)
        worksheet.merge_range('B6:E6', self.company_id.country_id.name + ', ' + self.company_id.zip, data_format)
        worksheet.merge_range('B7:E7', self.company_id.phone, data_format)
        worksheet.merge_range('B8:D8', self.company_id.email, workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'underline': True, 'bg_color': '#B4C7E7', 'color': 'blue'}))

        worksheet.merge_range('G2:I2', 'MONTH ' + str(self.invoice_months) + '- STORAGE FEES', workbook.add_format(
            {'border': 1, 'border_color': 'red', 'align': 'center', 'valign': 'vcenter',
             'color': 'red', 'font_size': 15}))

        worksheet.merge_range('M2:S2', 'STORAGE SERVICE INVOICE', workbook.add_format(
            {'bold': 1, 'align': 'left', 'valign': 'vcenter', 'font_size': 18}))

        worksheet.merge_range('M4:N4', 'Invoice #', border_format)
        worksheet.merge_range('O4:P4', 'Date', border_format)
        worksheet.merge_range('Q4:R4', 'Due Date', border_format)

        worksheet.merge_range('M5:N5', self.name, data_border_format_1)
        worksheet.merge_range('O5:P5', datetime.strftime(self.invoice_date, "%d-%m-%Y") if self.invoice_date else '',
                              data_border_format_1)
        worksheet.merge_range('Q5:R5', datetime.strftime(self.due_date, "%d-%m-%Y") if self.due_date else '',
                              data_border_format_1)

        worksheet.merge_range('B11:H11', 'BILL TO', border_grey_format)
        worksheet.merge_range('B12:H12', self.partner_id.name, workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'border': 1, 'bottom': False}))
        worksheet.merge_range('B13:H13', self.partner_id.street or '', border_bottom_format)
        worksheet.merge_range('B14:H14',
                              "{}, {}".format(self.partner_id.country_id.name or '', self.partner_id.zip or ''),
                              border_bottom_format)
        worksheet.merge_range('B15:H15', self.partner_id.email or '', workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'border': 1, 'top': False,
             'underline': True, 'bg_color': '#B4C7E7', 'color': 'blue'}))

        worksheet.merge_range('B17:C17', 'Your Item #', light_grey_format)
        worksheet.merge_range('D17:E17', 'Warefor #', light_grey_format)
        worksheet.merge_range('F17:G17', 'Charge', light_grey_format)
        worksheet.merge_range('H17:I17', 'Description', light_grey_format)
        worksheet.merge_range('J17:K17', 'Quantity', light_grey_format)
        worksheet.merge_range('L17:M17', 'UOM', light_grey_format)
        worksheet.merge_range('N17:O17', 'Unit Price', light_grey_format)
        worksheet.merge_range('P17:Q17', 'FOB', light_grey_format)
        worksheet.merge_range('R17:S17', 'Amount', light_grey_format)

        row = 17
        column = 1
        fees_total = 0
        total_qty = 0
        storage_cost_ids = self.transit_app_id.storage_cost_ids
        if storage_cost_ids:
            product_id = storage_cost_ids.mapped('product_id')[0]
        else:
            return False
        fob_line = 0
        for rec in self.order_lines:
            if fob_line == 1:
                unit_price = round(self.total_cost / total_qty, 2)
                charge = product_id.default_code or ''
                uom = product_id.uom_id.name
                worksheet.write(row, column, '', workbook.add_format(
                    {'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'right': False}))
                worksheet.write(row, column + 1, '', data_border_format_2)
                worksheet.write(row, column + 2, '', data_border_format)
                worksheet.write(row, column + 3, '', data_border_format_2)
                worksheet.write(row, column + 4, charge, data_border_format)
                worksheet.write(row, column + 5, '', data_border_format_2)
                worksheet.write(row, column + 6, product_id.name or '', data_border_format)
                worksheet.write(row, column + 7, '', data_border_format_2)
                # worksheet.write(row, column + 8, '', data_border_format_2)
                worksheet.write(row, column + 8, total_qty or '', data_border_format)
                worksheet.write(row, column + 9, '', data_border_format_2)
                worksheet.write(row, column + 10, uom if uom else '', data_border_format)
                worksheet.write(row, column + 11, '', data_border_format_2)
                worksheet.write(row, column + 12, round(unit_price, 2), data_border_format)
                worksheet.write(row, column + 13, '', data_border_format_2)
                worksheet.write(row, column + 14, '', data_border_format)
                worksheet.write(row, column + 15, '', data_border_format_2)
                worksheet.write(row, column + 16, self.total_cost, data_border_format)
                worksheet.write(row, column + 17, '', workbook.add_format(
                    {'border': 1, 'align': 'right', 'valign': 'vcenter', 'left': False}))
                row += 1
                break
            else:
                fob_line += 1
                qty = rec.qty
                total_qty = qty
                uom = rec.product_id.uom_id.name
                if rec.product_id.type != 'service':
                    product_price = rec.price
                    unit_price = 0
                    total_price = 0
                    charge = ''
                else:
                    product_price = 0
                    unit_price = rec.unit_price
                    total_price = rec.price
                    charge = rec.product_id.default_code or ''
                worksheet.write(row, column, '', workbook.add_format(
                    {'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'right': False}))
                worksheet.write(row, column + 1, '', data_border_format_2)
                worksheet.write(row, column + 2, rec.pallet_name or '', data_border_format)
                worksheet.write(row, column + 3, '', data_border_format_2)
                worksheet.write(row, column + 4, charge, data_border_format)
                worksheet.write(row, column + 5, '', data_border_format_2)
                worksheet.write(row, column + 6, rec.name or rec.product_id.name or '', data_border_format)
                worksheet.write(row, column + 7, '', data_border_format_2)
                # worksheet.write(row, column + 8, '', data_border_format_2)
                worksheet.write(row, column + 8, qty if qty else '', data_border_format)
                worksheet.write(row, column + 9, '', data_border_format_2)
                worksheet.write(row, column + 10, uom if uom else '', data_border_format)
                worksheet.write(row, column + 11, '', data_border_format_2)
                worksheet.write(row, column + 12, round(rec.unit_price, 2), data_border_format)
                worksheet.write(row, column + 13, '', data_border_format_2)
                worksheet.write(row, column + 14, product_price, data_border_format)
                worksheet.write(row, column + 15, '', data_border_format_2)
                worksheet.write(row, column + 16, total_price, data_border_format)
                worksheet.write(row, column + 17, '', workbook.add_format(
                    {'border': 1, 'align': 'right', 'valign': 'vcenter', 'left': False}))

            row += 1
        fees_total = self.total_cost
        total_name = 'K' + str(row + 1) + ':' + 'P' + str(row + 1)
        total = 'Q' + str(row + 1) + ':' + 'S' + str(row + 1)

        worksheet.merge_range(total_name, 'Total Net Amount', workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1, 'right': False, 'bg_color': '#D0CECE'}))
        worksheet.merge_range(total, round(fees_total, 2), workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1, 'left': False, 'bg_color': '#D0CECE'}))

        last_line = 'B' + str(row + 4) + ':' + 'S' + str(row + 4)
        worksheet.merge_range(last_line, '', workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'border': 1}))

        workbook.close()
        return file_name

    def get_portal_url(self):
        portal_link = "%s/?db=%s" % (
            self.env['ir.config_parameter'].sudo().get_param('web.base.url'), self.env.cr.dbname)
        return portal_link


class CustomInvoiceLine(models.Model):
    _name = 'custom.invoice.line'
    _description = 'custom invoice line'

    product_id = fields.Many2one('product.product', string='Product')
    account_id = fields.Many2one('account.account', string='Account')
    invoice_id = fields.Many2one('custom.invoice', string='Invoice')
    name = fields.Char(string='Name')
    processing_cost = fields.Float(string='Processing Fees')
    qty = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom', string='UoM')
    price = fields.Float(string='Price', compute="_compute_price")
    unit_price = fields.Float(string='Unit Price')
    is_exclude = fields.Boolean("Is Exclude?", default=False)
    pallet_name = fields.Char("Pallet Name")

    @api.depends("unit_price", "qty")
    def _compute_price(self):
        for rec in self:
            rec.price = round(rec.qty, 8) * round(rec.unit_price, 8)
