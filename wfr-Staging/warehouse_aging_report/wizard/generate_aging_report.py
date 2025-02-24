# -*- coding: utf-8 -*-
import base64
import io
import pandas as pd
import logging
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger("INVENTORY AGING REPORT")


class GenerateAgingReport(models.TransientModel):
    _name = "generate.aging.report"
    _description = "Generate Aging Report"

    warehouse_ids = fields.Many2many('stock.warehouse')
    categ_ids = fields.Many2many('product.category', string="Category")
    generate_for_all_category = fields.Boolean(string="Generate For All Category")

    def generate_report(self):
        # Create an in-memory bytes buffer to store the Excel file
        output = io.BytesIO()

        # Create an Excel writer object and add a worksheet
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Initialize workbook and worksheet
            workbook = writer.book

            fol_obj = self.env['freight.order.line']

            categ_ids = self.categ_ids

            if self.generate_for_all_category:
                categ_ids = self.env['product.category'].search([('is_use_on_aging_report', '=', True)])

            if not categ_ids:
                raise UserError(_('Please select product category'))

            if self.warehouse_ids:
                warehouses = self.warehouse_ids
            else:
                warehouses = self.env['stock.warehouse'].sudo().search([('is_use_on_report', '=', True)], limit=1)

            worksheet_generic = workbook.add_worksheet("All Warehouse")
            # Set title row for the sheet
            title = "Generic"
            title_format = workbook.add_format({
                'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'
            })
            worksheet_generic.set_row(0, 45)
            worksheet_generic.merge_range('A1:P1', title, title_format)
            worksheet_generic.set_row(1, 45)
            worksheet_generic.merge_range('A2:P2', "Inventory Aging for All Warehouse - {}".format(fields.Date.today()),
                                          title_format)

            # Write headers in row 1, starting from column A
            headers = [
                "SKU",
                "Name",
                "Product\nPer Pallet",
                "Inbound\nQuantity",
                "Returns &\nAdjustments",
                "Outbound\nQuantity",
                "Quantity\nOn Hand",
                "Pallet\nCount",
                "Turnover",
                "Last\nInbound",
                "Last\nOutbound",
                "0-30\nDays",
                "31-60\nDays",
                "61-90\nDays",
                "91-120\nDays",
                "120+\nDays"
            ]

            header_format = workbook.add_format({
                'bold': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True,
                'border': 1
            })

            worksheet_generic.set_row(2, 30)
            for col_num, header in enumerate(headers):
                worksheet_generic.write(2, col_num, header, header_format)

            worksheet_generic.set_column('A:A', 10)
            worksheet_generic.set_column('B:B', 45)
            worksheet_generic.set_column('C:C', 10)
            worksheet_generic.set_column('D:D', 10)
            worksheet_generic.set_column('E:E', 10)
            worksheet_generic.set_column('F:F', 10)
            worksheet_generic.set_column('G:G', 10)
            worksheet_generic.set_column('H:H', 8)
            worksheet_generic.set_column('I:I', 8)
            worksheet_generic.set_column('J:J', 20)
            worksheet_generic.set_column('K:K', 20)
            worksheet_generic.set_column('L:L', 12)
            worksheet_generic.set_column('M:M', 12)
            worksheet_generic.set_column('N:N', 12)
            worksheet_generic.set_column('O:O', 12)
            worksheet_generic.set_column('P:P', 12)

            generic_row_num = 3
            for warehouse in warehouses:
                for categ_id in categ_ids:
                    title = categ_id.name
                    worksheet = workbook.add_worksheet("{} - {}".format(warehouse.name, title))
                    title_format = workbook.add_format({
                        'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'
                    })
                    worksheet.set_row(0, 45)
                    worksheet.merge_range('A1:P1', title, title_format)
                    worksheet.set_row(1, 45)
                    worksheet.merge_range('A2:P2',
                                          "Inventory Aging for {} - {}".format(warehouse.name, fields.Date.today()),
                                          title_format)

                    worksheet.set_row(2, 30)
                    for col_num, header in enumerate(headers):
                        worksheet.write(2, col_num, header, header_format)

                    worksheet.set_column('A:A', 10)
                    worksheet.set_column('B:B', 45)
                    worksheet.set_column('C:C', 10)
                    worksheet.set_column('D:D', 10)
                    worksheet.set_column('E:E', 10)
                    worksheet.set_column('F:F', 10)
                    worksheet.set_column('G:G', 10)
                    worksheet.set_column('H:H', 8)
                    worksheet.set_column('I:I', 8)
                    worksheet.set_column('J:J', 20)
                    worksheet.set_column('K:K', 20)
                    worksheet.set_column('L:L', 12)
                    worksheet.set_column('M:M', 12)
                    worksheet.set_column('N:N', 12)
                    worksheet.set_column('O:O', 12)
                    worksheet.set_column('P:P', 12)
                    row_num = 3

                    _logger.info("******* CATEGORY {} *********".format(categ_id.name))
                    products = self.env['product.product'].search([('categ_id', '=', categ_id.id)])
                    for product in products:
                        fol_in_line_ids = fol_obj.search([('goods', '=', product.id), ('is_outbound', '!=', True),
                                                          ('warehouse_id', 'in', warehouse.ids)], order='id asc')
                        fol_out_line_ids = fol_obj.search([('goods', '=', product.id), ('is_outbound', '=', True),
                                                           ('warehouse_id', 'in', warehouse.ids)], order='id desc')

                        move_ids = self.env['stock.move.line'].search([('state', '=', 'done'),
                                                                       ('product_id', '=', product.id),
                                                                       ('location_id.usage', '=', 'customer'),
                                                                       ("picking_id.picking_type_id.code", "=",
                                                                        "incoming"),
                                                                       ("location_dest_id.warehouse_id", "in",
                                                                        warehouse.ids),
                                                                       ('company_id.is_logistics', '=', True)])

                        if fol_in_line_ids or fol_out_line_ids or move_ids:
                            total_qty_in = sum(fol_in_line_ids.mapped('total_quantity'))
                            total_qty_in_adj = sum(move_ids.mapped('qty_done'))
                            total_qty_out = sum(fol_out_line_ids.mapped('total_quantity'))
                            total_in = total_qty_in + total_qty_in_adj
                            on_hand = total_in - total_qty_out

                            if fol_in_line_ids:
                                fil_0_30 = fol_in_line_ids[0].create_date + timedelta(days=30)
                            else:
                                fil_0_30 = fields.Datetime.today()
                            # fl_1_in = fol_in_line_ids.filtered(lambda fl: fl.create_date <= fil_0_30)
                            # mv_1_in = move_ids.filtered(lambda mv: mv.date <= fil_0_30)
                            fl_1_out = fol_out_line_ids.filtered(lambda fl: fl.create_date <= fil_0_30)
                            range_1_out = sum(fl_1_out.mapped('total_quantity'))
                            range_1 = total_in - range_1_out

                            fil_31_60_st = fil_0_30 + timedelta(days=1)
                            fil_31_60 = fil_0_30 + timedelta(days=30)
                            # fl_2_in = fol_in_line_ids.filtered(
                            #     lambda fl: fl.create_date <= fil_31_60 and fl.create_date >= fil_31_60_st)
                            # mv_2_in = move_ids.filtered(lambda mv: mv.date <= fil_31_60 and mv.date >= fil_31_60_st)
                            fl_2_out = fol_out_line_ids.filtered(
                                lambda fl: fl.create_date <= fil_31_60 and fl.create_date >= fil_31_60_st)
                            range_2_out = sum(fl_2_out.mapped('total_quantity'))
                            range_2 = range_1 - range_2_out

                            fil_61_90_st = fil_31_60 + timedelta(days=1)
                            fil_61_90 = fil_31_60 + timedelta(days=30)
                            # fl_3_in = fol_in_line_ids.filtered(
                            #     lambda fl: fl.create_date <= fil_61_90 and fl.create_date >= fil_61_90_st)
                            # mv_3_in = move_ids.filtered(lambda mv: mv.date <= fil_61_90 and mv.date >= fil_61_90_st)
                            fl_3_out = fol_out_line_ids.filtered(
                                lambda fl: fl.create_date <= fil_61_90 and fl.create_date >= fil_61_90_st)
                            range_3_out = sum(fl_3_out.mapped('total_quantity'))
                            range_3 = range_2 - range_3_out

                            fil_91_120_st = fil_61_90 + timedelta(days=1)
                            fil_91_120 = fil_61_90 + timedelta(days=30)
                            # fl_4_in = fol_in_line_ids.filtered(
                            #     lambda fl: fl.create_date <= fil_91_120 and fl.create_date >= fil_91_120_st)
                            # mv_4_in = move_ids.filtered(lambda mv: mv.date <= fil_91_120 and mv.date >= fil_91_120_st)
                            fl_4_out = fol_out_line_ids.filtered(
                                lambda fl: fl.create_date <= fil_91_120 and fl.create_date >= fil_91_120_st)
                            range_4_out = sum(fl_4_out.mapped('total_quantity'))
                            range_4 = range_3 - range_4_out

                            fil_120_plus = fil_91_120 + timedelta(days=1)
                            # fl_5_in = fol_in_line_ids.filtered(lambda fl: fl.create_date >= fil_120_plus)
                            # mv_5_in = move_ids.filtered(lambda mv: mv.date >= fil_120_plus)
                            fl_5_out = fol_out_line_ids.filtered(lambda fl: fl.create_date >= fil_120_plus)
                            range_5_out = sum(fl_5_out.mapped('total_quantity'))
                            range_5 = range_4 - range_5_out

                            data_val = [product.default_code, product.name, product.product_per_pallet, total_qty_in,
                                        total_qty_in_adj, -total_qty_out, on_hand,
                                        round((total_qty_in + total_qty_in_adj) / (total_qty_out or 1), 2),
                                        round(1 - (on_hand / ((total_qty_in + total_qty_in_adj) or 1)), 2),
                                        fol_in_line_ids and str(fol_in_line_ids[-1].create_date.date()) or "",
                                        fol_out_line_ids and str(fol_out_line_ids[-1].create_date.date()) or "",
                                        range_1,
                                        range_2, range_3, range_4, range_5]
                            for col_num, value in enumerate(data_val):
                                worksheet_generic.write(generic_row_num, col_num, value)
                                worksheet.write(row_num, col_num, value)
                            generic_row_num += 1
                            row_num += 1

        # Create a base64-encoded file attachment in Odoo
        file_data = base64.b64encode(output.getvalue()).decode('utf-8')
        file_name = "Aging Report.xlsx"

        # Create an attachment in Odoo for the generated file
        attachment_id = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': file_data,
            'store_fname': file_name,
            'res_model': 'generate.aging.report',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })
        download_url = '/web/content/?model=ir.attachment&id={}&filename_field=name&field=datas&download=true&name={}'.format(
            attachment_id.id, attachment_id.name)
        action = {
            'type': 'ir.actions.act_url',
            'url': download_url,
            'target': 'new',
        }
        return action
