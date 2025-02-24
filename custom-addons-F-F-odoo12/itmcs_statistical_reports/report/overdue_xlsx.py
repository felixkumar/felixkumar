from datetime import datetime
from PIL import Image
from odoo import models, api


class OverdueReportXls(models.AbstractModel):
    _name = 'report.itmcs_statistical_reports.overdue_report_xlx'
    _inherit = 'report.report_xlsx.abstract'


    def generate_xlsx_report(self, workbook, data, lines):
        print(data,"===========================dfdffdfdfffffffffff")
        report_records = data.get('record')['form']
        partner_obj = self.env['res.partner']
        overdue_obj = self.env['overdue.report']
        sheet = workbook.add_worksheet('Overdue Info')
        company_header = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12,
                                        'bg_color': report_records['company_header_bgcolor'],'font_color': report_records['company_header_fontcolor']})
        report_header = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True,
                                        'bg_color': report_records['report_header_bgcolor'], 'font_size': 11,'font_color': report_records['report_header_fontcolor']})
        title_color= workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'bold': True ,
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
        start_date = datetime.strptime(report_records['start_date'], '%Y-%m-%d').strftime('%d/%m/%y')
        end_date = datetime.strptime(report_records['end_date'], '%Y-%m-%d').strftime('%d/%m/%y')
        sheet.insert_image('B2', 'images.jpg')
        sheet.merge_range('A1:G1', "Company : " + report_records['company'], company_header)
        if report_records['select_report'] == 'general':
            sheet.merge_range('A3:G3', 'General Due Sales Report', report_header)
        elif report_records['select_report'] == 'pos':
            sheet.merge_range('A3:G3', 'Pos Due Sales Report ', report_header)
        else:
            sheet.merge_range('A3:G3', 'Total Due SalesReport ', report_header)
        sheet.merge_range('A4:G4', "From " + start_date + " To " + end_date, report_header)
        
        rows = 5
        for report_record in report_records['context']:
            sheet.merge_range(rows, 0, rows, 5, "Customer :" + partner_obj.browse(report_record[0]).name, title_color)
            rows +=1
            sheet.write(rows, 1, "Customer Invoice", subtitle_color)
            sheet.write(rows, 2, "Overdue Amount", subtitle_color)
            overdue = overdue_obj.browse(report_record[1])
            rows += 1
            total= 0.0
            rows = rows
            for j in overdue:
                sheet.write(
                    rows, 1, j.ref, text_color)
                sheet.write_number(
                    rows, 2,  j.residual, text_color)
                total+= j.residual
                rows += 1
            sheet.write(
                        rows, 1, 'Total Amount', subtitle_color)
            sheet.write_number(
                        rows, 2,total, subtitle_color )
            rows += 2

            # {'context': {'tz': 'Europe/Brussels', 'uid': 2, 'xls_export': 1, 'active_model': 'overdue.wizard',
            #              'active_id': 4, 'active_ids': [4]},
            #  'data': '["/report/xlsx/itmcs_statistical_reports.overdue_report_xlx?options=%7B%22ids%22%3A%5B4%5D%2C%22model%22%3A%22overdue.wizard%22%2C%22record%22%3A%7B%22ids%22%3A%5B%5D%2C%22model%22%3A%22overdue.wizard%22%2C%22form%22%3A%7B%22id%22%3A4%2C%22partner_id%22%3A%5B14%2C%22Azure%20Interior%22%5D%2C%22start_date%22%3A%222022-09-01%22%2C%22end_date%22%3A%222022-09-30%22%2C%22select_report%22%3A%22total%22%2C%22context%22%3A%5B%5B14%2C%5B1%5D%5D%5D%2C%22company%22%3A%22YourCompany%22%2C%22company_header_bgcolor%22%3Afalse%2C%22company_header_fontcolor%22%3A%22%23000000%22%2C%22report_header_bgcolor%22%3Afalse%2C%22report_header_fontcolor%22%3Afalse%2C%22title_bgcolor%22%3Afalse%2C%22title_fontcolor%22%3Afalse%2C%22subtitle_bgcolor%22%3Afalse%2C%22subtitle_fontcolor%22%3Afalse%2C%22text_bgcolor%22%3Afalse%2C%22text_fontcolor%22%3Afalse%7D%7D%7D&context=%7B%22lang%22%3A%22en_US%22%2C%22tz%22%3A%22Europe%2FBrussels%22%2C%22uid%22%3A2%2C%22xls_export%22%3A1%2C%22active_model%22%3A%22overdue.wizard%22%2C%22active_id%22%3A4%2C%22active_ids%22%3A%5B4%5D%7D","xlsx"]',
            #  'token': 'dummy-because-api-expects-one', 'ids': [4], 'model': 'overdue.wizard',
            #  'record': {'ids': [], 'model': 'overdue.wizard',
            #             'form': {'id': 4, 'partner_id': [14, 'Azure Interior'], 'start_date': '2022-09-01',
            #                      'end_date': '2022-09-30', 'select_report': 'total', 'context': [[14, [1]]],
            #                      'company': 'YourCompany', 'company_header_bgcolor': False,
            #                      'company_header_fontcolor': '#000000', 'report_header_bgcolor': False,
            #                      'report_header_fontcolor': False, 'title_bgcolor': False, 'title_fontcolor': False,
            #                      'subtitle_bgcolor': False, 'subtitle_fontcolor': False, 'text_bgcolor': False,
            #                      'text_fontcolor': False}}}
