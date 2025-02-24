# -*- coding: utf-8 -*-
import io
from io import BytesIO
import base64
from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.tools.misc import xlsxwriter
from odoo.tools.misc import formatLang
from PIL import Image


class StockPickingInherit(models.Model):
    _inherit = 'account.move'

    detail_file = fields.Binary("File")

    def set_worksheet_column(self, worksheet):
        worksheet.set_column(0, 0, 2)
        worksheet.set_column(1, 1, 2)
        count = 2
        for i in range(300):
            worksheet.set_column(count, count, 2)
            count += 1

    def export_custom_invoice_xlsx_report(self):
        """
        generate xlsx report
        :return:
        """

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Invoice")
        # sheet.add_format({'border': 0})

        merge_super_col_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 8, 'bold': True, 'align': 'center', 'border': 1, 'bg_color': '#b8b8b8'})
        line_data_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 8, 'align': 'center', 'border': 0})
        line_data_style_border = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 8, 'align': 'center', 'border': 0, 'border': 1})
        merge_super_col_style_left = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 8, 'bold': True, 'align': 'left', 'border': 1,
             'bg_color': '#b8b8b8'})
        line_data_style_left = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 8, 'align': 'left'})
        line_data_style_left_bold = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 8, 'align': 'left', 'bold': True})
        line_data_style_right = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 8, 'align': 'right'})
        undr_line = workbook.add_format({'border': 2,'left': False, 'right': False, 'top': False, 'bottom': True, 'bold': True})
        background_clr = workbook.add_format({'bg_color': '#FFF'})
        super_col_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#FFA500', 'bold': True})
        self.set_worksheet_column(sheet)



        # main header
        img = base64.b64decode(self.company_id.logo)
        img = BytesIO(img)
        company_logo = Image.open(img).resize((150, 50), Image.ANTIALIAS)
        company_logo.save('/tmp/company_img.png')

        sheet.merge_range('B1:AF1', '')
        sheet.insert_image('B2:I4', '/tmp/company_img.png')
        sheet.merge_range('B2:U4', '')

        row = 4
        col = 1
        sheet.merge_range(row, col, row, col + 19, self.company_id.partner_id.name, line_data_style_left_bold)
        row += 1
        sheet.merge_range(row, col, row, col + 19, self.company_id.partner_id.street, line_data_style_left)
        row += 1
        sheet.merge_range(row, col, row, col + 19, '{},{},{}'.format(self.company_id.partner_id.city,
                                                                     self.company_id.partner_id.state_id.code,
                                                                     self.company_id.partner_id.zip),
                          line_data_style_left)
        row += 1
        sheet.merge_range(row, col, row, col + 19, self.company_id.partner_id.phone, line_data_style_left)



        col = 21
        row = 1
        sheet.merge_range(row, col, row, col + 10, '', )
        row += 1
        sheet.merge_range(row, col, row, col + 10, 'INVOICE:', merge_super_col_style)

        row += 1
        col = 21
        sheet.merge_range(row, col, row, col + 10, '', )
        row += 1
        sheet.merge_range(row, col, row, col + 3, 'Invoice #:', line_data_style_left)
        col += 4
        sheet.merge_range(row, col, row, col + 6, self.name, line_data_style_left_bold)

        row += 1
        col = 21
        sheet.merge_range(row, col, row, col + 10, '', )
        row += 1
        sheet.merge_range(row, col, row, col + 3, 'Invoice Date:', line_data_style_left)
        col += 4
        sheet.merge_range(row, col, row, col + 6, self.invoice_date and self.invoice_date.strftime('%m/%d/%y'),
                          line_data_style_left_bold)

        row += 1
        col = 21
        sheet.merge_range(row, col, row, col + 10, '', )

        # Table Bill TO , Ship To
        row = 8
        col = 1
        sheet.merge_range(row, col, row, col + 30, '', undr_line)
        row += 1
        sheet.merge_range(row, col, row, col + 30, '', )
        row += 1
        sheet.merge_range(row, col, row, col + 14, 'BILL TO:', merge_super_col_style_left)
        col += 15
        sheet.write(row, col, '')
        col += 1
        sheet.merge_range(row, col, row, col + 14, 'SHIP TO:', merge_super_col_style_left)

        row_left = row
        row += 1
        col = 1
        partner_name = self.freight_id.partner_id and self.freight_id.partner_id[0] or self.partner_id
        sheet.merge_range(row, col, row, col + 14, partner_name.name, line_data_style_left_bold)
        # col += 1
        # sheet.write(row, col, '', line_data_style_left)
        if self.freight_id.partner_id:
            row += 1
            col = 1
            sheet.merge_range(row, col, row, col + 14, self.freight_id.partner_id.street or '', line_data_style_left)
            # row += 1
            # sheet.merge_range(row, col, row, col+14, self.freight_id.partner_id.street2 or '', line_data_style_left)
            row += 1
            sheet.merge_range(row, col, row, col + 14, '{},{},{}'.format(self.freight_id.partner_id.city,
                                                                         self.freight_id.partner_id.state_id.name,
                                                                         self.freight_id.partner_id.zip),
                              line_data_style_left)
            row += 1
            sheet.merge_range(row, col, row, col + 14, self.freight_id.partner_id.country_id.name or '',
                              line_data_style_left)
        else:
            row += 1
            sheet.merge_range(row, col, row, col + 14, self.partner_id.street or '', line_data_style_left)
            row += 1
            # sheet.merge_range(row, col, row, col+14, self.partner_id.street2 or '', line_data_style_left)
            # row += 1
            sheet.merge_range(row, col, row, col + 14,
                              '{},{},{}'.format(self.partner_id.city, self.partner_id.state_id, self.partner_id.zip),
                              line_data_style_left)
            row += 1
            sheet.merge_range(row, col, row, col + 14, self.freight_id.partner_id.country_id.name or '',
                              line_data_style_left)

        row = row_left
        if self.freight_id.outbound_partner_id:
            row += 1
            col = 17
            sheet.merge_range(row, col, row, col + 14, self.freight_id.outbound_partner_id.name or '',
                              line_data_style_left_bold)
            row += 1
            sheet.merge_range(row, col, row, col + 14, self.freight_id.outbound_partner_id.street, line_data_style_left)
            row += 1
            # sheet.merge_range(row, col, row, col+14, self.freight_id.outbound_partner_id.street2, line_data_style_left)
            # row += 1
            sheet.merge_range(row, col, row, col + 14, '{},{},{}'.format(self.freight_id.outbound_partner_id.city,
                                                                         self.freight_id.outbound_partner_id.state_id.name,
                                                                         self.freight_id.outbound_partner_id.zip),
                              line_data_style_left)
            row += 1
            sheet.merge_range(row, col, row, col + 14, self.freight_id.outbound_partner_id.country_id.name or '',
                              line_data_style_left)
        else:
            row += 1
            col = 17
            sheet.merge_range(row, col, row, col + 14, self.partner_shipping_id.name or '', line_data_style_left_bold)
            row += 1
            sheet.merge_range(row, col, row, col + 14, self.partner_shipping_id.street, line_data_style_left)
            row += 1
            # sheet.merge_range(row, col, row, col+14, self.partner_shipping_id.street2, line_data_style_left)
            # row += 1
            sheet.merge_range(row, col, row, col + 14,
                              '{},{},{}'.format(self.partner_shipping_id.city, self.partner_shipping_id.state_id.name,
                                                self.partner_shipping_id.zip), line_data_style_left)
            row += 1
            sheet.merge_range(row, col, row, col + 14, self.partner_shipping_id.country_id.name or '',
                              line_data_style_left)

        # Table 1
        row += 1
        col = 1
        sheet.merge_range(row, col, row, col + 30, '', )
        row += 1
        col = 1
        sheet.merge_range(row, col, row, col + 7, 'Customer Account#', merge_super_col_style)
        col += 8
        sheet.merge_range(row, col, row, col + 7, 'Customer Reference#', merge_super_col_style)
        col += 8
        sheet.merge_range(row, col, row, col + 7, 'Payment Terms', merge_super_col_style)
        col += 8
        sheet.merge_range(row, col, row, col + 6, 'Due Date', merge_super_col_style)

        for data in self:
            row += 1
            col = 1
            sheet.merge_range(row, col, row, col + 7, data.partner_id.id, line_data_style_border)
            col += 8
            sheet.merge_range(row, col, row, col + 7, data.freight_id.reference, line_data_style_border)
            col += 8
            sheet.merge_range(row, col, row, col + 7, data.invoice_payment_term_id.note or '', line_data_style_border)
            col += 8
            sheet.merge_range(row, col, row, col + 6,
                              data.invoice_date_due and data.invoice_date_due.strftime('%m/%d/%y'), line_data_style_border)

        # Table 2
        row += 1
        col = 1
        sheet.merge_range(row, col, row, col + 7, 'Customer PO#', merge_super_col_style)
        col += 8
        sheet.merge_range(row, col, row, col + 7, 'PO Date#', merge_super_col_style)
        col += 8
        sheet.merge_range(row, col, row, col + 7, 'Buyer Name', merge_super_col_style)
        col += 8
        sheet.merge_range(row, col, row, col + 6, 'Ship Date', merge_super_col_style)

        for data in self:
            row += 1
            col = 1
            sheet.merge_range(row, col, row, col + 7, data.freight_id.customer_po, line_data_style_border)
            col += 8
            sheet.merge_range(row, col, row, col + 7, '', line_data_style_border)
            col += 8
            sheet.merge_range(row, col, row, col + 7, self.partner_id.name, line_data_style_border)
            col += 8
            sheet.merge_range(row, col, row, col + 6,
                              data.freight_id.date_order and data.freight_id.date_order.strftime('%m/%d/%y'),
                              line_data_style_border)

        # Table 3 Invoice Line
        row += 1
        col = 1
        sheet.merge_range(row, col, row, col + 30, '', )
        row += 1
        col = 1
        sheet.merge_range(row, col, row, col + 1, 'line', merge_super_col_style)
        col += 2
        sheet.merge_range(row, col, row, col + 3, 'item #', merge_super_col_style)
        col += 4
        sheet.merge_range(row, col, row, col + 7, 'Description', merge_super_col_style_left)
        col += 8
        sheet.merge_range(row, col, row, col + 2, 'Quantity', merge_super_col_style)
        col += 3
        sheet.merge_range(row, col, row, col + 2, 'UOM', merge_super_col_style)
        col += 3
        sheet.merge_range(row, col, row, col + 3, 'Unit Price', merge_super_col_style)
        col += 4
        sheet.merge_range(row, col, row, col + 2, 'Taxes', merge_super_col_style)
        col += 3
        sheet.merge_range(row, col, row, col + 3, 'Total Price', merge_super_col_style)

        for rec in self:
            # row += 1
            counter = 1
            for line in rec.invoice_line_ids:
                row += 1
                col = 1
                sheet.merge_range(row, col, row, col + 1, counter, line_data_style)
                col += 2
                sheet.merge_range(row, col, row, col + 3, line.product_id.default_code, line_data_style)
                col += 4
                sheet.merge_range(row, col, row, col + 7, line.name, line_data_style_left)
                col += 8
                sheet.merge_range(row, col, row, col + 2, line.quantity, line_data_style_right)
                col += 3
                sheet.merge_range(row, col, row, col + 2, line.cost_uom, line_data_style)
                col += 3
                price_unit = formatLang(self.env, line.price_unit or 0.0, currency_obj=line.currency_id)
                sheet.merge_range(row, col, row, col + 3, price_unit, line_data_style_right)
                col += 4
                sheet.merge_range(row, col, row, col+2, line.tax_ids.mapped('name') or 'N/A', line_data_style)
                # sheet.merge_range(row, col, row, col + 2, 'Taxes', line_data_style_right)
                col += 3
                price_subtotal = formatLang(self.env, line.price_subtotal or 0.0, currency_obj=line.currency_id)
                sheet.merge_range(row, col, row, col + 3, price_subtotal, line_data_style_right)
                counter += 1
            row += 1

        # Notes
        row_diff = 43 - row
        col = 1
        sheet.merge_range(row, col, row + row_diff, col + 30, '', line_data_style_left)
        row += row_diff + 1
        col = 1
        sheet.merge_range(row, col, row, col + 22, 'Notes :', line_data_style_left)
        col += 23
        sheet.merge_range(row, col, row, col + 3, 'Sub Total :', line_data_style_left)
        col += 4
        amount_untaxed = formatLang(self.env, self.amount_untaxed or 0.0, currency_obj=line.currency_id)
        sheet.merge_range(row, col, row, col + 3, amount_untaxed, line_data_style_right)

        row += 1
        col = 1
        sheet.merge_range(row + 1, col, row, col + 22, self.narration or '', line_data_style_left)
        col += 23
        sheet.merge_range(row, col, row, col + 3, 'Taxes :', line_data_style_left)
        col += 4
        amount_tax = formatLang(self.env, self.amount_tax or 0.0, currency_obj=line.currency_id)
        sheet.merge_range(row, col, row, col + 3, amount_tax, line_data_style_right)

        row += 1
        col = 24
        sheet.merge_range(row, col, row, col + 3, 'Total :', line_data_style_left)
        col += 4
        amount_total = formatLang(self.env, self.amount_total or 0.0, currency_obj=line.currency_id)
        sheet.merge_range(row, col, row, col + 3, amount_total, line_data_style_right)

        workbook.close()
        output.seek(0)
        output = base64.encodestring(output.read())
        self.write({'detail_file': output})
        filename = "ul88_export_{}_{}.xlsx".format('back_order_products', datetime.now().strftime('%d_%m_%y-%H:%M:%S'))
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=account.move&field=detail_file&download=true&id=%s&filename=%s' % (
                self[0].id, filename),
            'target': 'new',
        }
