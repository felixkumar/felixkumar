# -*- coding: utf-8 -*-
import io
import base64
from datetime import datetime
from odoo.tools.misc import xlsxwriter
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import pytz


class IBLEmptyFUllContainerReportXlsx(models.AbstractModel):
    _name = 'report.warefor_3pl_tus.report_ibl_full_empty_xlsx_report'
    _description = 'IBL Empty FUll Container Report Xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def set_worksheet_column(self, worksheet):
        worksheet.set_column(0, 0, 7)
        worksheet.set_column(1, 4, 20)
        for i in range(300):
            if i != 3:
                worksheet.set_row(i, 25)
            else:
                worksheet.set_row(i, 30)

    def generate_xlsx_report(self, workbook, data, records):
        title_name = records.mapped('name') and records.mapped('name')[0] or ''
        filename = '{} - Inbound Full & Empty Containers - {}'.format(title_name.upper(), datetime.now(pytz.timezone('US/Central')).strftime('%m-%d-%Y %I%M %p'))
        left = workbook.add_format(
            {'font_size': 11, 'bold': True, 'align': 'center', 'color': '#4f86f7', 'valign': 'vcenter'})
        content = workbook.add_format({'font_size': 11, 'bold': False, 'align': 'center', 'valign': 'vcenter'})
        header = workbook.add_format({'font_size': 12, 'bold': True, 'valign': 'vcenter', 'align': 'center'})
        sheet = workbook.add_worksheet("Sheet1")
        self.set_worksheet_column(sheet)

        row, col = 0, 0
        sheet.merge_range(row, col, row, col + 4, title_name.upper(), workbook.add_format(
            {'font_size': 24, 'bold': True, 'valign': 'vcenter', 'align': 'center'}))
        row += 1
        sheet.merge_range(row, col, row, col + 4, 'Inbound Full & Empty Containers', workbook.add_format(
            {'font_size': 18, 'bold': True, 'valign': 'vcenter', 'align': 'center'}))
        row += 1
        sheet.write(row, col, 'Date :', workbook.add_format(
            {'font_size': 14, 'bold': False, 'valign': 'vcenter', 'align': 'center'}))
        sheet.merge_range(row, col + 1, row, col + 4,
                          datetime.now(pytz.timezone('US/Central')).strftime('%A, %B %d, %Y %I:%M %p'),
                          workbook.add_format(
                              {'font_size': 14, 'bold': False, 'align': 'left', 'color': '#4f86f7',
                               'valign': 'vcenter'}))
        row += 1
        header_list = ['#', 'Container #', 'Received \nDate', 'Unloaded \nDate', 'Status']
        for head in header_list:
            sheet.write(row, col, head, header)
            col += 1

        row += 1
        col = 0
        serial = 1
        for rec in records:
            sheet.write(row, col, serial, content)
            sheet.write(row, col + 1, rec.reference, content)
            sheet.write(row, col + 2,
                        rec.received_date and rec.received_date.strftime('%m/%d/%Y') or '', content)
            sheet.write(row, col + 3,
                        rec.unload_end_date and rec.unload_end_date.strftime('%m/%d/%Y') or '', content)
            sheet.write(row, col + 4, rec.status, left)

            row += 1
            serial += 1

        workbook.close()
        self.env.ref('warefor_3pl_tus.report_ibl_full_empty_container').report_file = filename



class InboundEmptyFullReport(models.Model):
    _name = 'inbound.empty.full.report'
    _description = 'Inbound Empty And Full Report'

    reference = fields.Char('Container')
    received_date = fields.Date('Received Date')
    unload_end_date = fields.Date('Unloaded Date')
    status = fields.Char('Status')
    name = fields.Char(string='name', invisible='1')
