
import io
import xlsxwriter
import base64

from datetime import datetime
import pytz
from odoo import fields, models
from odoo.exceptions import UserError


class InventoryReport(models.TransientModel):
    _name = 'inventory.report.wizard'
    _description = 'Inventory Report Wizard'

    category_id = fields.Many2one(comodel_name='product.category', string="Product Category", required="1")
    partner_id = fields.Many2one(comodel_name='res.partner', string="Customer")
    title_name = fields.Char("Title", required="1")
    warehouse_ids = fields.Many2many(comodel_name='stock.warehouse', string="Warehouse", required="1")
    detail_file = fields.Binary("File")

    def _get_data(self):
        """ returns : List of dictionary of stock data for specific Warehouse"""
        product_ids = self.env['product.product'].search([('categ_id', '=', self.category_id.id)])
        if product_ids:
            quant_ids = self.env['stock.quant'].search([('warehouse_id', 'in', self.warehouse_ids.ids),
                                                        ('product_id', 'in', product_ids.ids)])
            products_list = []
            if quant_ids:
                products = quant_ids.mapped('product_id')
                for product in products:
                    product_quants = quant_ids.filtered(lambda x: x.product_id == product)
                    if product_quants and sum(product_quants.mapped('quantity')) > 0:
                        on_hand_quantity = sum(product_quants.mapped('quantity'))
                        available_quantity = sum(product_quants.mapped('available_quantity'))
                        diff_qty = on_hand_quantity - available_quantity
                        units_per_case = float(product.units_per_case or 0)
                        try:
                            on_hand_case = available_quantity / units_per_case
                        except ZeroDivisionError:
                            on_hand_case = 0
                        cartons_per_pallet = float(product.cartons_per_pallet or 0)
                        try:
                            # pallet_count = '{:0,.2f}'.format(float(on_hand_case / cartons_per_pallet or 0.00))
                            pallet_count = float('{:.2f}'.format(on_hand_case / cartons_per_pallet or 0.00))
                        except ZeroDivisionError:
                            pallet_count = 0.00
                        products_list.append({
                            'sku': product.default_code or '',
                            'name': product.name,
                            'on_hand_quantity': on_hand_quantity,
                            # 'available_quantity': '{:,d}'.format(available_quantity),
                            'available_quantity': f'{available_quantity:n}',
                            'diff_qty': diff_qty,
                            'units_per_case': units_per_case,
                            'on_hand_case': f'{on_hand_case:n}',
                            'cartons_per_pallet': cartons_per_pallet,
                            'pallet_stacking': product.pallet_stacking or '',
                            'pallet_count': pallet_count
                        })
            return products_list
        return False

    def set_worksheet_column(self, worksheet, row):
        """ Set the Column's width and Row's height for Excel sheet """
        worksheet.set_column(0, 0, 13)
        worksheet.set_column(1, 1, 55)
        worksheet.set_column(2, 2, 17)
        worksheet.set_column(3, 4, 15)
        worksheet.set_column(5, 5, 24)
        worksheet.set_column(6, 7, 15)

        for i in range(row):
            if i < 2:
                worksheet.set_row(i, 29)
            elif i == 2:
                worksheet.set_row(i, 33)
            else:
                worksheet.set_row(i, 15)

    def generate_xlsx_report(self):
        """  returns: Inventory Report  """
        products = self._get_data()
        if products:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            # Sheet Cell Styles
            content_center = workbook.add_format({'font_size': 11, 'align': 'center', 'valign': 'vcenter',
                                                  'border': 0})
            content_left = workbook.add_format({'font_size': 11, 'align': 'left', 'valign': 'vcenter',
                                                'border': 0, 'indent': 1})
            content_right = workbook.add_format({'font_size': 11, 'align': 'right', 'valign': 'vcenter',
                                                 'border': 0, 'indent': 1})

            header_center = workbook.add_format({'font_size': 11, 'valign': 'vcenter', 'align': 'center',
                                                 'border': 1, 'bg_color': '#d9d9d9'})
            header_left = workbook.add_format({'font_size': 11, 'valign': 'vcenter', 'align': 'left',
                                               'border': 1, 'bg_color': '#d9d9d9', 'indent': 1})
            sheet = workbook.add_worksheet(self.title_name.upper())
            row, col = 0, 0

            user_tz = self.env.user.tz or 'US/Central'
            date_string = 'As of %s' % datetime.now(pytz.timezone(user_tz)).strftime('%m/%d/%Y %I:%M')

            # For First 2 rows
            sheet.merge_range(row, col, row, col + 1, self.title_name.upper() + ' - Inventory Report',
                              workbook.add_format({'font_size': 16, 'bold': True, 'valign': 'vcenter', 'align': 'left',
                                                   'indent': 1}))
            row += 1
            sheet.merge_range(row, col, row, col + 1, date_string,
                              workbook.add_format({'font_size': 14, 'valign': 'vcenter', 'align': 'left',
                                                   'color': '#4f86f7', 'indent': 1}))
            row += 1

            # Header Row
            # headers = ['SKU', 'Description', 'On Hand \n(Units)', 'Available On Hand', 'Difference', 'Units per \nCase', 'On Hand \n(Cases)',
            #            'Footprint \n(TI/HI)', 'Cases per \nPallet', 'Pallet \nCount']
            headers = ['SKU', 'Description', 'Available On Hand', 'Units per \nCase',
                       'On Hand \n(Cases)', 'Footprint \n(TI/HI)', 'Cases per \nPallet', 'Pallet \nCount']
            for head in headers:
                if col < 2:
                    sheet.write(row, col, head, header_left)
                else:
                    sheet.write(row, col, head, header_center)

                col += 1

            row += 1
            col = 0
            # Sheet data
            for product in products:
                sheet.write(row, col, product['sku'], content_center)
                sheet.write(row, col + 1, product['name'], content_left)
                # sheet.write(row, col + 2, product['on_hand_quantity'], content_right)
                sheet.write(row, col + 2, product['available_quantity'], content_right)
                # sheet.write(row, col + 4, product['diff_qty'], content_right)
                sheet.write(row, col + 3, product['units_per_case'], content_right)
                sheet.write(row, col + 4, product['on_hand_case'], content_right)
                sheet.write(row, col + 5, product['pallet_stacking'], content_center)
                sheet.write(row, col + 6, product['cartons_per_pallet'], content_right)
                sheet.write(row, col + 7, product['pallet_count'], content_right)
                row += 1

            self.set_worksheet_column(sheet, row)

            # Filter for the data
            sheet.autofilter(2, 0, row-1, 7)

            workbook.close()
            output.seek(0)

            output = base64.encodebytes(output.read())
            self.write({'detail_file': output})
            return {
                'type': 'ir.actions.act_url',
                'url': 'web/content/?model=inventory.report.wizard&field=detail_file&download=true&id=%s&filename=%s - '
                       'Inventory as of %s' % (self.id, self.title_name.upper(),
                                               datetime.now(tz=pytz.timezone(user_tz)).strftime('%m-%d-%y %I%M%p')),
                'target': 'new',
            }
        else:
            raise UserError(f'Stock not found in %s.' % ','.join(f'{warehouse.name}' for warehouse in
                                                                            self.warehouse_ids))
