from datetime import datetime
from odoo.http import request
from odoo import models, api


# cash ledger report xls file
class CashReportXls(models.AbstractModel):
    _name = 'report.itmcs_statistical_reports.cash_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        report_records = data.get('record')['form']
        account_obj = self.env['account.account']
        sheet = workbook.add_worksheet('Cash Info')
        company_header = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12,
                                        'bg_color': report_records['company_header_bgcolor'],'font_color': report_records['company_header_fontcolor']})
        report_header = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True,
                                        'bg_color': report_records['report_header_bgcolor'], 'font_size': 11,'font_color': report_records['report_header_fontcolor']})
        title_color= workbook.add_format({'font_size': 12, 'bottom': True, 'right': True, 'left': True, 'top': True, 'bold': True ,
                                           'bg_color': report_records['title_bgcolor'],'font_color': report_records['title_fontcolor']})
        subtitle_color = workbook.add_format({'font_size': 10, 'bottom': True, 'right': True, 'left': True, 'top': True,'bold' : True,
                                              'bg_color': report_records['subtitle_bgcolor'],'font_color': report_records['subtitle_fontcolor']})
        text_color = workbook.add_format({'font_size': 10, 'bottom': True, 'right': True, 'left': True, 'top': True,
                                              'bg_color': report_records['text_bgcolor'],'font_color': report_records['text_fontcolor']})
        report_header.set_align('center')
        company_header.set_align('center')
        title_color.set_align('center')
        subtitle_color.set_align('center')
        text_color.set_align('center')
        start_date = report_records['start_date']
        end_date = report_records['end_date']
        sheet.merge_range('A1:G1', "Company : " + report_records['company'], company_header)
        
        sheet.merge_range('A3:G3', 'Cash Ledger', report_header)
        sheet.merge_range('A4:G4', "From " + start_date + " To " + end_date, report_header)
        rows = 5
        sheet.write(rows, 0, "Opening Balance", title_color)
        sheet.write_number(
                    rows, 1, report_records.get('context')['opening_balance_receipt'],title_color)
        
        
        rows = 7
       
        sheet.write(rows, 0, "Receipt", title_color)
        rows += 1
        total= 0.0
        if report_records.get('context').get('receipt'):
            
            sheet.write(
                rows, 0, "Account Name", subtitle_color)
            sheet.write(rows, 1, "Amount", subtitle_color)
            sheet.write(rows, 2, "Balance", subtitle_color)
            rows += 1
            rows = rows
            for j in report_records.get('context'):
                account_name = account_obj.browse(j.get('account_id'))
                sheet.write(
                    rows, 0, account_name.name, text_color)
                sheet.write_number(
                    rows, 1, j.get('amount'), text_color)
                total+= j.get('amount')
                sheet.write_number(
                    rows, 2, total, text_color)
                 
                rows += 1
            sheet.write(
                        rows, 1, 'Total Receipt', subtitle_color)
            sheet.write_number(
                        rows, 2, total, subtitle_color)
        rows += 2
        sheet.write(rows, 0, "Payment", title_color)
        rows += 1
        total_payment= 0.0
        if report_records.get('context').get('payment'):
            sheet.write(
                rows, 0, "Account Name", subtitle_color)
            sheet.write(rows, 1, "Amount", subtitle_color)
            sheet.write(rows, 2, "Balance", subtitle_color)
            rows += 1
            rows = rows
            for j in report_records.get('payment'):
                account_name = account_obj.browse(j.get('account_id'))
                sheet.write(
                    rows, 0, account_name.name, text_color)
                sheet.write_number(
                    rows, 1, j.get('amount') , text_color)
                total_payment+= j.get('amount')
                sheet.write_number(
                    rows, 2, total_payment , text_color)
                 
                rows += 1
            sheet.write(
                        rows, 1, 'Total Payment', subtitle_color)
            sheet.write_number(
                        rows, 2, total, subtitle_color)
        rows += 2
        sheet.write(rows, 1, "Closing Balance", subtitle_color)
        sheet.write_number(
                    rows, 2, report_records.get('context')['closing_bal_payment'], subtitle_color)
