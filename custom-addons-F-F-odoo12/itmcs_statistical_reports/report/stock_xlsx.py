from odoo.addons.itmcs_statistical_reports.report.report_xlsx import ReportXlsx
from datetime import datetime

class StockReportXls(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, lines):
        report_records = data['form']['context']
        sheet = workbook.add_worksheet('Stock Info')
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
        sheet.merge_range('A1:J1', "Company : " + data['form']['company'], company_header)
        
        sheet.merge_range('A3:J3', 'Stock Analysis - Sales by warehouse', report_header)
        if data['form']['filter_date'] == 'duration':
            sheet.merge_range('A4:J4', "From " + start_date + " To " +end_date, report_header)
        
        else:
            sheet.merge_range('A4:J4', "Date: " + start_date, report_header)
        rows = 6
        
        for report_record in report_records:
            sheet.merge_range(rows, 0, rows, 9, "Warehouse :" + report_record.get('warehouse'), title_color)
            
            
            rows += 1
            if data['form']['choose_report'] == True:
                sheet.write(
                    rows, 0, "No", subtitle_color)
                sheet.write(rows, 1, "Product Code", subtitle_color)
                sheet.write(rows, 2, "Product Name", subtitle_color)
                sheet.write(rows, 3, "Unit", subtitle_color)
                sheet.write(rows, 4, "Opening Quantity", subtitle_color)
                sheet.write(rows, 5, "Quantity In", subtitle_color)
                sheet.write(rows, 6, "Quantity Out", subtitle_color)
                sheet.write(rows, 7, "Closing Quantity", subtitle_color)
                sheet.write(rows, 8, "Weighted Avg cost", subtitle_color)
                sheet.write(rows, 9, "Stock value", subtitle_color)
                rows += 1
                rows = rows
                no = 1
                total= 0.0
                for j in report_record.get('product_data'):
                    sheet.write(rows, 0, no, text_color)
                    no += 1
                    sheet.write(
                        rows, 1 , j.get('product_code'), text_color)
                    sheet.write(
                        rows, 2, j.get('product'), text_color)
                    sheet.write(
                        rows, 3, j.get('unit'), text_color)
                    sheet.write_number(
                        rows, 4, j.get('open_qty'), text_color)
                    sheet.write_number(
                        rows, 5, j.get('in_qty'), text_color)
                    sheet.write_number(
                        rows, 6, j.get('out_qty'), text_color)
                    sheet.write_number(
                        rows, 7,j.get('close_qty'), text_color)
                    sheet.write_number(
                        rows, 8,j.get('avg_cost') , text_color)
                    
                    sheet.write_number(
                        rows, 9, j.get('stock_value'), text_color)
                    total+= j.get('stock_value')
                    
                    rows += 1
                sheet.write(
                        rows, 8, 'Total', subtitle_color)
                sheet.write_number(
                        rows, 9, total, subtitle_color)
                rows += 2
            else:
                sheet.write(
                    rows, 0, "No", subtitle_color)
                sheet.write(rows, 1, "Product Code", subtitle_color)
                sheet.write(rows, 2, "Product Name", subtitle_color)
                sheet.write(rows, 3, "Unit", subtitle_color)
                sheet.write(rows, 4, "Closing Quantity", subtitle_color)
                sheet.write(rows, 5, "Weighted Avg cost", subtitle_color)
                sheet.write(rows, 6, "Stock value", subtitle_color)
                rows += 1
                rows = rows
                no = 1
                total= 0.0
                for j in report_record.get('product_data'):
                    sheet.write(rows, 0, no, text_color)
                    no += 1
                    sheet.write(
                        rows, 1 ,j.get('product_code') , text_color)
                    sheet.write(
                        rows, 2,j.get('product') , text_color)
                    sheet.write(
                        rows, 3, j.get('unit'), text_color)
                    sheet.write_number(
                        rows, 4,j.get('close_qty') , text_color)
                    sheet.write_number(
                        rows, 5,j.get('avg_cost') , text_color)
                    
                    sheet.write_number(
                        rows, 6, j.get('stock_value'), text_color)
                    total+= j.get('stock_value')
                    rows += 1
                
                sheet.write(
                        rows, 5, 'Total', subtitle_color)
                sheet.write_number(
                        rows, 6, total, subtitle_color)
                rows += 2
            
StockReportXls('report.itmcs_statistical_reports.stock_analysis.xlsx', 'custom.wizard')
