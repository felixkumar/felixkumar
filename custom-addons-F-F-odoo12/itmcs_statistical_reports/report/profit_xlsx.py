from odoo.addons.itmcs_statistical_reports.report.report_xlsx import ReportXlsx
from datetime import datetime

class ProfitReportXls(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, lines):
        report_records = data['form']['context']
        sheet = workbook.add_worksheet('Profit Info')
        company_header = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12,
                                        'bg_color': data['form']['company_header_bgcolor'],'font_color': data['form']['company_header_fontcolor']})
        report_header = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True,
                                        'bg_color': data['form']['report_header_bgcolor'], 'font_size': 11,'font_color': data['form']['report_header_fontcolor']})
        title_color= workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'bold': True ,
                                           'bg_color': data['form']['title_bgcolor'],'font_color': data['form']['title_fontcolor']})
        subtitle_color = workbook.add_format({'font_size': 10, 'bottom': True, 'right': True, 'left': True, 'top': True,'bold' : True,
                                              'bg_color': data['form']['subtitle_bgcolor'],'font_color': data['form']['subtitle_fontcolor']})
        text_color = workbook.add_format({'font_size': 10, 'bottom': True, 'right': True, 'left': True, 'top': True,  
                                              'bg_color': data['form']['text_bgcolor'],'font_color': data['form']['text_fontcolor']})
        report_header.set_align('center')
        company_header.set_align('center')
        title_color.set_align('center')
        subtitle_color.set_align('center')
        text_color.set_align('center')
        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').strftime('%d/%m/%y')
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').strftime('%d/%m/%y')
        sheet.merge_range('A1:G1', "Company : " + data['form']['company'], company_header)
        if data['form']['select_report'] == 'customer':
            sheet.merge_range('A3:G3', ' Profit  Analysis - Sales by Customer ', report_header)
        elif data['form']['select_report'] == 'product':
            sheet.merge_range('A3:G3', 'Profit Analysis - Sales by Product ', report_header)
        sheet.merge_range('A4:G4', "From " + start_date + " To " + end_date, report_header)
        
        
        rows = 7
        
        for report_record in report_records:
            if data['form']['select_report'] == 'customer':
                sheet.merge_range(rows, 0, rows, 6, "Customer :" + report_record.get('customer'), title_color)
            elif data['form']['select_report'] == 'product':
                sheet.merge_range(rows, 0, rows, 6, "Product :" + report_record.get('product'), title_color)
            rows += 1
            sheet.write(
                rows, 0, "No", subtitle_color)
            sheet.write(rows, 1, "Product Name", subtitle_color)
            sheet.write(rows, 2, "Quantity", subtitle_color)
            sheet.write(rows, 3, "Sale Price(Unit)", subtitle_color)
            sheet.write(rows, 4, "Cost Price(Unit)", subtitle_color)
            sheet.write(rows, 5, "Profit", subtitle_color)
            sheet.write(rows, 6, "Margin (%)", subtitle_color)

            rows += 1
            rows = rows
            no = 1
            total= 0.0
            for j in report_record.get('product_data'):
                sheet.write(rows, 0, no, text_color)
                no += 1
                sheet.write(
                    rows, 1, j.get('product_name') , text_color)
                sheet.write_number(
                    rows, 2, j.get('qty'), text_color)
                sheet.write_number(
                    rows, 3,j.get('sale_price') , text_color)
                sheet.write_number(
                    rows, 4, j.get('cost_price'), text_color)
                sheet.write_number(
                    rows, 5, j.get('gross_profit'), text_color)
                sheet.write_number(
                    rows, 6, j.get('margin') , text_color)
                total+= j.get('gross_profit')
                rows += 1
            sheet.write(
                        rows, 5, 'Total Gross Profit', subtitle_color)
            sheet.write_number(
                        rows, 6, total, subtitle_color)
            rows += 2
            
ProfitReportXls('report.itmcs_statistical_reports.profit_analysis.xlsx', 'profit.analysis.report')
