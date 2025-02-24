from odoo import models, fields, api
from odoo.exceptions import ValidationError
class PartnerXlsx(models.AbstractModel):
    _name = 'report.naham_margin_report.margin_excel'
    _inherit = 'report.report_xlsx.abstract'


    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet('data')
        fromat1 = workbook.add_format({'border':2,'font_size':14,'align':'vcenter','bold':True})
        fromat2 = workbook.add_format({'border':1,'font_size':10,'align':'vcenter'})
        fromat3 = workbook.add_format({'border':2,'font_size':10,'align':'vcenter','bold':True})

        sheet.set_column(5, 5, 45)
        sheet.set_column(7, 7, 11)
        sheet.write('H1', 'رقم المستند', fromat1)
        sheet.write('G1', 'تاريخ التحرير', fromat1)
        sheet.write('F1', 'المنتج', fromat1)
        sheet.write('E1', 'الوحدة', fromat1)
        sheet.write('D1', 'الكمية', fromat1)
        sheet.write('C1', 'إجمالي البيع', fromat1)
        sheet.write('B1', 'إجمالي التكلفة', fromat1)
        sheet.write('A1', 'الربح', fromat1)

        domain = [
            ('move_id.state', '=', 'posted'),
            ('move_id.type', 'in', ['out_invoice', 'out_refund']),
            ('account_id.user_type_id.name', 'in',['Income']),
        ]
        if data['form']['product_ids']:
            domain.append(('product_id.id', 'in', data['form']['product_ids']))
        if data['form']['date_from']:
            domain.append(('move_id.invoice_date', '>=', data['form']['date_from']))
        if data['form']['date_to']:
            domain.append(('move_id.invoice_date', '<=', data['form']['date_to']))
        if data['form']['partner_id']:
            domain.append(('move_id.partner_id.id', '=', data['form']['partner_id'][0]))
        if data['form']['salesman_id']:
            domain.append(('move_id.invoice_user_id.id', '=', data['form']['salesman_id'][0]))
        print('---------------------------------------------')
        print(domain)
        # lines = self.env['account.move.line'].search(domain, order='product_id')
        lines = self.env['account.move.line'].search(domain)
        print(lines)
        lines_dict = []
        account_type_id = self.env.ref('account.data_account_type_direct_costs')
        total_total_price = 0.0
        total_total_cost = 0.0
        total_total_profit = 0.0
        total_quantity = 0.0
        row=1
        for line in lines:
                domain2 = [
                    ('move_id.id', '=', line.move_id.id),
                    ('exclude_from_invoice_tab', '=', True),
                    ('product_id.id', '=', line.product_id.id),
                    ('account_id.user_type_id.id', '=', account_type_id.id)
                ]
                move_type = line.move_id.type
                line_ids = self.env['account.move.line'].search(domain2)
                if move_type == 'out_invoice':
                    total_cost = sum(line_ids.mapped('debit')) or 0.0
                    quantity = sum(line.mapped('quantity')) or 0.0
                    total_price = sum(line.mapped('price_unit')) or 0.0

                else:
                    total_cost = sum(line_ids.mapped('credit')) or 0.0
                    total_cost *= -1
                    quantity = sum(line.mapped('quantity')) or 0.0
                    quantity *= -1
                    total_price = sum(line.mapped('price_unit')) or 0.0
                    total_price *= -1



                lines_dict.append({
                    'ref': line.move_id.name,
                    'invoice_date': line.move_id.invoice_date,
                    'product': line.product_id.name,
                    'uom': line.product_uom_id.name,
                    'quantity': line.quantity,
                    'total_price': line.price_unit * line.quantity,
                    'total_cost': total_cost,
                    'total_profit': round((line.price_unit * line.quantity) - total_cost, 2)
                })
                total_quantity += line.quantity
                total_total_price += line.price_unit * line.quantity
                total_total_cost += total_cost
                total_total_profit += (line.price_unit * line.quantity) - total_cost
                sheet.write(row, 7, line.move_id.name, fromat2)
                sheet.write(row, 6, str(line.move_id.invoice_date), fromat2)
                sheet.write(row, 5, line.product_id.name, fromat2)
                sheet.write(row, 4, line.product_uom_id.name, fromat2)
                sheet.write(row, 3, quantity, fromat2)
                sheet.write(row, 2, total_price * line.quantity, fromat2)
                sheet.write(row, 1, total_cost, fromat2)
                sheet.write(row, 0, round((total_price * line.quantity) - (total_cost), 2), fromat2)
                row += 1
        sheet.write(row, 3, round(total_quantity,2), fromat3)
        sheet.write(row, 2, round(total_total_price,2), fromat3)
        sheet.write(row, 1, round(total_total_cost,2), fromat3)
        sheet.write(row, 0, round(total_total_profit,2), fromat3)







