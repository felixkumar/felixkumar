from itertools import product

from odoo import fields, api, models
import base64
import io
from datetime import date
from odoo.tools.misc import xlsxwriter
from odoo.exceptions import ValidationError
from datetime import date, timedelta, datetime
import random


class SaleExtended(models.TransientModel):
    _name = 'container.report.wizard'
    _description = 'Container Report Wizard'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    detail_file = fields.Binary("File")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse")
    partner_id = fields.Many2one("res.partner", string="Customer")

    def set_worksheet_column(self, worksheet):
        worksheet.set_column(0, 0, 18)
        worksheet.set_column(1, 1, 18)

        worksheet.set_row(0, 30)
        worksheet.set_row(1, 20)
        count = 2
        for i in range(300):
            worksheet.set_column(count, count, 25)
            count += 1

    def generate_xlxs_report(self):
        if self.end_date < self.start_date:
            self.end_date = date.today()
            raise ValidationError('Please select valid end date')
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        left = workbook.add_format({'bold': False, 'align': 'left'})
        left_note = workbook.add_format({'bold': True, 'align': 'left'})
        center = workbook.add_format({'bold': False, 'align': 'center'})
        v_common_bg_style = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#c9ccd1'})
        left_common_bg_style = workbook.add_format({'bold': True, 'align': 'left', 'bg_color': '#c9ccd1'})
        center_common_bg_style = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#c9ccd1'})
        sheet = workbook.add_worksheet("Sheet1")
        self.set_worksheet_column(sheet)
        col = 0
        row = 0
        sheet.merge_range(row, col, row, col + 3, 'Warehouse Container Report', v_common_bg_style)
        row += 1
        col = 0
        sheet.write(row, col, 'Customer :', left_note)
        col += 1
        sheet.merge_range(row, col, row, col + 2, self.partner_id and self.partner_id.name or 'All', left)
        # row += 1
        # col = 0
        # sheet.write(row, col, 'From Date:', left_note)
        # col += 1
        # sheet.write(row, col, self.start_date.strftime('%m-%d-%Y'), left)
        # col += 1
        # sheet.write(row, col, 'To Date:', left_note)
        # col += 1
        # sheet.write(row, col, self.end_date.strftime('%m-%d-%Y'), left)
        row += 1
        col = 0
        sheet.write(row, col, 'Warehouse :', left_note)
        col += 1
        sheet.merge_range(row, col, row, col + 2, self.warehouse_id and self.warehouse_id.name or 'All', left)
        row += 1
        col = 0
        sheet.write(row, col, 'DATE', left_common_bg_style)
        col += 1
        sheet.write(row, col, 'UNLOADS', center_common_bg_style)
        col += 1
        sheet.write(row, col, 'DRAYED', center_common_bg_style)
        col += 1
        sheet.write(row, col, 'EMPTIES', center_common_bg_style)
        row += 1
        delta = self.end_date - self.start_date
        for i in range(delta.days + 1):
            col = 0
            day = self.start_date + timedelta(days=i)
            sheet.write(row, col, str(day), left)
            col += 1
            unload_count = self.get_unload_count(day)
            sheet.write(row, col, str(unload_count), center)
            col += 1
            drayed_count = self.get_drayed_count(day)
            sheet.write(row, col, str(drayed_count), center)
            col += 1
            empty_count = self.get_empties_count(day)
            sheet.write(row, col, str(empty_count), center)
            row += 1

        row += 1
        col = 0
        sheet.write(row, col, 'Notes :', left_note)
        row += 1
        col = 0
        sheet.merge_range(row, col + 1, row, col, 'Full containers to be processed: ', left)
        col += 1
        sheet.write(row, col, 'Notes :', left_note)

        workbook.close()
        output.seek(0)

        output = base64.b64encode(output.read())
        self.write({'detail_file': output})
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=container.report.wizard&field=detail_file&download=true&id=%s&filename=Warehouse Container Report' % (
                self.id),
            'target': 'new',
        }

    def get_unload_count(self, day=None):
        start_time = day.strftime('%Y-%m-%d 00:00:00')
        end_time = day.strftime('%Y-%m-%d 23:59:59')
        domain = [('unload_end_date', '!=', False), ('check_out_truck_yard', '>=', start_time),
                  ('check_out_truck_yard', '<=', end_time), ('active', 'in', [True, False])]
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.warehouse_id:
            domain.append(('warehouse_id', '=', self.warehouse_id.id))

        IBL = self.env['freight.freight'].search_count(domain)

        domain = [('loading_end_date', '!=', False), ('check_out_truck_yard', '>=', start_time),
                  ('check_out_truck_yard', '<=', end_time), ('active', 'in', [True, False])]
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.warehouse_id:
            domain.append(('warehouse_id', '=', self.warehouse_id.id))

        OBL = self.env['freight.freight'].search_count(domain)
        return IBL + OBL
        # return self.env['freight.freight'].search_count([('unload_end_date', '>=', start_time), ('unload_end_date', '<=', end_time),('check_out_truck_yard', '>=', start_time), ('check_out_truck_yard', '<=', end_time), ('is_outbound', '=', False)])

    def get_drayed_count(self, day=None):
        start_time = day.strftime('%Y-%m-%d 00:00:00')
        end_time = day.strftime('%Y-%m-%d 23:59:59')
        domain = [('check_in_truck_yard', '>=', start_time), ('check_in_truck_yard', '<=', end_time),
                  ('active', 'in', [True, False])]
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.warehouse_id:
            domain.append(('warehouse_id', '=', self.warehouse_id.id))

        IBL = self.env['freight.freight'].search_count(domain)

        domain = [('check_in_truck_yard', '>=', start_time), ('check_in_truck_yard', '<=', end_time),
                  ('active', 'in', [True, False])]
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.warehouse_id:
            domain.append(('warehouse_id', '=', self.warehouse_id.id))

        OBL = self.env['freight.freight'].search_count(domain)
        return IBL + OBL
        # return self.env['freight.freight'].search_count()

    def get_empties_count(self, day=None):
        start_time = day.strftime('%Y-%m-%d 00:00:00')
        end_time = day.strftime('%Y-%m-%d 23:59:59')
        domain = [('unload_end_date', '>=', start_time), ('unload_end_date', '<=', end_time),
                  ('check_out_truck_yard', '=', False), ('active', 'in', [True, False])]
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.warehouse_id:
            domain.append(('warehouse_id', '=', self.warehouse_id.id))

        IBL = self.env['freight.freight'].search_count(domain)

        domain = [('loading_end_date', '>=', start_time), ('loading_end_date', '<=', end_time),
                  ('check_out_truck_yard', '=', False), ('active', 'in', [True, False])]
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.warehouse_id:
            domain.append(('warehouse_id', '=', self.warehouse_id.id))

        OBL = self.env['freight.freight'].search_count(domain)
        return IBL + OBL
        # is_ibl = self.env['freight.freight'].search_count([('unload_end_date', '>=', start_time), ('unload_end_date', '<=', end_time),('check_out_truck_yard', '=', False)])
        # return self.env['freight.freight'].search_count([('unload_end_date', '>=', start_time), ('unload_end_date', '<=', end_time),('check_out_truck_yard', '=', False), ('is_outbound', '=', False)])

    # [('create_date', '&gt;=', datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')),('create_date', '&lt;=', datetime.datetime.now().strftime('%Y-%m-%d 23:59:59'))]
