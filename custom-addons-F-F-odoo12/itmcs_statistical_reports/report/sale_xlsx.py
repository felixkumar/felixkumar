from odoo import models, api
from datetime import datetime


class SaleReportXls(models.AbstractModel):
    _name = 'report.itmcs_statistical_reports.sale_report_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        report_records = data.get('record')['form']
        sheet = workbook.add_worksheet('Sale Info')
        company_header = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12,
                                        'bg_color': report_records['company_header_bgcolor'],'font_color': report_records['company_header_fontcolor']})
        report_header = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True,
                                        'bg_color': report_records['report_header_bgcolor'], 'font_size': 11,'font_color': report_records['report_header_fontcolor']})
        title_color= workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'bold': True ,
                                           'bg_color': report_records['title_bgcolor'],'font_color': report_records['title_fontcolor']})
        subtitle_color = workbook.add_format({'font_size': 10, 'bottom': True, 'right': True, 'left': True, 'top': True,'bold': True,  
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
        sheet.merge_range('A3:M3', 'Sale Margin Report', report_header)
        sheet.merge_range('A4:M4', "From " + start_date + " To " +end_date, report_header)
        rows = 6
        recs = [report_records]
        for report_record in recs:
            # if report_record['select_report'] == 'customer':
            #     sheet.merge_range(rows, 0, rows, 10, "Customer :" + report_record.get('context')[0].get('customer'), title_color)
            #
            #     rows += 1
            #
            #     sheet.write(
            #         rows, 0, "No", subtitle_color)
            #     sheet.write(rows, 1, "Sale Order", subtitle_color)
            #     sheet.write(rows, 2, "Product", subtitle_color)
            #     sheet.write(rows, 3, "Order Date", subtitle_color)
            #     sheet.write(rows, 4, "Customer", subtitle_color)
            #     sheet.write(rows, 5, "Warehouse", subtitle_color)
            #     sheet.write(rows, 6, "Sale Team", subtitle_color)
            #     sheet.write(rows, 7, "Salesperson", subtitle_color)
            #     sheet.write(rows, 8, "Cost", subtitle_color)
            #     sheet.write(rows, 9, "Price(Tax Excluded)", subtitle_color)
            #     sheet.write(rows, 10, "Discount", subtitle_color)
            #     sheet.write(rows, 11, "Margin", subtitle_color)
            #     sheet.write(rows, 12, "Margin (%)", subtitle_color)
            #     rows += 1
            #     rows = rows
            #     no = 1
            #     total= 0.0
            #     bill_total= 0.0
            #     for j in report_record.get('context')[0].get('product_data'):
            #         sheet.write(rows, 0, no, text_color)
            #         no += 1
            #         sheet.write(
            #             rows, 1, j.get('order'),  text_color)
            #         sheet.write(
            #             rows, 2, j.get('product_name') , text_color)
            #         sheet.write(
            #             rows, 3, j.get('date_order'), text_color)
            #         sheet.write(
            #             rows, 4, j.get('partner') , text_color)
            #         sheet.write_number(
            #             rows, 5, j.get('warehouse'), text_color)
            #         sheet.write_number(
            #             rows, 6,j.get('salesteam'),  text_color)
            #         sheet.write_number(
            #             rows, 7,j.get('salesperson') , text_color)
            #         sheet.write_number(
            #             rows, 8, j.get('cost_price') , text_color)
            #         sheet.write_number(
            #             rows, 9,j.get('bill_amount'), text_color)
            #         sheet.write_number(
            #             rows, 10,j.get('discount'), text_color)
            #
            #         sheet.write_number(
            #             rows, 11,j.get('discount'), text_color)
            #
            #         sheet.write_number(
            #             rows, 10, j.get('margin'), text_color)
            #         total+= j.get('gross_profit')
            #         bill_total+= j.get('bill_amount')
            #         rows += 1
            #     sheet.write(
            #             rows, 9, 'Total Gross Profit', subtitle_color)
            #     sheet.write_number(
            #             rows, 10,total, subtitle_color)
            #     rows += 1
            #     sheet.write(
            #             rows, 9, 'Total Bill Amount', subtitle_color)
            #     sheet.write_number(
            #             rows, 10, bill_total, subtitle_color)
            #     rows += 2
                rows += 1
                sheet.write(
                    rows, 0, "No", subtitle_color)
                sheet.write(rows, 1, "Sale Order", subtitle_color)
                sheet.write(rows, 2, "Product", subtitle_color)
                sheet.write(rows, 3, "Order Date", subtitle_color)
                sheet.write(rows, 4, "Customer", subtitle_color)
                sheet.write(rows, 5, "Warehouse", subtitle_color)
                sheet.write(rows, 6, "Sale Team", subtitle_color)
                sheet.write(rows, 7, "Salesperson", subtitle_color)
                sheet.write(rows, 8, "Cost", subtitle_color)
                sheet.write(rows, 9, "Price(Tax Excluded)", subtitle_color)
                sheet.write(rows, 10, "Discount", subtitle_color)
                sheet.write(rows, 11, "Margin", subtitle_color)
                sheet.write(rows, 12, "Margin (%)", subtitle_color)
                rows += 1
                rows = rows
                no = 1
                total= 0.0
                bill_total= 0.0
                prod_data = report_record.get('context')[0].get('product_data')
                for j in prod_data:
                    sheet.write(rows, 0, no, text_color)
                    no += 1
                    sheet.write(
                        rows, 1, j.get('order'), text_color)
                    sheet.write(
                        rows, 2, j.get('product_name'), text_color)
                    sheet.write(
                        rows, 3, j.get('date_order'), text_color)
                    sheet.write(
                        rows, 4, j.get('partner'), text_color)
                    sheet.write(
                        rows, 5, j.get('warehouse'), text_color)
                    sheet.write(
                        rows, 6, j.get('salesteam'), text_color)
                    sheet.write(
                        rows, 7, j.get('salesperson'), text_color)
                    sheet.write_number(
                        rows, 8, j.get('cost_price'), text_color)
                    sheet.write_number(
                        rows, 9, j.get('bill_amount'), text_color)
                    sheet.write_number(
                        rows, 10, j.get('discount'), text_color)
                    sheet.write_number(
                        rows, 11, j.get('margin_amnt'), text_color)
                    sheet.write_number(
                        rows, 12, j.get('margin'), text_color)
                    rows += 1


