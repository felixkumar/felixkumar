from odoo import models, fields, api, _
from datetime import datetime
from xlsxwriter.utility import xl_rowcol_to_cell


class LocationReport(models.AbstractModel):
    _name = 'report.warefor_3pl_tus.report_empty_location'
    _description = 'Location Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        o = self.env['empty.location.report'].browse(docids)
        if o.product_id:
            quant_ids = self.env['stock.quant'].search([('product_id', '=', o.product_id.id), ('quantity', '>', 0),
                                                        ('company_id', 'in', o.company_id.ids)])
            location_ids = self.env['stock.location'].search(
                ["&", "&", ('usage', '=', 'internal'), ("complete_name", "ilike", "TPI"),
                 ("quant_ids", "=", False), ('company_id', '=', o.company_id.ids)])
            location_ids = location_ids - quant_ids.mapped('location_id')
            location_list = []
            location_dict = {}
            rec_list = []
            for rec in location_ids:
                rec_list.append(rec)
                if len(rec_list) == 3:
                    location_list.append(rec_list)
                    rec_list = []
            print('==========')
        return {
            'location': location_list,
        }


class EmptyLocationReportXlsx(models.AbstractModel):
    _name = 'report.warefor_3pl_tus.report_empty_location_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def set_worksheet_column(self, worksheet):
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 30)
        count = 2
        for i in range(10):
            worksheet.set_column(count, count, 20)
            count += 1

    def generate_xlsx_report(self, workbook, data, records):
        worksheet = workbook.add_worksheet('Location Information')
        bold_txt = workbook.add_format({'font_size': 11, 'bold': True, 'align': 'left', 'bg_color': '#bbbdbb'})
        comman_txt = workbook.add_format({'font_size': 11, 'align': 'left'})
        merge_format = workbook.add_format({'bold': 1, 'align': 'center', 'valign': 'vcenter', 'align': 'center'})
        total_monetary_format = workbook.add_format(
            {'align': 'right', 'bold': True})
        self.set_worksheet_column(worksheet)
        row = 0
        for o in records:
            worksheet.merge_range('A1:C2', 'Location Information', merge_format)
            row += 2
            column = 0
            worksheet.set_row(row, 30)
            worksheet.write(row, column, 'Name', bold_txt)
            column += 1
            worksheet.write(row, column, 'Product Stock', bold_txt)
            column += 1
            worksheet.write(row, column, '# Pallet', bold_txt)
            column += 1
            row += 1
            location_ids = self.env['stock.location'].search(
                ["&", "&", ('usage', '=', 'internal'), ("complete_name", "ilike", "TPI"),
                 ("quant_ids", "=", False), ('company_id', 'in', o.company_id.ids)])
            for rec in location_ids:
                column = 0
                quant_id = self.env['stock.quant'].search(
                    [('product_id', '=', o.product_id.id), ('company_id', 'in', o.company_id.ids),
                     ('location_id', '=', rec.id)])
                product_stock = sum(quant_id.mapped('quantity'))
                worksheet.write(row, column, rec.name, comman_txt)
                column += 1
                worksheet.write(row, column, product_stock if product_stock else 0, comman_txt)
                column += 1
                worksheet.write(row, column, rec.outbound_stored_pallet, comman_txt)
                row += 1


class EmptyLocationReport(models.TransientModel):
    _name = 'empty.location.report'
    _description = 'Empty Location Report'

    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=False, )
    company_id = fields.Many2many(comodel_name="res.company", string="Company")

    def print_report_pdf(self):
        return self.env.ref('warefor_3pl_tus.empty_location_report').report_action(self)

    def print_report_excel(self):
        return self.env.ref('warefor_3pl_tus.report_empty_location_excel').report_action(self)
