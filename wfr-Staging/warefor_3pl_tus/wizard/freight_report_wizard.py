# -*- coding: utf-8 -*-
import io
from io import BytesIO
import base64
import pytz
import calendar
from datetime import datetime
from PIL import Image
import os

from odoo.tools.misc import xlsxwriter
from ast import literal_eval
import logging

from odoo import api, models, fields
from odoo.exceptions import ValidationError
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class FreightReportWizard(models.TransientModel):
    _name = 'freight.report.wizard'
    _description = 'Freight Report Wizard'

    date_from = fields.Date(string="From", help="Date from")
    date_to = fields.Date(string="To", help="Date to")
    customer_id = fields.Many2one("res.partner", string="Customers", help="Select the customers to filter the PL records")
    is_outbound = fields.Boolean(string="Is Outbound")

    @api.model
    def default_get(self, fields_list):
        vals = super(FreightReportWizard, self).default_get(fields_list)
        default_is_outbound = self.env.context.get('default_is_outbound')
        vals['is_outbound'] = default_is_outbound
        return vals

    def generate_pl_report(self):
        if self.is_outbound:
            res = self.action_outbound_logistic_report()
        else:
            res = self.action_inbound_logistic_report()
        return res

    def action_inbound_logistic_report(self):
        """

        :return:
        """
        domain = [('is_outbound', '=', False), ('active', 'in', [True, False])]
        if self.date_from:
            domain.append(('unload_end_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('unload_end_date', '<=', self.date_to))
        if self.customer_id:
            domain.append(('partner_id', 'in', self.customer_id.ids))
        outbound_logistic_ids = self.env["freight.freight"].search(domain)

        dict_data = []
        header_name = ""

        if not outbound_logistic_ids:
            raise ValidationError("No record found to generate the report!")

        try:
            ###########################################
            header_columns = [ "Reference #","Ship From","Transport" , "Item #", "Lot #","BOL",
                              "Description", "Quantity", "Total \nPallets", "Units \nPer Pallet",
                              "Total \nWeight", "Weight \nPallet", "Received \nDate", "Remarks"]
            header_name = 'INBOUND RELEASE ORDERS LOG'

            if self.customer_id.name:
                header_name = "{} INBOUND ORDERS LOG".format(self.customer_id.name).upper()

            xlsx_file = "Inbound_Logistic_Report_{}.xlsx".format(fields.Date.today())
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            v_common_bg_style = workbook.add_format(
                {'bold': True, 'align': 'vcenter', 'valign': 'center', 'border': 0, 'center_across': 'center', 'font_size': 24})
            left_common_bg_style = workbook.add_format(
                {'bold': False, 'valign': 'vcenter', 'align': 'center', 'border': 0})
            left_common_style_number = workbook.add_format(
                {'bold': False, 'align': 'left', 'border': 0})
            date_common_bg_style = workbook.add_format(
                {'bold': True, 'valign': 'vcenter', 'align': 'center', 'border': 0, 'color': '#4f86f7'})

            header_common_bg_style = workbook.add_format(
                {'valign': 'vcenter', 'align': 'center', 'border': 1, 'bg_color': '#b8b8b8', 'font_size': 10,
                 'text_wrap': True})
            header_common_bg_style_for_description = workbook.add_format({'valign': 'vcenter', 'align': 'left','border': 1, 'bg_color': '#b8b8b8', 'font_size': 10, 'indent':1})
            data_style_1 = workbook.add_format({'valign': 'vcenter','align': 'center', 'border': 1, 'font_size': 10})
            data_style_2 = workbook.add_format({'valign': 'vcenter','align': 'left', 'border': 1, 'font_size': 10, 'indent': 1})
            data_style_3 = workbook.add_format({'valign': 'vcenter','align': 'right', 'border': 1, 'font_size': 10, 'indent': 1, 'num_format': '#,###'})
            data_style_4 = workbook.add_format({'valign': 'vcenter','align': 'center', 'border': 1, 'font_size': 10, 'color': '#4f86f7'})
            data_style_6 = workbook.add_format({'valign': 'vcenter', 'align': 'left', 'border': 1, 'font_size': 10, 'indent': 1})
            data_style_for_0_3 = workbook.add_format({'valign': 'vcenter', 'align': 'center', 'border': 1, 'font_size': 10, 'bold':True})
            data_style_for_col1 = workbook.add_format({'valign': 'vcenter','align': 'left', 'border': 1, 'font_size': 10, 'indent': 1, 'bold': True})
            sheet = workbook.add_worksheet("Sheet1")
            sheet.set_column(0, 0, 15)
            sheet.set_column(1, 1, 30)
            sheet.set_column(2, 2, 20)
            sheet.set_column(3, 3, 15)
            sheet.set_column(4, 4, 12)
            sheet.set_column(5, 5, 15)
            sheet.set_column(6, 6, 45)
            sheet.set_column(7, 7, 12)
            sheet.set_column(8, 8, 12)
            sheet.set_column(9, 9, 12)
            sheet.set_column(10, 10, 12)
            sheet.set_column(11, 11, 12)
            sheet.set_column(12, 12, 15)
            sheet.set_column(13, 13, 30)
            # logo = base64.b64decode(self.env.company.logo)
            # logo = BytesIO(logo)

            # company_logo = Image.open(logo).resize((180, 50), Image.ANTIALIAS)
            # company_logo.save('/tmp/company_logo.png')
            path = os.path.abspath(os.path.join(__file__,'../../../')) + '/warefor_3pl_tus/static/src/img/warefor_logo.png'
            sheet.insert_image('A1:A2', path, {'x_offset': 10, 'y_offset': 10, 'x_scale':0.09, 'y_scale':0.1})

            col = 0
            row = 0
            sheet.set_row(row, 50)
            sheet.merge_range(row, col, row, col + 13, header_name, v_common_bg_style)
            row += 1
            col = 0
            sheet.write(row, col, 'Last Updated', left_common_bg_style)
            col += 1
            sheet.write(row, col, "{} {} {}".format(
                datetime.today().day, calendar.month_name[datetime.today().month], datetime.today().year),
                        date_common_bg_style)
            col += 1
            sheet.write(row, col, '', left_common_bg_style)
            col += 1
            sheet.write(row, col, 'Time', left_common_bg_style)
            col += 1
            user_tz = self.env.user.tz
            if user_tz:
                local = pytz.timezone(user_tz)
                header_date = datetime.strftime(pytz.utc.localize(datetime.today()).astimezone(local), '%I:%M %p')
            sheet.write(row, col, str(header_date), date_common_bg_style)

            for temp in range(9):
                col += 1
                sheet.write(row, col, '', date_common_bg_style)

            # Header for Start-Date , End-date ########
            row += 1
            col = 0
            sheet.write(row, col, 'From Date', left_common_bg_style)
            col += 1
            sheet.write(row, col, str(self.date_from and self.date_from.strftime('%m/%d/%Y') or "N/A"), date_common_bg_style)
            col += 1
            sheet.write(row, col, '', left_common_bg_style)
            col += 1
            sheet.write(row, col, 'To Date', left_common_bg_style)
            col += 1
            sheet.write(row, col, str(self.date_to and self.date_to.strftime('%m/%d/%Y') or "N/A"), date_common_bg_style)
            col += 1
            sheet.write(row, col, '', left_common_bg_style)
            col += 1
            sheet.write(row, col, '', left_common_bg_style)
            col += 1

            # customer_name = ','.join([''.join(customers) for customers in customers_name])
            # sheet.merge_range(row, col, row, col + 7, str(customer_name or "N/A"), left_common_style)


            row += 1
            col = 0
            ##################### Header ######################
            for header in header_columns:
                sheet.set_row(row, 30)
                if header in ['Description', 'Remarks']:
                    sheet.write(row, col, header,header_common_bg_style_for_description)
                else:
                    sheet.write(row, col, header, header_common_bg_style)
                col += 1
            row += 1
            ###########################################
            for obl_id in outbound_logistic_ids:
                freight_order_line_ids = obl_id.freight_order_line_ids
                for freight_line in freight_order_line_ids.sudo():
                    total_pallate = freight_line.required_pallet
                    total_weight = freight_line.net_weight
                    weight_pallet = 0
                    if total_pallate:
                        weight_pallet = total_weight/total_pallate
                    if obl_id.unload_end_date:
                        receive_date = str(obl_id.unload_end_date.strftime('%m/%d/%Y') or "N/A")
                    else:
                        receive_date = "N/A"

                    # location = obl_id.picking_ids and obl_id.picking_ids.mapped('location_id.name')
                    location = obl_id.picking_ids.mapped('move_line_ids_without_package').filtered(
                        lambda x: x.product_id.id == freight_line.goods.id).mapped('picking_id').mapped(
                        'location_id.name')
                    locations = ', '.join([''.join(loc) for loc in location])

                    data = {
                        "Reference #": obl_id.reference or "N/A",
                        "Come From": obl_id.port_discharge_id.name or "N/A",
                        "Transport": obl_id.drayage_id.name or "N/A",
                        # "Customer PO#": obl_id.customer_po or "N/A",
                        # "Transport": obl_id.freight_transport_id.name or "N/A",
                        "Item #": freight_line.goods.default_code or "N/A",
                        "Lot #": freight_line.lot_id.name or "N/A",
                        "BOL": obl_id.awb_no or "N/A",
                        "Description": freight_line.goods.name or "N/A",
                        "Quantity": int(freight_line.total_quantity or 0),
                        "Total Pallets": int(total_pallate or 0),
                        "Units Per Pallet": int(freight_line.total_pallet or 0),
                        "Total Weight": int(total_weight or 0),
                        "Weight Pallet": int(weight_pallet or 0),
                        "Received Date": receive_date,
                        # "WH Location": locations or "N/A",
                        "REMARKS:": obl_id.ibl_remarks.name or "N/A",
                    }
                    data = data.values()
                    col = 0
                    size = 12
                    for val in data:
                        if col in [2, 14, 13]:
                            sheet.write(row, col, val, data_style_2)
                        elif col in [7, 8, 9, 10, 11]:
                            sheet.write(row, col, val, data_style_3)
                        # elif col == 0:
                        #     sheet.write(row, col, val, data_style_1)
                        elif col == 6:
                            sheet.write(row, col, val, data_style_6)
                        elif col == 12:
                            sheet.write(row, col, val, data_style_4)
                        elif col in [0, 3]:
                            sheet.write(row, col, val, data_style_for_0_3)
                        elif col == 1:
                            sheet.write(row, col, val, data_style_for_col1)
                        else:
                            if col == 13 and len(location) >1:
                                sheet.set_row(row,size * len(location),None)
                            sheet.write(row, col, val, data_style_1)
                        col += 1
                    row += 1
            ###########################################
            workbook.close()
            output.seek(0)

            output = base64.encodebytes(output.read())
            ##########################################

            new_attach = {
                'name': xlsx_file,
                'type': "binary",
                'mimetype': 'application/zip',
                'datas': output,
                'res_model': self._name,
                'res_id': self.id,
            }
            attachment_id = self.env["ir.attachment"].create(new_attach)
            download_url = '/web/content/?model=ir.attachment&id={}&filename_field=name&field=datas&download=true&name={}'.format(
                attachment_id.id, attachment_id.name)
            action = {
                'type': 'ir.actions.act_url',
                'url': download_url,
                'target': 'new',
            }
            return action
        except Exception as e:
            _logger.error("Warning : Unable to generate report. Please contact your administrator. **** {}".format(e))
            raise ValidationError("Warning : Unable to generate report. Please contact your administrator.")

    def action_outbound_logistic_report(self):
        """

        :return:
        """
        domain = [('is_outbound', '=', True), ('active', 'in', [True, False])]
        if self.date_from:
            domain.append(('check_out_truck_yard', '>=', self.date_from))
        if self.date_to:
            domain.append(('check_out_truck_yard', '<=', self.date_to))
        if self.customer_id:
            domain.append(('partner_id', 'in', self.customer_id.ids))
        outbound_logistic_ids = self.env["freight.freight"].search(domain)

        dict_data = []
        header_name = ""

        if not outbound_logistic_ids:
            raise ValidationError("No record found to generate the report!")

        try:
            header_columns = ["Reference #", "Customer PO#", "Ship to", "Item #", "Lot #", "BOL",
                              "Description", "Quantity", "Total \nPallets", "Units \nPer Pallet",
                              "Total\nWeight", "Weight\nPallet", "Ship Date", "Carrier",
                              "Driver Name", "Remarks"]
            header_name = 'OUTBOUND RELEASE ORDERS LOG'

            if self.customer_id.name:
                header_name = "{} OUTBOUND ORDERS LOG".format(self.customer_id.name).upper()

            xlsx_file = "Outbound_Logistic_Report_{}.xlsx".format(fields.Date.today())
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            v_common_bg_style = workbook.add_format(
                {'bold': True, 'align': 'vcenter', 'valign': 'center', 'border': 0, 'center_across': 'center', 'font_size': 24})
            left_common_bg_style = workbook.add_format(
                {'bold': False, 'valign': 'vcenter', 'align': 'center', 'border': 0})
            left_common_style = workbook.add_format(
                {'bold': True, 'valign': 'vcenter', 'align': 'left', 'border': 0, 'color': '#4f86f7'})
            date_common_bg_style = workbook.add_format(
                {'bold': True, 'valign': 'vcenter', 'align': 'center', 'border': 0, 'color': '#4f86f7'})
            header_common_bg_style = workbook.add_format(
                {'valign': 'vcenter', 'align': 'center', 'border': 1, 'bg_color': '#b8b8b8', 'font_size': 10,
                 'text_wrap': True})
            header_common_bg_style2 = workbook.add_format(
                {'valign': 'vcenter', 'align': 'left', 'border': 1, 'bg_color': '#b8b8b8', 'font_size': 10,
                 'text_wrap': True, 'indent' : 1})
            data_style_1 = workbook.add_format({'valign': 'vcenter', 'align': 'center', 'border': 1, 'font_size': 10})
            data_style_2 = workbook.add_format({'valign': 'vcenter', 'align': 'left', 'border': 1, 'font_size': 10, 'indent': 1})
            data_style_3 = workbook.add_format({'valign': 'vcenter', 'align': 'right', 'border': 1, 'font_size': 10, 'indent': 1, 'num_format': '#,###'})
            data_style_4 = workbook.add_format({'bold': True, 'valign': 'vcenter', 'border': 1, 'font_size': 10,'align': 'center'})
            data_style_5 = workbook.add_format({'bold': True, 'valign': 'vcenter', 'align': 'center', 'border': 1, 'font_size': 10})
            data_style_6 = workbook.add_format({'bold': True,'valign': 'vcenter', 'align': 'left', 'border': 1, 'font_size': 10, 'indent': 1})
            data_style_13 = workbook.add_format({'valign': 'vcenter', 'align': 'left', 'border': 1, 'font_size': 10, 'indent': 1,'color': '#4f86f7'})
            data_style_14_15 = workbook.add_format({'valign': 'vcenter', 'align': 'left', 'border': 1, 'font_size': 10, 'indent': 1, 'color': '#4f86f7'})
            data_style_12 = workbook.add_format({'valign': 'vcenter', 'align': 'center', 'border': 1, 'font_size': 10, 'color': '#4f86f7'})

            sheet = workbook.add_worksheet("Sheet1")
            sheet.set_column(0, 0, 12)
            sheet.set_column(1, 1, 15)
            sheet.set_column(2, 2, 35)
            sheet.set_column(3, 3, 12)
            sheet.set_column(4, 4, 12)
            sheet.set_column(5, 5, 15)
            sheet.set_column(6, 6, 45)
            sheet.set_column(7, 7, 8)
            sheet.set_column(8, 8, 12)
            sheet.set_column(9, 9, 12)
            sheet.set_column(10, 10, 12)
            sheet.set_column(11, 11, 12)
            sheet.set_column(12, 12, 15)
            sheet.set_column(13, 13, 30)
            sheet.set_column(14, 14, 20)
            sheet.set_column(15, 15, 25)
            # logo = base64.b64decode(self.env.company.logo)
            # logo = BytesIO(logo)
            # company_logo = Image.open(logo).resize((180, 50), Image.ANTIALIAS)
            # company_logo.save('/tmp/company_logo.png')
            path = os.path.abspath(os.path.join(__file__, '../../../')) + '/warefor_3pl_tus/static/src/img/warefor_logo.png'
            sheet.insert_image('A1:A2', path, {'x_offset': 10, 'y_offset': 10, 'x_scale': 0.09, 'y_scale': 0.1})

            col = 0
            row = 0
            sheet.set_row(row, 50)
            sheet.merge_range(row, col, row, col + 15, header_name, v_common_bg_style)
            row += 1
            col = 0
            sheet.write(row, col, 'Last Updated', left_common_bg_style)
            col += 1
            sheet.write(row, col, "{} {} {}".format(
                datetime.today().day, calendar.month_name[datetime.today().month], datetime.today().year),
                        date_common_bg_style)
            col += 1
            sheet.write(row, col, '', left_common_bg_style)
            col += 1
            sheet.write(row, col, 'Time', left_common_bg_style)
            col += 1
            user_tz = self.env.user.tz
            if user_tz:
                local = pytz.timezone(user_tz)
                header_date = datetime.strftime(pytz.utc.localize(datetime.today()).astimezone(local), '%I:%M %p')
            sheet.write(row, col, str(header_date), date_common_bg_style)

            for temp in range(9):
                col += 1
                sheet.write(row, col, '', date_common_bg_style)

            # Header for Start-Date , End-date ########
            row += 1
            col = 0
            sheet.write(row, col, 'From Date', left_common_bg_style)
            col += 1
            sheet.write(row, col, str(self.date_from and self.date_from.strftime('%m/%d/%Y') or "N/A"), date_common_bg_style)
            col += 1
            sheet.write(row, col, '', left_common_bg_style)
            col += 1
            sheet.write(row, col, 'To Date', left_common_bg_style)
            col += 1
            sheet.write(row, col, str(self.date_to and self.date_to.strftime('%m/%d/%Y') or "N/A"), date_common_bg_style)
            col += 1
            sheet.write(row, col, '', left_common_bg_style)
            col += 1
            sheet.write(row, col, '', left_common_bg_style)
            col += 1

            # customer_name = ','.join([''.join(customers) for customers in customers_name])
            # sheet.merge_range(row, col, row, col + 9, str(customer_name or "N/A"), left_common_style)

            row += 1
            col = 0
            ###########################################
            for header in header_columns:
                if header in ["Carrier","Driver Name", "Remarks"]:
                    sheet.set_row(row, 30)
                    sheet.write(row, col, header, header_common_bg_style2)
                else:
                    sheet.set_row(row, 30)
                    sheet.write(row, col, header, header_common_bg_style)
                col += 1
            row += 1
            for obl_id in outbound_logistic_ids:
                freight_order_line_ids = obl_id.freight_order_line_ids
                for freight_line in freight_order_line_ids.sudo():
                    total_pallate = freight_line.required_pallet
                    total_weight = freight_line.net_weight
                    weight_pallet = 0
                    if total_pallate:
                        weight_pallet = total_weight / total_pallate
                    if obl_id.check_out_truck_yard:
                        ship_date = str(obl_id.check_out_truck_yard.strftime('%m/%d/%Y') or "N/A")
                    else:
                        ship_date = "N/A"
                    # location = obl_id.picking_ids and obl_id.picking_ids.mapped('location_id.name')
                    location = obl_id.picking_ids.mapped('move_line_ids_without_package').filtered(
                        lambda x: x.product_id.id == freight_line.goods.id).mapped('picking_id').mapped(
                        'location_id.name')
                    locations = ', \n'.join([''.join(loc) for loc in location])

                    data = {
                        "Reference #": obl_id.reference or "N/A",
                        "Customer PO#": obl_id.customer_po or "N/A",
                        "Ship to:": obl_id.outbound_partner_id.name or "N/A",
                        "Item #": freight_line.goods.default_code or "N/A",
                        "Lot #": freight_line.lot_id.name or "N/A",
                        "BL": obl_id.bol_number or "N/A",
                        "Description": freight_line.goods.name or "N/A",
                        "Quantity": int(freight_line.total_quantity),
                        "Total Pallets": int(total_pallate or 0),
                        "Units Per Pallet": int(freight_line.total_pallet or 0),
                        "Total Weight": int(total_weight or 0),
                        "Weight Pallet": int(weight_pallet or 0),
                        "Ship Date": ship_date,
                        # "Location #": locations or "N/A",
                        "Carrier": obl_id.carrier_flight.name or "N/A",
                        "Driver Name": obl_id.truck_driver_name or "N/A",
                        "REMARKS:": obl_id.obl_remarks.name or "N/A",
                    }
                    data = data.values()
                    col = 0
                    size = 12
                    for val in data:
                        sheet.set_row(row,15)
                        if col in [5, 6, 16]:
                            sheet.write(row, col, val, data_style_2)
                        elif col in [7, 8, 9, 10, 11]:
                            sheet.write(row, col, val, data_style_3)
                        elif col == 0:
                            sheet.write(row, col, val, data_style_5)
                        elif col in [1,3]:
                            sheet.write(row, col, val, data_style_4)
                        elif col == 2:
                            sheet.write(row, col, val, data_style_6)
                        elif col == 13:
                            sheet.write(row, col, val,data_style_13)
                        elif col in [14,15]:
                            sheet.write(row, col, val, data_style_14_15)
                        elif col == 12:
                            sheet.write(row, col, val, data_style_12)
                        else:
                            if col == 13 and len(location) > 1:
                                sheet.set_row(row, size * len(location), None)
                            sheet.write(row, col, val, data_style_1)
                        col += 1
                    row += 1
            ###########################################
            workbook.close()
            output.seek(0)

            output = base64.encodebytes(output.read())
            ##########################################

            new_attach = {
                'name': xlsx_file,
                'type': "binary",
                'mimetype': 'application/zip',
                'datas': output,
                'res_model': self._name,
                'res_id': self.id,
            }
            attachment_id = self.env["ir.attachment"].create(new_attach)
            download_url = '/web/content/?model=ir.attachment&id={}&filename_field=name&field=datas&download=true&name={}'.format(
                attachment_id.id, attachment_id.name)
            action = {
                'type': 'ir.actions.act_url',
                'url': download_url,
                'target': 'new',
            }
            return action
        except Exception as e:
            raise ValidationError("Warning : Unable to generate report. Please contact your administrator.")
