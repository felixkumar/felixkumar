from odoo import fields, api, models
import base64
import io
from datetime import date
from odoo.tools.misc import xlsxwriter
from odoo.exceptions import ValidationError
import random


class AccountAssetsReport(models.TransientModel):
    _name = 'account.assets.report.wizard'
    _description = 'Assets Reports'

    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=True, )
    start_date = fields.Date('From Date', required=True)
    end_date = fields.Date('To Date', required=True)
    assets_category_ids = fields.Many2many(comodel_name="account.asset.category", string="Asset Category")
    detail_file = fields.Binary("File")

    def set_worksheet_column(self, worksheet):
        worksheet.set_column(0, 0, 23)
        worksheet.set_column(1, 1, 23)
        count = 2
        for i in range(300):
            worksheet.set_column(count, count, 23)
            count += 1

    def generate_xlsx_report(self):
        if self.end_date < self.start_date:
            self.end_date = date.today()
            raise ValidationError('Please select valid End date')
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        c_list = ['#E4F6AD', '#FFF49A', '#F9EBEB', '#D9A5F9	', '#FEF7E7', '#FEECA1', '#E2E095', '#E9FBA6', '#B4F297',
                  '#E8E9E2', '#8888FF']

        v_common_bg_style = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'center', 'bg_color': '#E4F6AD'})
        left_common_bg_style = workbook.add_format(
            {'bold': True, 'valign': 'vcenter', 'align': 'center', 'bg_color': '#c9ccd1', 'border': 1})
        blank_common_bg_style = workbook.add_format(
            {'bold': True, 'valign': 'vcenter', 'align': 'center', 'bg_color': '#F9EBEB', 'border': 1})
        sheet = workbook.add_worksheet("Sheet1")
        self.set_worksheet_column(sheet)
        col = 0
        row = 0
        sheet.merge_range(row, col, row + 1, col + 7, 'Assets Report', v_common_bg_style)
        row += 2
        col = 0
        sheet.write(row, col, 'From Date', left_common_bg_style)
        col += 1
        sheet.write(row, col, str(self.start_date), left_common_bg_style)
        col += 1
        sheet.write(row, col, '', left_common_bg_style)
        col += 1
        sheet.write(row, col, 'To Date', left_common_bg_style)
        col += 1
        sheet.write(row, col, str(self.end_date), left_common_bg_style)
        col += 1
        sheet.write(row, col, '', left_common_bg_style)
        col += 1
        sheet.write(row, col, 'Company Name', left_common_bg_style)
        col += 1
        sheet.write(row, col, self.company_id.name, left_common_bg_style)
        row += 1
        col = 0
        sheet.write(row, col, '', blank_common_bg_style)
        col += 1
        sheet.write(row, col, '', blank_common_bg_style)
        col += 1
        sheet.write(row, col, '', blank_common_bg_style)
        col += 1
        sheet.write(row, col, '', blank_common_bg_style)
        col += 1
        sheet.write(row, col, '', blank_common_bg_style)
        col += 1
        sheet.write(row, col, '', blank_common_bg_style)
        col += 1
        sheet.write(row, col, '', blank_common_bg_style)
        col += 1
        sheet.write(row, col, '', blank_common_bg_style)
        row += 1
        col = 0
        sheet.write(row, col, 'Category', left_common_bg_style)
        col += 1
        sheet.write(row, col, 'Date', left_common_bg_style)
        col += 1
        sheet.write(row, col, 'Reference', left_common_bg_style)
        col += 1
        sheet.write(row, col, 'Name', left_common_bg_style)
        col += 1
        sheet.write(row, col, 'Rate', left_common_bg_style)
        col += 1
        sheet.write(row, col, 'Addition', left_common_bg_style)
        col += 1
        sheet.write(row, col, 'Disposal', left_common_bg_style)
        col += 1
        sheet.write(row, col, 'Closing', left_common_bg_style)
        row += 1

        domain = self.prepare_domain()
        category_id = self.assets_category_ids
        if not category_id:
            category_id = self.env['account.asset.category'].search([('company_id', '=', self.company_id.id)])
        counter = 0
        color = []
        for i in range(len(category_id)):
            color.append(random.choice(c_list))
        color = color
        for category in category_id:
            record_list = []
            tot_list = []
            record_style = workbook.add_format(
                {'bold': False, 'align': 'left', 'border': 1, 'text_wrap': True,
                 'bg_color': '{}'.format(color.__getitem__(counter))})
            new_record_style = workbook.add_format(
                {'bold': True, 'align': 'left', 'border': 1, 'text_wrap': True,
                 'bg_color': '{}'.format(color.__getitem__(counter))})
            new_record_style_1 = workbook.add_format(
                {'bold': True, 'align': 'right', 'border': 1, 'text_wrap': True,
                 'bg_color': '{}'.format(color.__getitem__(counter))})
            temp_domain = domain + [('category_id', '=', category.id)]
            asset_id = self.env['account.asset.asset'].search(temp_domain)
            addition_total = 0
            disposal_total = 0
            closing_total = 0
            for asset in asset_id:
                rate = asset.method_progress_factor * 100
                addition = asset.value_residual
                disposal = sum(asset.depreciation_line_ids.mapped('amount'))
                closing = addition - disposal
                addition_total += round(addition, 2)
                disposal_total += round(disposal, 2)
                closing_total += round(closing, 2)
                record_list.append({
                    'category': asset.category_id.name,
                    'date': str(asset.date),
                    'ref': asset.code or '',
                    'name': asset.name,
                    'rate': str(str(rate) + " %") or '',
                    'addition': round(addition, 2),
                    'disposal': round(disposal, 2),
                    'closing': round(closing, 2),
                })
            for rec in record_list:
                rec = rec.values()
                col = 0
                for val in rec:
                    sheet.write(row, col, val, record_style)
                    col += 1
                row += 1
            if addition_total or disposal_total or closing_total:
                sheet.merge_range(row, 0, row, 4, 'Total', new_record_style_1)
                sheet.write(row, 5, addition_total, new_record_style)
                sheet.write(row, 6, disposal_total, new_record_style)
                sheet.write(row, 7, closing_total, new_record_style)
            if asset_id:
                row += 2

            counter += 1
        workbook.close()
        output.seek(0)

        output = base64.encodebytes(output.read())
        self.write({'detail_file': output})
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=account.assets.report.wizard&field=detail_file&download=true&id=%s&filename=Asset Report' % (
                self.id),
            'target': 'new',
        }

    def prepare_domain(self):
        domain = [('date', '>=', self.start_date), ('date', '<=', self.end_date)]
        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))
        return domain
