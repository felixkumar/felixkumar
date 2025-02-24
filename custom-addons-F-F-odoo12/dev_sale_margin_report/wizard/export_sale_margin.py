# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo.tools.misc import xlwt
from io import BytesIO
from odoo import api, fields, models, _
from xlwt import easyxf
import base64
from datetime import date, datetime


class ExportSaleMargin(models.TransientModel):
    _name ='export.sale.margin'

    def print_pdf_sale_margin(self):
        return self.env.ref('dev_sale_margin_report.menu_sale_margin_report').report_action(self)

    def export_sale_margin_report(self):
        filename = 'Sale Margin Report.xls'
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sale Margin Report')

        # defining various font styles
        header_style = easyxf('font:height 430;pattern: pattern solid, fore_color 0x3F; align: horiz center;font:bold True;')
        sub_header = easyxf('font:height 210;pattern: pattern solid, fore_color silver_ega;font:bold True;align: horiz center;')
        content = easyxf('font:height 200;')
        content_center = easyxf('font:height 200;align: horiz center;')
        content_center_red = easyxf('font:height 200;align: horiz center;font: colour red;')
        content_red = easyxf('font:height 200;font: colour red;')
        content_right = easyxf('font:height 200;align: horiz right;', num_format_str='0.00')
        content_right_red = easyxf('font:height 200;align: horiz right;font: colour red;', num_format_str='0.00')
        content_date2 = easyxf('font:height 200;align: horiz center;')

        # setting with of the column
        worksheet.col(0).width = 60 * 60
        worksheet.col(1).width = 60 * 60
        worksheet.col(2).width = 60 * 60
        worksheet.col(3).width = 60 * 60
        worksheet.col(4).width = 60 * 60
        worksheet.col(5).width = 60 * 60
        worksheet.col(6).width = 60 * 60
        worksheet.col(7).width = 60 * 60
        worksheet.col(8).width = 65 * 65
        worksheet.col(9).width = 60 * 60
        worksheet.col(10).width = 60 * 60
        worksheet.col(11).width = 60 * 60
        worksheet.col(12).width = 60 * 60
        worksheet.col(13).width = 60 * 60
        worksheet.col(14).width = 60 * 60
        worksheet.col(15).width = 60 * 60
        worksheet.col(16).width = 60 * 60
        worksheet.col(17).width = 60 * 60

        worksheet.write_merge(1, 3, 1, 4, 'POS Report', header_style)

        # writing (Labels)
        worksheet.write(5,1,'From ', content_right)
        start = datetime.strptime(str(self.start_date), '%Y-%m-%d')
        start_date = start.strftime('%d/%m/%Y')
        worksheet.write(5,2,start_date, content_date2)
        worksheet.write(5,4,'To ', content_right)
        end = datetime.strptime(str(self.end_date), '%Y-%m-%d')
        end_date = end.strftime('%d/%m/%Y')
        worksheet.write(5,5,end_date, content_date2)
        worksheet.write_merge(7, 8, 0, 0, 'Ticket ', sub_header)
        worksheet.write_merge(7, 8, 1, 1, 'Fecha', sub_header)
        worksheet.write_merge(7, 8, 2, 2, 'Cliente', sub_header)
        worksheet.write_merge(7, 8, 3, 3, 'Producto', sub_header)
        worksheet.write_merge(7, 8, 4, 4, 'Referencia Interna', sub_header)
        worksheet.write_merge(7, 8, 5, 5, 'Color y Talla', sub_header)
        worksheet.write_merge(7, 8, 6, 6, 'Marca', sub_header)
        worksheet.write_merge(7, 8, 7, 7, 'Sub familia', sub_header)
        worksheet.write_merge(7, 8, 8, 8, 'Nombre de Caracteristicas', sub_header)
        worksheet.write_merge(7, 8, 9, 9, 'Genero', sub_header)
        worksheet.write_merge(7, 8, 10, 10, 'Cantidad', sub_header)
        worksheet.write_merge(7, 8, 11, 11, 'PVP', sub_header)
        worksheet.write_merge(7, 8, 12, 12, 'Precio con descuento', sub_header)
        worksheet.write_merge(7, 8, 13, 13, 'IVA', sub_header)
        worksheet.write_merge(7, 8, 14, 14, 'Cost', sub_header)
        worksheet.write_merge(7, 8, 15, 15, 'Proveedor', sub_header)
        worksheet.write_merge(7, 8, 16, 16, 'Cajero', sub_header)



        # content writing

        domain = [('state', 'in', ['sale','done']),
                  ('date_order', '>=', self.start_date),
                  ('date_order', '<=', self.end_date)]

        if self.user_ids:
            user_domain = ('user_id', 'in', self.user_ids.ids)
            domain.append(user_domain)

        sale_order_ids = self.env['pos.order'].search(domain)

        row_counter = 9
        if sale_order_ids:
            for sale_id in sale_order_ids:
                if sale_id.lines:
                    for line in sale_id.lines:
                        content_style = content
                        center_cell = content_center
                        decimal_right_content = content_right

                        worksheet.write(row_counter, 0, sale_id.name or '',  center_cell)
                        order_date = datetime.strptime(str(sale_id.date_order), "%Y-%m-%d %H:%M:%S").strftime('%d/%m/%Y')
                        worksheet.write(row_counter, 1, order_date or '',  center_cell)
                        worksheet.write(row_counter, 2, sale_id.partner_id.name or '',  content_style)
                        worksheet.write(row_counter, 3, line.full_product_name or '',  content_style)
                        worksheet.write(row_counter, 4, line.product_id.default_code or '',  content_style)
                        attribute_text=''
                        for attribute in  line.product_id.product_template_attribute_value_ids:
                            attribute_text += attribute.name+' ,'
                        worksheet.write(row_counter, 5, attribute_text or '',  content_style)
                        worksheet.write(row_counter, 6, line.product_id.x_marca or '',  content_style)
                        worksheet.write(row_counter, 7, line.product_id.categ_id.name or '',  content_style)
                        worksheet.write(row_counter, 8, line.product_id.x_caracteristicas or '',  content_style)
                        worksheet.write(row_counter, 9, line.product_id.x_genero or '',  content_style)

                        worksheet.write(row_counter, 10, line.qty or '',  decimal_right_content)
                        worksheet.write(row_counter, 11, line.product_id.lst_price or '',  content_style)
                        worksheet.write(row_counter, 12, line.price_subtotal_incl or '',  decimal_right_content)

                        tax_text=''
                        for tax in  line.tax_ids_after_fiscal_position:
                            tax_text += tax.name+' ,'
                        worksheet.write(row_counter, 13, tax_text or '',  content_style)
                        worksheet.write(row_counter, 14, line.product_id.standard_price or 0,  decimal_right_content)
                        worksheet.write(row_counter, 15, line.product_id.variant_seller_ids[0].name.name if line.product_id.variant_seller_ids else '',  content_style)
                        worksheet.write(row_counter, 16, sale_id.user_id.name or '',  content_style)

                        row_counter += 1

        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        excel_file = base64.encodestring(fp.read())
        fp.close()
        self.write({'excel_file': excel_file})
        active_id = self.ids[0]
        url = ('web/content/?model=export.sale.margin&download=true&field=excel_file&id=%s&filename=%s' % (active_id, filename))
        if self.excel_file:
            return {'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'new'}

    start_date = fields.Date(string="From", default=date.today(), required=True)
    end_date = fields.Date(string="To", default=date.today(), required=True)
    excel_file = fields.Binary(string='Excel File')
    user_ids = fields.Many2many('res.users', string='Salesperson')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: