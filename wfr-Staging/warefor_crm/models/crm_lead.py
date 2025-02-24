# -*- coding: utf-8 -*-

import base64
import os
from io import BytesIO

import xlsxwriter
from PIL import Image
from odoo import models, fields


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    product_development_id = fields.Many2one('product.development', string="Product Development")
    product_id = fields.Many2one('product.product', string="Product")

    # Item Creation
    item_description = fields.Text(string="Item Description")
    item_number = fields.Integer(string="Items Number")
    item_upc = fields.Char(string="UPC")
    item_mfr_number = fields.Integer(string="MFR Item Number")
    item_mfr_name = fields.Char(string="MFR Item Name")
    item_customer_number = fields.Integer(string="Customer Item Number")
    item_customer_name = fields.Char(string="Customer Item Name")
    item_unit_of_sale = fields.Integer(string="Unit of Sale")
    item_cost = fields.Float(string="Cost")
    item_composition = fields.Binary(string="Composition")
    item_product_specifications = fields.Binary(string="Product Specifications")
    item_review_date = fields.Date(string="Review Date")
    item_approval_date = fields.Date(string="Approval Date")
    item_presentation_date = fields.Date(string="Presentation Date")
    item_minimum_order_qty = fields.Date(string="Minimum Order Quantity")
    production_starting_date = fields.Date(string="Production Starting Date")
    item_etd = fields.Char(string="ETD")
    item_eta = fields.Char(string="ETA")
    item_shipping_date = fields.Date(string="Shipping Date")
    in_store_date = fields.Date(string="In Store Date")

    # Product Dimensions
    item_length_in = fields.Float(string="Length(In)",  required=False, )
    item_length_cm = fields.Float(string="Length(Cm)",  required=False, )
    item_width_in = fields.Float(string="Width(In)",  required=False, )
    item_width_cm = fields.Float(string="Width(Cm)",  required=False, )
    item_height_in = fields.Float(string="Height(In)",  required=False, )
    item_height_cm = fields.Float(string="Height(Cm)",  required=False, )
    item_cube_in = fields.Float(string="Cube(In)",  required=False, )
    item_cube_cm = fields.Float(string="Cube(Cm)", required=False, )
    item_gross_wight_lbs = fields.Float(string="Gross Wight(Lbs)",  required=False, )
    item_gross_wight_kg = fields.Float(string="Gross Wight(Kg)",  required=False, )
    item_net_wight_lbs = fields.Float(string="Net Wight(lbs)",  required=False, )
    item_net_wight_kg = fields.Float(string="Net Wight(Kg)",  required=False, )

    # DS - Packaging Dimensions
    item_pack_length_in = fields.Float(string="Length(In)", required=False, )
    item_pack_length_cm = fields.Float(string="Length(Cm)", required=False, )
    item_pack_width_in = fields.Float(string="Width(In)", required=False, )
    item_pack_width_cm = fields.Float(string="Width(Cm)", required=False, )
    item_pack_height_in = fields.Float(string="Height(In)", required=False, )
    item_pack_height_cm = fields.Float(string="Height(Cm)", required=False, )
    item_pack_cube_ft = fields.Float(string="Cube(Ft3)", required=False, )
    item_pack_cube_m = fields.Float(string="Cube(m3)", required=False, )
    item_pack_gross_wight_lbs = fields.Float(string="Gross Wight(Lbs)", required=False, )
    item_pack_gross_wight_kg = fields.Float(string="Gross Wight(Kg)", required=False, )
    item_pack_net_wight_lbs = fields.Float(string="Net Wight(lbs)", required=False, )
    item_pack_net_wight_kg = fields.Float(string="Net Wight(Kg)", required=False, )

    # RETAIL - Packaging Dimensions
    item_retail_pack_length_in = fields.Float(string="Length(In)", required=False, )
    item_retail_pack_length_cm = fields.Float(string="Length(Cm)", required=False, )
    item_retail_pack_width_in = fields.Float(string="Width(In)", required=False, )
    item_retail_pack_width_cm = fields.Float(string="Width(Cm)", required=False, )
    item_retail_pack_height_in = fields.Float(string="Height(In)", required=False, )
    item_retail_pack_height_cm = fields.Float(string="Height(Cm)", required=False, )
    item_retail_pack_cube_ft = fields.Float(string="Cube(Ft3)", required=False, )
    item_retail_pack_cube_m = fields.Float(string="Cube(m3)", required=False, )
    item_retail_pack_gross_wight_lbs = fields.Float(string="Gross Wight(Lbs)", required=False, )
    item_retail_pack_gross_wight_kg = fields.Float(string="Gross Wight(Kg)", required=False, )
    item_retail_pack_net_wight_lbs = fields.Float(string="Net Wight(lbs)", required=False, )
    item_retail_pack_net_wight_kg = fields.Float(string="Net Wight(Kg)", required=False, )

    def create_product_dev(self):
        for rec in self:
            pro_development = self.env['product.development'].create({
                'product_id': rec.product_id.id,
            })
            rec.product_development_id = pro_development.id

    def print_pd_report(self):
        # Get Report Data
        report_data = self.get_report_data()

        # Prepare Excel Report
        report_file_name = self.prepare_excel_report(report_data)

        # Create Attachment
        attachment = self.create_attachment(report_file_name)

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'download',
        }

    def get_report_data(self):
        return []

    def prepare_excel_report(self, report_data):
        file_name = '/tmp/pd_report.xlsx'
        workbook = xlsxwriter.Workbook(file_name)
        worksheet = workbook.add_worksheet()
        worksheet.screen_gridlines = False

        worksheet.set_landscape()

        worksheet.fit_to_pages(1, 0)
        worksheet.set_zoom(80)

        worksheet.set_column(0, 0, 2)
        worksheet.set_column(1, 1, 2)
        worksheet.set_column(2, 2, 2)
        worksheet.set_column(3, 3, 2)
        worksheet.set_column(4, 4, 2)
        worksheet.set_column(5, 5, 2)
        worksheet.set_column(6, 6, 2)
        worksheet.set_column(7, 7, 2)
        worksheet.set_column(8, 8, 2)
        worksheet.set_column(9, 9, 2)
        worksheet.set_column(10, 10, 2)
        worksheet.set_column(11, 11, 2)
        worksheet.set_column(12, 12, 2)
        worksheet.set_column(13, 13, 2)
        worksheet.set_column(14, 14, 2)
        worksheet.set_column(15, 15, 2)
        worksheet.set_column(16, 16, 2)
        worksheet.set_column(17, 17, 2)
        worksheet.set_column(18, 18, 2)
        worksheet.set_column(19, 19, 2)
        worksheet.set_column(20, 20, 2)

        worksheet.set_column(21, 21, 2)
        worksheet.set_column(22, 22, 2)
        worksheet.set_column(23, 23, 2)
        worksheet.set_column(24, 24, 2)
        worksheet.set_column(25, 25, 2)
        worksheet.set_column(26, 26, 2)
        worksheet.set_column(27, 27, 2)
        worksheet.set_column(28, 28, 2)
        worksheet.set_column(29, 29, 2)
        worksheet.set_column(30, 30, 2)

        worksheet.set_column(32, 32, 2)
        worksheet.set_column(32, 32, 2)
        worksheet.set_column(33, 33, 2)
        worksheet.set_column(34, 34, 2)
        worksheet.set_column(35, 35, 2)
        worksheet.set_column(36, 36, 2)
        worksheet.set_column(37, 37, 2)
        worksheet.set_column(38, 38, 2)
        worksheet.set_column(39, 39, 2)
        worksheet.set_column(40, 40, 2)

        worksheet.set_column(41, 41, 2)
        worksheet.set_column(42, 42, 2)
        worksheet.set_column(43, 43, 2)
        worksheet.set_column(44, 44, 2)
        worksheet.set_column(45, 45, 2)
        worksheet.set_column(46, 46, 2)
        worksheet.set_column(47, 47, 2)
        worksheet.set_column(48, 48, 2)
        worksheet.set_column(49, 49, 2)
        worksheet.set_column(50, 50, 2)

        worksheet.set_column(51, 51, 2)
        worksheet.set_column(52, 52, 2)
        worksheet.set_column(53, 53, 2)
        worksheet.set_column(54, 54, 2)
        worksheet.set_column(55, 55, 2)
        worksheet.set_column(56, 56, 2)
        worksheet.set_column(57, 57, 2)
        worksheet.set_column(58, 58, 2)
        worksheet.set_column(59, 59, 2)
        worksheet.set_column(60, 60, 2)

        worksheet.set_column(61, 61, 2)
        worksheet.set_column(62, 62, 2)
        worksheet.set_column(63, 63, 2)
        worksheet.set_column(64, 64, 2)

        worksheet.set_row(0, 40)
        worksheet.set_row(1, 30)
        worksheet.set_row(7, 30)
        worksheet.set_row(8, 25)
        worksheet.set_row(41, 25)
        worksheet.set_row(51, 40)
        worksheet.set_row(55, 25)
        worksheet.set_row(72, 30)
        worksheet.set_row(87, 40)
        worksheet.set_row(91, 25)
        worksheet.set_row(106, 20)
        worksheet.set_row(116, 20)

        first_row_format_tt = workbook.add_format(
            {'bold': 1, 'font_size': 18, 'font': 'Calibri Light', 'bottom': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFFFF'})
        first_row_format = workbook.add_format(
            {'bold': 1, 'border': 1, 'left': False, 'font_size': 18, 'font': 'Calibri Light', 'align': 'center',
             'valign': 'vcenter', 'bg_color': '#FFFFFF'})
        blue_format_top = workbook.add_format(
            {'bold': 1, 'top': True, 'align': 'center', 'valign': 'vcenter', 'color': 'blue'})
        blue_format = workbook.add_format(
            {'bold': 1, 'align': 'center', 'valign': 'vcenter', 'color': 'blue'})
        blue_format_1 = workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'color': 'blue'})
        blue_border_1 = workbook.add_format(
            {'border': 1, 'align': 'left', 'valign': 'vcenter', 'color': 'blue'})
        blue_border = workbook.add_format(
            {'border': 1, 'bold': 1, 'align': 'center', 'valign': 'vcenter', 'color': 'blue'})
        normal_format = workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'text_wrap': True})
        bold_format = workbook.add_format(
            {'bold': 1, 'align': 'left', 'valign': 'vcenter'})
        black_format = workbook.add_format(
            {'border': 1, 'align': 'left', 'valign': 'vcenter'})
        light_grey_format = workbook.add_format(
            {'border': 1, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True, 'bg_color': '#C0C0C0'})
        light_grey_bold = workbook.add_format(
            {'bold': 1, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'bg_color': '#C0C0C0'})
        grey_format = workbook.add_format(
            {'bold': 1, 'border': 1, 'align': 'center', 'font_size':9, 'valign': 'vcenter', 'bg_color': '#969696'})
        yellow_format = workbook.add_format(
            {'bold': 1, 'border': 1, 'align': 'center', 'font_size': 9, 'valign': 'vcenter', 'bg_color': '#FFCC00'})
        grey_bottom = workbook.add_format(
            {'bold': 1, 'border': 1, 'text_wrap': True, 'bottom': False, 'align': 'center', 'font_size':9, 'valign': 'vcenter', 'bg_color': '#969696'})
        grey_top = workbook.add_format(
            {'bold': 1, 'border': 1, 'top': False, 'align': 'center', 'font_size': 9, 'valign': 'vcenter',
             'bg_color': '#969696'})

        border_format = workbook.add_format(
            {'bold': 1, 'border': 1, 'left': False, 'top': False, 'bottom': False, 'align': 'center', 'font_size': 9,
             'valign': 'vcenter'})

        table_format = workbook.add_format(
            {'bold': 1, 'border': 1, 'top': False, 'bottom': False, 'align': 'center', 'font_size': 9, 'valign': 'vcenter'})

        table_format_2 = workbook.add_format(
            {'bold': 1, 'border': 1, 'top': False, 'bottom': True, 'align': 'center', 'font_size': 9,
             'valign': 'vcenter'})

        for rec in self.product_development_id:

            logo = base64.b64decode(self.company_id.logo)
            logo = BytesIO(logo)

            company_logo = Image.open(logo).resize((220, 60), Image.ANTIALIAS)
            company_logo.save('/tmp/company_logo.png')

            worksheet.insert_image('A1:L1', '/tmp/company_logo.png')
            worksheet.merge_range('T1:AT1', self.company_id.name, first_row_format_tt)
            worksheet.merge_range('AU1:BM1', '', first_row_format_tt)

            worksheet.merge_range('A2:F2', 'Revised Date:', blue_format_top)
            worksheet.merge_range('A3:F3', 'Importer:', blue_format)
            worksheet.merge_range('A4:F4', 'In Care of :', blue_format)
            worksheet.merge_range('A5:F5', 'Address:', blue_format)

            worksheet.merge_range('G2:S2', 'Revised Date', workbook.add_format(
                {'top': True, 'align': 'left', 'valign': 'vcenter', 'color': 'blue'}))
            worksheet.merge_range('G3:S3', 'Revised Date', blue_format_1)
            worksheet.merge_range('G4:S4', 'Revised Date', blue_format_1)
            worksheet.merge_range('G5:S5', 'Revised Date', blue_format_1)

            worksheet.merge_range('U2:Y2', 'PO #:', blue_format)
            worksheet.merge_range('U3:Y3', 'Sold to:', blue_format)
            worksheet.merge_range('U4:Y4', 'Address:', blue_format)

            worksheet.merge_range('Z2:AJ2', 'Revised Date', workbook.add_format(
                {'top': True, 'align': 'left', 'valign': 'vcenter', 'color': 'blue'}))
            worksheet.merge_range('Z3:AJ3', 'Revised Date', blue_format)
            worksheet.merge_range('Z4:AJ4', 'Revised Date', blue_format)

            worksheet.merge_range('AN3:AU3', 'Shipping Window:', workbook.add_format(
                {'bold': 1, 'border': 1, 'bottom': False, 'align': 'center', 'valign': 'vcenter', 'color': 'blue'}))
            worksheet.merge_range('AN4:AU4', 'ETA Houston Port:',  workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'align': 'center', 'valign': 'vcenter', 'color': 'blue'}))
            worksheet.merge_range('AN5:AU5', 'Shipment to PS:', workbook.add_format(
                {'bold': 1, 'border': 1, 'bottom': False, 'align': 'center', 'valign': 'vcenter', 'color': 'blue'}))
            worksheet.merge_range('AN6:AU6', 'In Club Date:',  workbook.add_format(
                {'bold': 1, 'border': 1, 'bottom': True, 'top': False, 'align': 'center', 'valign': 'vcenter', 'color': 'blue'}))

            worksheet.merge_range('A8:BM8', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#969696'}))

            worksheet.merge_range('A9:G9', 'Specifications:', workbook.add_format(
                {'bold': 1, 'align': 'center', 'valign': 'vcenter'}))

            worksheet.merge_range('A10:G10', 'Material:', normal_format)
            worksheet.merge_range('H10:R10', rec.material, blue_format)
            worksheet.merge_range('A11:G11', 'Absorption:', normal_format)
            worksheet.merge_range('A12:G12', 'Production system:', normal_format)
            worksheet.merge_range('A13:G13', 'Shape:', normal_format)
            worksheet.merge_range('A14:G14', 'Style:', normal_format)
            worksheet.merge_range('A15:G15', 'Decoration System:', normal_format)
            worksheet.merge_range('A16:G16', 'Color:', normal_format)
            worksheet.merge_range('A17:G17', 'Markings:', normal_format)

            worksheet.merge_range('U10:Z10', 'Compatibility:', normal_format)
            worksheet.merge_range('U11:Z11', 'Packaging:', normal_format)
            worksheet.merge_range('U12:Z12', 'Brand:', normal_format)
            worksheet.merge_range('AA12:AM12', rec.brand, blue_format_1)
            worksheet.merge_range('U13:Z13', 'Country of Origin:', normal_format)
            worksheet.merge_range('AA13:AM13', rec.made_in.name, blue_format_1)

            img = base64.b64decode(self.company_id.logo)
            img = BytesIO(img)

            company_logo = Image.open(img).resize((300, 100), Image.ANTIALIAS)
            company_logo.save('/tmp/company_img.png')

            worksheet.insert_image('AS10:AZ10', '/tmp/company_img.png')

            illustration = base64.b64decode(rec.image)
            illustration = BytesIO(illustration)

            illustration_logo = Image.open(illustration).resize((150, 100), Image.ANTIALIAS)
            illustration_logo.save('/tmp/illustration.png')

            worksheet.merge_range('A19:J19', 'ILLUSTRATION', grey_bottom)
            worksheet.merge_range('A20:J20', '', grey_top)
            worksheet.insert_image('B21:I21', '/tmp/illustration.png')

            worksheet.merge_range('K19:W19', 'DESCRIPTION', grey_bottom)
            worksheet.merge_range('K20:W20', '', grey_top)

            worksheet.merge_range('K21:W21', rec.description, normal_format)

            worksheet.merge_range('X19:AA19', 'COUNTRY OF', grey_bottom)
            worksheet.merge_range('X20:AA20', 'ORIGIN', grey_top)
            worksheet.merge_range('X21:AA21', rec.made_in.name if rec.made_in else '', blue_format_1)

            worksheet.merge_range('AB19:AE19', 'WAREFOR', grey_bottom)
            worksheet.merge_range('AB20:AE20', 'ITEM #', grey_top)

            worksheet.merge_range('AB21:AE21', '', blue_format_1)

            worksheet.merge_range('AF19:AI19', 'MFR', grey_bottom)
            worksheet.merge_range('AF20:AI20', 'ITEM #', grey_top)

            worksheet.merge_range('AF21:AI21', '', blue_format_1)

            worksheet.merge_range('AJ19:AN19', 'UPC', grey_bottom)
            worksheet.merge_range('AJ20:AN20', '', grey_top)

            worksheet.merge_range('AJ21:AN21', rec.upc, blue_format_1)

            worksheet.merge_range('AO19:AZ19', 'PACKAGING INFORMATION', grey_format)
            worksheet.merge_range('AO20:AR20', 'UNIT', grey_format)

            worksheet.merge_range('AO21:AR21', '1 Set', blue_format_1)

            worksheet.merge_range('AS20:AV20', 'CUBE', grey_format)
            worksheet.merge_range('AS21:AV21', rec.packaging_cuft_ds, blue_format_1)
            worksheet.merge_range('AW20:AZ20', 'WEIGHT', grey_format)
            worksheet.merge_range('AW21:AZ21', rec.packaging_weight_ds, blue_format_1)

            worksheet.merge_range('BA19:BD19', 'OXFORD BR', grey_bottom)
            worksheet.merge_range('BE19:BH19', 'OXFORD US', grey_bottom)
            worksheet.merge_range('BI19:BM19', 'QUANTITY', grey_bottom)

            worksheet.merge_range('BA20:BD20', 'SALE PRICE', grey_top)
            worksheet.merge_range('BE20:BH20', 'SALE PRICE', grey_top)
            worksheet.merge_range('BI20:BM20', '', grey_top)

            worksheet.write(20, 9, '', border_format)
            worksheet.write(21, 9, '', border_format)
            worksheet.write(22, 9, '', border_format)
            worksheet.write(23, 9, '', border_format)
            worksheet.write(24, 9, '', border_format)
            worksheet.write(25, 9, '', border_format)
            worksheet.write(26, 9, '', border_format)
            worksheet.write(27, 9, '', border_format)
            worksheet.write(28, 9, '', border_format)
            worksheet.write(29, 9, '', border_format)
            worksheet.write(30, 9, '', border_format)
            worksheet.write(31, 9, '', border_format)
            worksheet.write(32, 9, '', border_format)
            worksheet.write(33, 9, '', border_format)
            worksheet.write(34, 9, '', border_format)
            worksheet.write(35, 9, '', border_format)
            worksheet.write(36, 9, '', border_format)
            worksheet.write(37, 9, '', border_format)
            worksheet.write(38, 9, '', border_format)
            worksheet.write(39, 9, '', border_format)
            worksheet.write(40, 9, '', border_format)

            worksheet.write(20, 22, '', border_format)
            worksheet.write(21, 22, '', border_format)
            worksheet.write(22, 22, '', border_format)
            worksheet.write(23, 22, '', border_format)
            worksheet.write(24, 22, '', border_format)
            worksheet.write(25, 22, '', border_format)
            worksheet.write(26, 22, '', border_format)
            worksheet.write(27, 22, '', border_format)
            worksheet.write(28, 22, '', border_format)
            worksheet.write(29, 22, '', border_format)
            worksheet.write(30, 22, '', border_format)
            worksheet.write(31, 22, '', border_format)
            worksheet.write(32, 22, '', border_format)
            worksheet.write(33, 22, '', border_format)
            worksheet.write(34, 22, '', border_format)
            worksheet.write(35, 22, '', border_format)
            worksheet.write(36, 22, '', border_format)
            worksheet.write(37, 22, '', border_format)
            worksheet.write(38, 22, '', border_format)
            worksheet.write(39, 22, '', border_format)
            worksheet.write(40, 22, '', border_format)

            worksheet.write(20, 26, '', border_format)
            worksheet.write(21, 26, '', border_format)
            worksheet.write(22, 26, '', border_format)
            worksheet.write(23, 26, '', border_format)
            worksheet.write(24, 26, '', border_format)
            worksheet.write(25, 26, '', border_format)
            worksheet.write(26, 26, '', border_format)
            worksheet.write(27, 26, '', border_format)
            worksheet.write(28, 26, '', border_format)
            worksheet.write(29, 26, '', border_format)
            worksheet.write(30, 26, '', border_format)
            worksheet.write(31, 26, '', border_format)
            worksheet.write(32, 26, '', border_format)
            worksheet.write(33, 26, '', border_format)
            worksheet.write(34, 26, '', border_format)
            worksheet.write(35, 26, '', border_format)
            worksheet.write(36, 26, '', border_format)
            worksheet.write(37, 26, '', border_format)
            worksheet.write(38, 26, '', border_format)
            worksheet.write(39, 26, '', border_format)
            worksheet.write(40, 26, '', border_format)

            worksheet.write(20, 39, '', border_format)
            worksheet.write(21, 39, '', border_format)
            worksheet.write(22, 39, '', border_format)
            worksheet.write(23, 39, '', border_format)
            worksheet.write(24, 39, '', border_format)
            worksheet.write(25, 39, '', border_format)
            worksheet.write(26, 39, '', border_format)
            worksheet.write(27, 39, '', border_format)
            worksheet.write(28, 39, '', border_format)
            worksheet.write(29, 39, '', border_format)
            worksheet.write(30, 39, '', border_format)
            worksheet.write(31, 39, '', border_format)
            worksheet.write(32, 39, '', border_format)
            worksheet.write(33, 39, '', border_format)
            worksheet.write(34, 39, '', border_format)
            worksheet.write(35, 39, '', border_format)
            worksheet.write(36, 39, '', border_format)
            worksheet.write(37, 39, '', border_format)
            worksheet.write(38, 39, '', border_format)
            worksheet.write(39, 39, '', border_format)
            worksheet.write(40, 39, '', border_format)

            worksheet.write(20, 51, '', border_format)
            worksheet.write(21, 51, '', border_format)
            worksheet.write(22, 51, '', border_format)
            worksheet.write(23, 51, '', border_format)
            worksheet.write(24, 51, '', border_format)
            worksheet.write(25, 51, '', border_format)
            worksheet.write(26, 51, '', border_format)
            worksheet.write(27, 51, '', border_format)
            worksheet.write(28, 51, '', border_format)
            worksheet.write(29, 51, '', border_format)
            worksheet.write(30, 51, '', border_format)
            worksheet.write(31, 51, '', border_format)
            worksheet.write(32, 51, '', border_format)
            worksheet.write(33, 51, '', border_format)
            worksheet.write(34, 51, '', border_format)
            worksheet.write(35, 51, '', border_format)
            worksheet.write(36, 51, '', border_format)
            worksheet.write(37, 51, '', border_format)
            worksheet.write(38, 51, '', border_format)
            worksheet.write(39, 51, '', border_format)
            worksheet.write(40, 51, '', border_format)

            worksheet.write(20, 64, '', border_format)
            worksheet.write(21, 64, '', border_format)
            worksheet.write(22, 64, '', border_format)
            worksheet.write(23, 64, '', border_format)
            worksheet.write(24, 64, '', border_format)
            worksheet.write(25, 64, '', border_format)
            worksheet.write(26, 64, '', border_format)
            worksheet.write(27, 64, '', border_format)
            worksheet.write(28, 64, '', border_format)
            worksheet.write(29, 64, '', border_format)
            worksheet.write(30, 64, '', border_format)
            worksheet.write(31, 64, '', border_format)
            worksheet.write(32, 64, '', border_format)
            worksheet.write(33, 64, '', border_format)
            worksheet.write(34, 64, '', border_format)
            worksheet.write(35, 64, '', border_format)
            worksheet.write(36, 64, '', border_format)
            worksheet.write(37, 64, '', border_format)
            worksheet.write(38, 64, '', border_format)
            worksheet.write(39, 64, '', border_format)
            worksheet.write(40, 64, '', border_format)

            worksheet.merge_range('A41:J41', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'left': False, 'bottom': True, 'align': 'center', 'font_size': 9,
                 'valign': 'vcenter'}))
            worksheet.merge_range('K41:W41', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'left': False, 'bottom': True, 'align': 'center', 'font_size': 9,
                 'valign': 'vcenter'}))
            worksheet.merge_range('X41:AA41', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'left': False, 'bottom': True, 'align': 'center', 'font_size': 9,
                 'valign': 'vcenter'}))
            worksheet.merge_range('AB41:AN41', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'left': False, 'bottom': True, 'align': 'center', 'font_size': 9,
                 'valign': 'vcenter'}))
            worksheet.merge_range('AO41:AZ41', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'left': False, 'bottom': True, 'align': 'center', 'font_size': 9,
                 'valign': 'vcenter'}))
            worksheet.merge_range('BA41:BM41', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'left': False, 'bottom': True, 'align': 'center', 'font_size': 9,
                 'valign': 'vcenter'}))

            worksheet.merge_range('B42:E42', 'Notes:', blue_format)

            worksheet.merge_range('A43:E43', 'Samples:', blue_format)
            worksheet.merge_range('A46:E46', 'Brand:', blue_format_1)
            worksheet.merge_range('F46:BA46', rec.brand, blue_format_1)
            worksheet.merge_range('A47:E47', 'Packaging:', blue_format_1)
            worksheet.merge_range('A48:E48', 'Dimensions:', blue_format_1)
            worksheet.merge_range('A50:E50', 'Shipment:', blue_format_1)

            worksheet.merge_range('A51:BM51', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'right': False, 'align': 'center',
                 'valign': 'vcenter', 'bg_color': '#FFFFFF'}))

            worksheet.insert_image('A52:L52', '/tmp/company_logo.png')
            worksheet.merge_range('T52:BM52', 'PDW - PRODUCT DIMENSIONS & WEIGHTS', first_row_format)

            worksheet.merge_range('A53:S53', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'bottom': False, 'right': False, 'align': 'center',
                 'valign': 'vcenter', 'bg_color': '#FFFFFF'}))
            worksheet.merge_range('U53:BM53', '', blue_format)

            worksheet.merge_range('B54:E54', 'Date:', blue_format)
            worksheet.merge_range('U54:X54', 'PO #:', blue_format)

            worksheet.merge_range('A55:BM55', '', blue_format)

            worksheet.merge_range('A56:BM56', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#969696'}))

            worksheet.merge_range('A57:BM57', '', blue_format)

            worksheet.merge_range('A58:P58', 'ITEM IDENTIFICATION', grey_format)
            worksheet.merge_range('Q58:AG58', 'PACKAGING INFORMATION', grey_format)
            worksheet.merge_range('AH58:BM58', 'PALLET INFORMATION', grey_format)

            worksheet.write(58, 15, '', border_format)
            worksheet.write(59, 15, '', border_format)
            worksheet.write(60, 15, '', border_format)
            worksheet.write(61, 15, '', border_format)
            worksheet.write(62, 15, '', border_format)
            worksheet.write(63, 15, '', border_format)
            worksheet.write(64, 15, '', border_format)
            worksheet.write(65, 15, '', border_format)
            worksheet.write(66, 15, '', border_format)
            worksheet.write(67, 15, '', border_format)
            worksheet.write(68, 15, '', border_format)
            worksheet.write(69, 15, '', border_format)
            worksheet.write(70, 15, '', border_format)
            worksheet.write(71, 15, '', border_format)
            worksheet.write(72, 15, '', border_format)
            worksheet.write(73, 15, '', border_format)
            worksheet.write(74, 15, '', border_format)
            worksheet.write(75, 15, '', border_format)
            worksheet.write(76, 15, '', border_format)
            worksheet.write(77, 15, '', border_format)

            worksheet.write(58, 32, '', border_format)
            worksheet.write(59, 32, '', border_format)
            worksheet.write(60, 32, '', border_format)
            worksheet.write(61, 32, '', border_format)
            worksheet.write(62, 32, '', border_format)
            worksheet.write(63, 32, '', border_format)
            worksheet.write(64, 32, '', border_format)
            worksheet.write(65, 32, '', border_format)
            worksheet.write(66, 32, '', border_format)
            worksheet.write(67, 32, '', border_format)
            worksheet.write(68, 32, '', border_format)
            worksheet.write(69, 32, '', border_format)
            worksheet.write(70, 32, '', border_format)
            worksheet.write(71, 32, '', border_format)
            worksheet.write(72, 32, '', border_format)
            worksheet.write(73, 32, '', border_format)
            worksheet.write(74, 32, '', border_format)
            worksheet.write(75, 32, '', border_format)
            worksheet.write(76, 32, '', border_format)
            worksheet.write(77, 32, '', border_format)

            worksheet.write(58, 64, '', border_format)
            worksheet.write(59, 64, '', border_format)
            worksheet.write(60, 64, '', border_format)
            worksheet.write(61, 64, '', border_format)
            worksheet.write(62, 64, '', border_format)
            worksheet.write(63, 64, '', border_format)
            worksheet.write(64, 64, '', border_format)
            worksheet.write(65, 64, '', border_format)
            worksheet.write(64, 64, '', border_format)
            worksheet.write(67, 64, '', border_format)
            worksheet.write(68, 64, '', border_format)
            worksheet.write(69, 64, '', border_format)
            worksheet.write(70, 64, '', border_format)
            worksheet.write(71, 64, '', border_format)
            worksheet.write(72, 64, '', border_format)
            worksheet.write(73, 64, '', border_format)
            worksheet.write(74, 64, '', border_format)
            worksheet.write(75, 64, '', border_format)
            worksheet.write(76, 64, '', border_format)
            worksheet.write(77, 64, '', border_format)

            worksheet.merge_range('A78:P78', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'left': False, 'bottom': True, 'align': 'center', 'font_size': 9,
                 'valign': 'vcenter'}))
            worksheet.merge_range('Q78:AG78', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'left': False, 'bottom': True, 'align': 'center', 'font_size': 9,
                 'valign': 'vcenter'}))
            worksheet.merge_range('AH78:BM78', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'left': False, 'bottom': True, 'align': 'center', 'font_size': 9,
                 'valign': 'vcenter'}))

            worksheet.merge_range('B60:F60', 'Mfr. Item #:', black_format)
            worksheet.merge_range('B62:F62', 'Retailer Item #:', black_format)
            worksheet.merge_range('B64:F64', 'UPC Number:', workbook.add_format(
                {'border': 1, 'right': False, 'align': 'left', 'valign': 'vcenter'}))
            worksheet.merge_range('G64:O64', rec.upc, workbook.add_format(
                {'border': 1, 'left': False, 'align': 'left', 'valign': 'vcenter', 'color': 'blue'}))
            worksheet.insert_image('G71:O71', '/tmp/illustration.png')

            worksheet.merge_range('B66:H66', 'Item Description:', workbook.add_format(
                {'border': 1, 'right': False, 'align': 'left', 'valign': 'vcenter'}))
            worksheet.merge_range('G66:O66', rec.description, workbook.add_format(
                {'border': 1, 'left': False, 'align': 'left', 'valign': 'vcenter', 'color': 'blue', 'text_wrap': True}))

            worksheet.merge_range('R60:W60', 'Case Pack:', black_format)

            worksheet.merge_range('R72:Z72', 'Dimensions & Weight:', normal_format)

            cube = rec.packaging_width_ds * rec.packaging_height_ds

            worksheet.merge_range('R73:T73', 'Width (Front)', light_grey_format)
            worksheet.merge_range('U73:W73', 'Depth (Side)', light_grey_format)
            worksheet.merge_range('X73:Z73', 'Height', light_grey_format)
            worksheet.merge_range('AA73:AC73', 'Cube', light_grey_format)
            worksheet.merge_range('AD73:AF73', 'Weight', light_grey_format)

            worksheet.merge_range('R74:T74', rec.packaging_width_ds, blue_border_1)
            worksheet.merge_range('U74:W74', '', blue_border_1)
            worksheet.merge_range('X74:Z74', rec.packaging_height_ds, blue_border_1)
            worksheet.merge_range('AA74:AC74', cube, blue_border_1)
            worksheet.merge_range('AD74:AF74', rec.packaging_weight_ds, blue_border_1)

            worksheet.merge_range('R75:T75', '', table_format_2)
            worksheet.merge_range('U75:W75', '', table_format_2)
            worksheet.merge_range('X75:Z75', '', table_format_2)
            worksheet.merge_range('AA75:AC75', '', table_format_2)
            worksheet.merge_range('AD75:AF75', '', table_format_2)

            worksheet.merge_range('AI60:AN60', 'Units/Pallet:', black_format)

            worksheet.merge_range('AI72:AX72', 'Dimensions & Weight - (Excluding Pallet)', normal_format)
            worksheet.merge_range('AY72:BL72', 'Dimensions & Weight - (Including Pallet)', normal_format)

            worksheet.merge_range('AI73:AK73', '48" (Front)', light_grey_format)
            worksheet.merge_range('AL73:AN73', '40" (Side)', light_grey_format)
            worksheet.merge_range('AO73:AP73', 'Height', light_grey_format)
            worksheet.merge_range('AQ73:AR73', 'Cube', light_grey_format)
            worksheet.merge_range('AS73:AT73', 'Weight', light_grey_format)

            cube_1 = rec.packaging_width * rec.packaging_height
            worksheet.merge_range('AI74:AK74', '', blue_border_1)
            worksheet.merge_range('AL74:AN74', rec.packaging_width, blue_border_1)
            worksheet.merge_range('AO74:AP74', rec.packaging_height, blue_border_1)
            worksheet.merge_range('AQ74:AR74', cube_1, blue_format_1)
            worksheet.merge_range('AS74:AT74', '', table_format)

            worksheet.merge_range('AI75:AK75', '', black_format)
            worksheet.merge_range('AL75:AN75', '', black_format)
            worksheet.merge_range('AO75:AP75', '', black_format)
            worksheet.merge_range('AQ75:AR75', '', table_format_2)
            worksheet.merge_range('AS75:AT75', '', table_format_2)

            worksheet.merge_range('AY73:BA73', '48" (Front)', light_grey_format)
            worksheet.merge_range('BB73:BC73', '40" (Side)', light_grey_format)
            worksheet.merge_range('BD73:BF73', 'Height', light_grey_format)
            worksheet.merge_range('BG73:BI73', 'Cube', light_grey_format)
            worksheet.merge_range('BJ73:BL73', 'Weight', light_grey_format)

            cube_2 = rec.packaging_width_cm * rec.packaging_height_cm
            worksheet.merge_range('AY74:BA74', '', blue_border_1)
            worksheet.merge_range('BB74:BC74', rec.packaging_width_cm, blue_border_1)
            worksheet.merge_range('BD74:BF74', rec.packaging_height_cm, blue_border_1)
            worksheet.merge_range('BG74:BI74', cube_2, table_format)
            worksheet.merge_range('BJ74:BL74', '', table_format)

            worksheet.merge_range('AY75:BA75', '', black_format)
            worksheet.merge_range('BB75:BC75', '', black_format)
            worksheet.merge_range('BD75:BF75', '', black_format)
            worksheet.merge_range('BG75:BI75', '', table_format_2)
            worksheet.merge_range('BJ75:BL75', '', table_format_2)

            worksheet.merge_range('A87:BM87', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'right': False, 'align': 'center',
                 'valign': 'vcenter', 'bg_color': '#FFFFFF'}))

            worksheet.insert_image('A88:L88', '/tmp/company_logo.png')
            worksheet.merge_range('T88:BM88', 'CONTAINER & TRUCK LOAD CALCULATION', first_row_format)

            worksheet.merge_range('A89:S89', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'bottom': False, 'right': False, 'align': 'center',
                 'valign': 'vcenter', 'bg_color': '#FFFFFF'}))
            worksheet.merge_range('U89:BM89', '', blue_format)

            worksheet.merge_range('B90:E90', 'Date:', blue_format)
            worksheet.merge_range('U90:X90', 'PO #:', blue_format)

            worksheet.merge_range('A91:BM91', '', blue_format)

            worksheet.merge_range('A92:BM92', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#969696'}))

            worksheet.merge_range('G94:P94', 'ILLUSTRATION', grey_bottom)
            worksheet.merge_range('G95:P95', '', grey_top)
            worksheet.insert_image('G96:P96', '/tmp/illustration.png')

            worksheet.merge_range('Q94:AC94', 'DESCRIPTION', grey_bottom)
            worksheet.merge_range('Q95:AC95', '', grey_top)
            worksheet.merge_range('Q96:AC96', rec.description, normal_format)

            worksheet.merge_range('AD94:AG94', 'COUNTRY', grey_bottom)
            worksheet.merge_range('AD95:AG95', 'OF ORIGIN', grey_top)
            worksheet.merge_range('AD96:AG96', rec.made_in.name, normal_format)

            worksheet.merge_range('AH94:AK94', 'MFR ', grey_bottom)
            worksheet.merge_range('AH95:AK95', 'ITEM #', grey_top)

            worksheet.merge_range('AL94:AO94', 'RETAILER', grey_bottom)
            worksheet.merge_range('AL95:AO95', 'ITEM #', grey_top)

            worksheet.merge_range('AP94:AW94', 'UPC', grey_bottom)
            worksheet.merge_range('AP95:AW95', '', grey_top)
            worksheet.merge_range('AP96:AW96', rec.upc, normal_format)

            worksheet.merge_range('AX94:BH94', 'PALLET INFORMATION', grey_format)
            worksheet.merge_range('AX95:BA95', 'UNITS/PALLET', grey_format)
            worksheet.merge_range('BB95:BE95', 'CUBE', grey_format)
            worksheet.merge_range('BF95:BH95', 'WEIGHT', grey_format)

            worksheet.write(95, 5, '', border_format)
            worksheet.write(96, 5, '', border_format)
            worksheet.write(97, 5, '', border_format)
            worksheet.write(98, 5, '', border_format)
            worksheet.write(99, 5, '', border_format)
            worksheet.write(100, 5, '', border_format)
            worksheet.write(101, 5, '', border_format)
            worksheet.write(102, 5, '', border_format)

            worksheet.write(95, 15, '', border_format)
            worksheet.write(96, 15, '', border_format)
            worksheet.write(97, 15, '', border_format)
            worksheet.write(98, 15, '', border_format)
            worksheet.write(99, 15, '', border_format)
            worksheet.write(100, 15, '', border_format)
            worksheet.write(101, 15, '', border_format)
            worksheet.write(102, 15, '', border_format)

            worksheet.write(95, 28, '', border_format)
            worksheet.write(96, 28, '', border_format)
            worksheet.write(97, 28, '', border_format)
            worksheet.write(98, 28, '', border_format)
            worksheet.write(99, 28, '', border_format)
            worksheet.write(100, 28, '', border_format)
            worksheet.write(101, 28, '', border_format)
            worksheet.write(102, 28, '', border_format)

            worksheet.write(95, 32, '', border_format)
            worksheet.write(96, 32, '', border_format)
            worksheet.write(97, 32, '', border_format)
            worksheet.write(98, 32, '', border_format)
            worksheet.write(99, 32, '', border_format)
            worksheet.write(100, 32, '', border_format)
            worksheet.write(101, 32, '', border_format)
            worksheet.write(102, 32, '', border_format)

            worksheet.write(95, 36, '', border_format)
            worksheet.write(96, 36, '', border_format)
            worksheet.write(97, 36, '', border_format)
            worksheet.write(98, 36, '', border_format)
            worksheet.write(99, 36, '', border_format)
            worksheet.write(100, 36, '', border_format)
            worksheet.write(101, 36, '', border_format)
            worksheet.write(102, 36, '', border_format)

            worksheet.write(95, 40, '', border_format)
            worksheet.write(96, 40, '', border_format)
            worksheet.write(97, 40, '', border_format)
            worksheet.write(98, 40, '', border_format)
            worksheet.write(99, 40, '', border_format)
            worksheet.write(100, 40, '', border_format)
            worksheet.write(101, 40, '', border_format)
            worksheet.write(102, 40, '', border_format)

            worksheet.write(95, 48, '', border_format)
            worksheet.write(96, 48, '', border_format)
            worksheet.write(97, 48, '', border_format)
            worksheet.write(98, 48, '', border_format)
            worksheet.write(99, 48, '', border_format)
            worksheet.write(100, 48, '', border_format)
            worksheet.write(101, 48, '', border_format)
            worksheet.write(102, 48, '', border_format)

            worksheet.write(95, 59, '', border_format)
            worksheet.write(96, 59, '', border_format)
            worksheet.write(97, 59, '', border_format)
            worksheet.write(98, 59, '', border_format)
            worksheet.write(99, 59, '', border_format)
            worksheet.write(100, 59, '', border_format)
            worksheet.write(101, 59, '', border_format)
            worksheet.write(102, 59, '', border_format)

            worksheet.merge_range('G103:P103', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False,'left': True, 'bottom': True, 'align': 'center', 'font_size': 9,
                 'valign': 'vcenter'}))
            worksheet.merge_range('Q103:AC103', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'left': True, 'bottom': True, 'align': 'center', 'font_size': 9,
                 'valign': 'vcenter'}))
            worksheet.merge_range('AD103:AG103', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'left': True, 'bottom': True, 'align': 'center', 'font_size': 9,
                 'valign': 'vcenter'}))
            worksheet.merge_range('AH103:AK103', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'left': True, 'bottom': True, 'align': 'center', 'font_size': 9,
                 'valign': 'vcenter'}))
            worksheet.merge_range('AL103:AO103', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'left': True, 'bottom': True, 'align': 'center', 'font_size': 9,
                 'valign': 'vcenter'}))
            worksheet.merge_range('AP103:AW103', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'left': True, 'bottom': True, 'align': 'center', 'font_size': 9,
                 'valign': 'vcenter'}))
            worksheet.merge_range('AX103:BH103', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'left': True, 'bottom': True, 'align': 'center', 'font_size': 9,
                 'valign': 'vcenter'}))

            worksheet.merge_range('G106:R106', 'Ocean Containers', workbook.add_format(
                {'align': 'left', 'valign': 'vcenter', 'bold': 1}))
            worksheet.merge_range('AC106:AS106', 'Wedge Trailer (Dry Van)', workbook.add_format(
                {'align': 'left', 'valign': 'vcenter', 'bold': 1}))

            worksheet.merge_range('G107:L107', 'Container Size', grey_format)
            worksheet.merge_range('M107:Q107', '20 Ft.', grey_format)
            worksheet.merge_range('R107:V107', '40 Ft.', yellow_format)
            worksheet.merge_range('W107:AA107', '40 Ft. HC', grey_format)

            worksheet.merge_range('G108:L108', 'Cu Ft', light_grey_bold)
            worksheet.merge_range('M108:Q108', '', light_grey_bold)
            worksheet.merge_range('R108:V108', '', light_grey_bold)
            worksheet.merge_range('W108:AA108', '', light_grey_bold)

            worksheet.merge_range('G109:L109', 'Units', blue_border)
            worksheet.merge_range('M109:Q109', '', black_format)
            worksheet.merge_range('R109:V109', '', black_format)
            worksheet.merge_range('W109:AA109', '', black_format)

            worksheet.merge_range('G110:L110', 'Pay Load (Lbs)', light_grey_bold)
            worksheet.merge_range('M110:Q110', '', light_grey_bold)
            worksheet.merge_range('R110:V110', '', light_grey_bold)
            worksheet.merge_range('W110:AA110', '', light_grey_bold)

            worksheet.merge_range('G111:L111', 'Units', blue_border)
            worksheet.merge_range('M111:Q111', '', black_format)
            worksheet.merge_range('R111:V111', '', black_format)
            worksheet.merge_range('W111:AA111', '', black_format)

            worksheet.merge_range('AC107:AI107', 'Trailer Size', grey_format)
            worksheet.merge_range('AJ107:AU107', '48 Foot', grey_format)
            worksheet.merge_range('AV107:BG107', '53 Foot', yellow_format)

            worksheet.merge_range('AC108:AI108', 'Cu Ft', light_grey_bold)
            worksheet.merge_range('AJ108:AU108', '', light_grey_bold)
            worksheet.merge_range('AV108:BG108', '', light_grey_bold)

            worksheet.merge_range('AC109:AI109', 'Quantity', blue_border)
            worksheet.merge_range('AJ109:AU109', '', blue_border)
            worksheet.merge_range('AV109:BG109', '', blue_border)

            worksheet.merge_range('AC110:AI110', 'Pay Load (Lbs)', light_grey_bold)
            worksheet.merge_range('AJ110:AU110', '', light_grey_bold)
            worksheet.merge_range('AV110:BG110', '', light_grey_bold)

            worksheet.merge_range('AC111:AI111', 'Quantity', blue_border)
            worksheet.merge_range('AJ111:AU111', '', blue_border)
            worksheet.merge_range('AV111:BG111', '', blue_border)

            worksheet.merge_range('G113:L113', 'Container Size', light_grey_bold)
            worksheet.merge_range('M113:Q113', '20 Ft.', light_grey_bold)
            worksheet.merge_range('R113:V113', '40 Ft.', light_grey_bold)
            worksheet.merge_range('W113:AA113', '40 Ft. HC', light_grey_bold)

            worksheet.merge_range('G114:L114', 'Cubic Metric', table_format)
            worksheet.merge_range('M114:Q114', '', black_format)
            worksheet.merge_range('R114:V114', '', black_format)
            worksheet.merge_range('W114:AA114', '', black_format)

            worksheet.merge_range('G115:L115', 'Pay Load (Kg)', light_grey_bold)
            worksheet.merge_range('M115:Q115', '', light_grey_bold)
            worksheet.merge_range('R115:V115', '', light_grey_bold)
            worksheet.merge_range('W115:AA115', '', light_grey_bold)

            worksheet.merge_range('AC113:AI113', 'Trailer Size', light_grey_bold)
            worksheet.merge_range('AJ113:AU113', '48 Foot', light_grey_bold)
            worksheet.merge_range('AV113:BG113', '53 Foot', light_grey_bold)

            worksheet.merge_range('AC114:AI114', 'Cubic Metric', light_grey_bold)
            worksheet.merge_range('AJ114:AU114', '', light_grey_bold)
            worksheet.merge_range('AV114:BG114', '', light_grey_bold)

            worksheet.merge_range('AC115:AI115', 'Pay Load (Kg)', light_grey_bold)
            worksheet.merge_range('AJ115:AU115', '', light_grey_bold)
            worksheet.merge_range('AV115:BG115', '', light_grey_bold)

            worksheet.merge_range('G117:Q117', 'Order Quantity:', bold_format)

            worksheet.merge_range('G118:AA118', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'bottom': False, 'align': 'center', 'font_size': 9, 'valign': 'vcenter', 'bg_color': '#FFCC00'}))
            worksheet.merge_range('G119:AA119', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'align': 'center', 'font_size': 9, 'valign': 'vcenter', 'bg_color': '#FFCC00'}))

            worksheet.merge_range('AC118:BC118', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'bottom': False, 'align': 'center', 'font_size': 9, 'valign': 'vcenter'}))
            worksheet.merge_range('AC119:BC119', '', workbook.add_format(
                {'bold': 1, 'border': 1, 'top': False, 'align': 'center', 'font_size': 9, 'valign': 'vcenter'}))

        workbook.close()
        return file_name

    def create_attachment(self, file_name):
        """
        Delete file created in tmp dir, Delete old attachment and create attachment for download report
        :param file_name: file name string
        :return: attachment ir.attachment object
        """
        ir_attachment_obj = self.env['ir.attachment']

        # Read File data
        with open(file_name, "rb+") as file:
            file_data = base64.encodebytes(file.read())
            file.close()

        # Remove tmp file
        os.remove(file_name)

        # Delete Old Attachment
        attachments = ir_attachment_obj.search([('name', '=ilike', 'PD Report.xlsx'),
                                                ('res_model', '=', 'crm.lead')])
        attachments and attachments.unlink()

        return ir_attachment_obj.create({
            'name': 'PD Report.xlsx',
            'datas': file_data,
            'res_model': 'crm.lead',
            'type': 'binary'
        })