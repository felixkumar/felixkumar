# -*- coding: utf-8 -*-
import io
import base64
from datetime import datetime
from odoo.tools.misc import xlsxwriter
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import pytz


class InboundReportWizard(models.TransientModel):
    _name = 'inbound.report.wizard'
    _description = 'Inbound Report Wizard'

    partner_id = fields.Many2one("res.partner", string="Customer")
    title_name = fields.Char("Title")
    warehouse_ids = fields.Many2many('stock.warehouse', string="Warehouses")
    detail_file = fields.Binary("File")

    def set_worksheet_column(self, worksheet):
        worksheet.set_column(0, 0, 7)
        worksheet.set_column(1, 4, 20)
        for i in range(300):
            if i != 3:
                worksheet.set_row(i, 25)
            else:
                worksheet.set_row(i, 30)

    def get_ibl_empty_containers(self, domain):
        domain.append(('osd_rec_stage_id.name', '=', 'Processed (IB Empty/OB Loaded)'))
        records = self.env['freight.freight'].search(domain)
        domain.remove(('osd_rec_stage_id.name', '=', 'Processed (IB Empty/OB Loaded)'))
        if records:
            data = self.env['freight.freight'].search_read([('id', 'in', records.ids)],
                                                           fields=['check_in_truck_yard', 'reference',
                                                                   'unload_end_date',
                                                                   'osd_rec_stage_id'],
                                                           order='unload_end_date asc')
            [x.update({'status': 'EMPTY'}) for x in data]
            return data
        else:
            return False

    def get_ibl_full_containers(self, domain):
        full_domain = ['|', ('osd_rec_stage_id.name', '=', 'Checked In (IB Full) / Staged (OB)'),
                       ('osd_rec_stage_id.name', '=', 'In Process (Unloading/Loading)')]
        domain += full_domain
        records = self.env['freight.freight'].search(domain)
        [domain.remove(x) for x in full_domain if x in domain]
        if records:
            data = self.env['freight.freight'].search_read([('id', 'in', records.ids)],
                                                           fields=['check_in_truck_yard', 'reference',
                                                                   'unload_end_date',
                                                                   'osd_rec_stage_id'],
                                                           order='check_in_truck_yard asc')
            [x.update({'status': 'FULL'}) for x in data]
            return data
        else:
            return False

    def get_report_data(self):
        domain = [('partner_id', '=', self.partner_id.id), ('warehouse_id', 'in', self.warehouse_ids.ids),
                  ('is_outbound', '=', False)]
        data = []
        empty_data = self.get_ibl_empty_containers(domain)
        full_data = self.get_ibl_full_containers(domain)
        if not empty_data and not full_data:
            raise UserError(
                _("There is no Inbound Empty/Full Container found for customer {}.".format(self.partner_id.name)))
        else:
            if empty_data:
                data += empty_data
            if full_data:
                data += full_data
            return data

    def generate_ibl_full_empty_container_report(self):
        data = self.get_report_data()
        if data:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            left = workbook.add_format(
                {'font_size': 11, 'bold': True, 'align': 'center', 'color': '#4f86f7', 'valign': 'vcenter'})
            content = workbook.add_format({'font_size': 11, 'bold': False, 'align': 'center', 'valign': 'vcenter'})
            header = workbook.add_format({'font_size': 12, 'bold': True, 'valign': 'vcenter', 'align': 'center'})
            sheet = workbook.add_worksheet("Sheet1")
            self.set_worksheet_column(sheet)

            row, col = 0, 0
            sheet.merge_range(row, col, row, col + 4, self.title_name.upper(), workbook.add_format(
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
            for rec in data:
                sheet.write(row, col, serial, content)
                sheet.write(row, col + 1, rec.get('reference'), content)
                sheet.write(row, col + 2,
                            rec.get('check_in_truck_yard') and rec.get('check_in_truck_yard').astimezone(
                                pytz.timezone(self.env.user.tz)).strftime(
                                '%m/%d/%Y') or '', content)
                sheet.write(row, col + 3,
                            rec.get('unload_end_date') and rec.get('unload_end_date').astimezone(
                                pytz.timezone(self.env.user.tz)).strftime('%m/%d/%Y') or '',
                            content)
                sheet.write(row, col + 4, rec.get('status'), left)

                row += 1
                serial += 1

            workbook.close()
            output.seek(0)

            output = base64.encodebytes(output.read())
            self.write({'detail_file': output})

            return {
                'type': 'ir.actions.act_url',
                'url': 'web/content/?model=inbound.report.wizard&field=detail_file&download=true&id={}&filename={} - Inbound Full %26 Empty Containers - {}.xlsx'.format(
                    self.id, self.title_name.upper(),
                    datetime.now(pytz.timezone('US/Central')).strftime('%m-%d-%Y %I%M %p')),
                'target': 'new',
            }

    def view_report(self):
        self._cr.execute('DELETE FROM inbound_empty_full_report;')
        data = self.get_report_data()
        for rec in data:
            vals = {
                'reference': rec.get('reference'),
                'received_date': rec.get('check_in_truck_yard') and rec.get('check_in_truck_yard').date() or False,
                'unload_end_date': rec.get('unload_end_date') and rec.get('unload_end_date').date() or False,
                'status': rec.get('status'),
                'name': self.title_name,
            }
            self.env['inbound.empty.full.report'].create(vals)

        return {
            'name': _('{}- Inbound Full & Empty Containers-{}'.format(self.title_name.upper(), datetime.now(
                tz=pytz.timezone(self.env.user.tz)).strftime('%m-%d-%Y %I%M %p'))),
            'view_mode': 'tree',
            'res_model': 'inbound.empty.full.report',
            'view_id': False,
            'context': {'create': False, 'delete': False},
            'type': 'ir.actions.act_window',
        }
