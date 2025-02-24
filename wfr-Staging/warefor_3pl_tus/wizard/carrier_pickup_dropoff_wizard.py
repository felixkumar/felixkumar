# -*- coding: utf-8 -*-
import io
import math
from io import BytesIO
import base64
import pytz
import os

from datetime import datetime
from PIL import Image

from odoo.tools.misc import xlsxwriter
import logging

from odoo import api, models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def _get_hours_minutes_from_seconds(seconds):
    hours = math.floor(seconds / 3600)
    minutes = math.floor(round((seconds / 3600 - hours) * 60, 2))
    return hours, minutes


class CarrierPickupDropOffWizard(models.TransientModel):
    _name = "carrier.pickup.dropoff.wizard"
    _description = 'Carrier Pickup Dropoff Report Wizard'

    date_from = fields.Date(string="From", help="Date from", required="1")
    date_to = fields.Date(string="To", help="Date to",required="1")
    partner_id = fields.Many2one("res.partner", string="Customers", help="Select the customers to filter the records.",required="1")
    detail_file = fields.Binary("File")

    def convert_datetime_pytz(self, date):
        user_tz = self.env.user.tz or 'US/Central'
        return pytz.utc.localize(date).astimezone(pytz.timezone(user_tz))

    def _prepare_data(self):
        """ returns : List of dictionary of Inbound Outbound record for specific Customer within the data range"""
        data_dict = []
        date_from = datetime(year=self.date_from.year, month=self.date_from.month, day=self.date_from.day, hour=0,
                             minute=0, second=0)
        date_to = datetime(year=self.date_to.year, month=self.date_to.month, day=self.date_to.day, hour=11, minute=59,
                           second=59)

        freight_ids = self.env['freight.freight'].search(
            [('create_date', '>=', self.convert_datetime_pytz(date_from)),
             ('create_date', '<=', self.convert_datetime_pytz(date_to)),
             ('partner_id', '=', self.partner_id.id), ('osd_rec_stage_id.name', '!=', 'NEW')])
        for rec in freight_ids:
            if rec.is_outbound:
                freight_type = "Outbound"
                remarks = rec.obl_remarks and rec.obl_remarks.name or 'N/A'
                carrier = rec.carrier_flight and rec.carrier_flight.name or 'N/A'

            else:
                freight_type = "Inbound"
                remarks = rec.ibl_remarks and rec.ibl_remarks.name or 'N/A'
                carrier = rec.drayage_id and rec.drayage_id.name or 'N/A'

            check_in_truck_yard = rec.check_in_truck_yard and self.convert_datetime_pytz(rec.check_in_truck_yard) or ''
            schedule_date = rec.pickup_schedule_date and self.convert_datetime_pytz(rec.pickup_schedule_date) or ''
            message_vals = []
            if rec.message_ids:
                message_ids = rec.message_ids.sudo().filtered(lambda x:x.tracking_value_ids)
                tracking_values = message_ids.sudo().mapped('tracking_value_ids').filtered(lambda x:x.field.name == 'pickup_schedule_date')
                if tracking_values:
                    for tracking in tracking_values:
                        schedule_update_date = tracking.mail_message_id.date and self.convert_datetime_pytz(tracking.mail_message_id.date) or ''
                        schedule_date = tracking.new_value_datetime and self.convert_datetime_pytz(tracking.new_value_datetime) or ''
                        status = "Not Scheduled"
                        if schedule_date and check_in_truck_yard:
                            schedule_date = schedule_date.replace(second=0, microsecond=0)
                            check_in_truck_yard = check_in_truck_yard.replace(second=0, microsecond=0)
                            if check_in_truck_yard <= schedule_date:
                                diff = schedule_date.replace(tzinfo=None) - check_in_truck_yard.replace(tzinfo=None)
                                hours, minutes = _get_hours_minutes_from_seconds(diff.total_seconds())
                                delay = f'{hours}:' + str(minutes).zfill(2)
                                status = "Early"
                            else:
                                diff = check_in_truck_yard.replace(tzinfo=None) - schedule_date.replace(tzinfo=None)
                                hours, minutes = _get_hours_minutes_from_seconds(diff.total_seconds())
                                delay = f'{hours}:' + str(minutes).zfill(2)
                                status = "Late"
                        else:
                            if schedule_date and not check_in_truck_yard:
                                status = "Not Checked In"
                            delay = ""
                        message_vals.append({
                            "Reference": rec.reference or 'N/A',
                            "Inbound/Outbound": freight_type,
                            "Carrier": carrier,
                            "Scheduled Date Update By": tracking.mail_message_id.author_id and tracking.mail_message_id.author_id.name or '',
                            "Scheduled Date Update Date": schedule_update_date and schedule_update_date.strftime('%m/%d/%y %I:%M %p') or '',
                            "Scheduled Date": schedule_date and schedule_date.strftime('%m/%d/%y %I:%M %p') or '',
                            "Checked In": check_in_truck_yard and check_in_truck_yard.strftime('%m/%d/%y %I:%M %p') or '',
                            "Status": status,
                            "Delay": delay,
                            "Remarks": remarks,
                        })
            if message_vals:
                data_dict += message_vals
            else:
                status = "Not Scheduled"
                if schedule_date and check_in_truck_yard:
                    schedule_date = schedule_date.replace(second=0, microsecond=0)
                    check_in_truck_yard = check_in_truck_yard.replace(second=0, microsecond=0)
                    if check_in_truck_yard <= schedule_date:
                        diff = schedule_date.replace(tzinfo=None) - check_in_truck_yard.replace(tzinfo=None)
                        hours, minutes = _get_hours_minutes_from_seconds(diff.total_seconds())
                        delay = f'{hours}:' + str(minutes).zfill(2)
                        status = "Early"
                    else:
                        diff = check_in_truck_yard.replace(tzinfo=None) - schedule_date.replace(tzinfo=None)
                        hours, minutes = _get_hours_minutes_from_seconds(diff.total_seconds())
                        delay = f'{hours}:' + str(minutes).zfill(2)
                        status = "Late"
                else:
                    if schedule_date and not check_in_truck_yard:
                        status = "Not Checked In"
                    delay = ""
                vals = {
                    "Reference": rec.reference or 'N/A',
                    "Inbound/Outbound": freight_type,
                    "Carrier": carrier,
                    "Scheduled Date Update By": '',
                    "Scheduled Date Update Date": '',
                    "Scheduled Date": schedule_date and schedule_date.strftime('%m/%d/%y %I:%M %p') or '',
                    "Checked In": check_in_truck_yard and check_in_truck_yard.strftime('%m/%d/%y %I:%M %p') or '',
                    "Status": status,
                    "Delay": delay,
                    "Remarks": remarks,

                }
                data_dict.append(vals)
        return data_dict

    def set_worksheet_column(self, worksheet, row):
        """ Set the Column's width and Row's height for Excel sheet """
        worksheet.set_column(0, 0, 13)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 2, 25)
        worksheet.set_column(3, 4, 22)
        worksheet.set_column(5, 8, 17)
        worksheet.set_column(9, 9, 25)

        for i in range(row):
            worksheet.set_row(i, 15)
        worksheet.set_row(0, 40)
        worksheet.set_row(2, 20)
        worksheet.set_row(3, 25)

    def generate_xlsx_report(self):
        """  returns: Carrier Pickup & Dropoff Report  """
        records = self._prepare_data()
        if records:
            output = io.BytesIO()

            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            # Sheet Cell Styles
            content_center = workbook.add_format({'font_size': 11, 'align': 'center', 'valign': 'vcenter',
                                                  'border': 0})
            blue_center = workbook.add_format({'font_size': 11, 'align': 'left', 'valign': 'vcenter',
                                                'border': 0, 'indent': 1, 'color': '#0432FF', 'bold': True,})
            content_left = workbook.add_format({'font_size': 10, 'align': 'left', 'valign': 'vcenter',
                                                 'border': 0, 'indent': 1})

            header_center = workbook.add_format({'font_size': 10, 'valign': 'vcenter', 'align': 'center',
                                                 'border': 1, 'bg_color': '#b8b8b8'})
            bold_center = workbook.add_format({'font_size': 10, 'valign': 'vcenter', 'align': 'center',
                                                'indent': 1, 'bold': True})
            blue_left = workbook.add_format({'font_size': 10, 'align': 'left', 'valign': 'vcenter',
                                               'border': 0, 'indent': 1, 'color': '#0432FF'})
            blue_right = workbook.add_format({'font_size': 10, 'align': 'right', 'valign': 'vcenter',
                                             'border': 0, 'indent': 1, 'color': '#0432FF'})
            sheet = workbook.add_worksheet(self.partner_id.name.upper())
            row, col = 0, 0
            company = self.env.company
            logo = base64.b64decode(company.logo)
            logo = BytesIO(logo)

            user_tz = self.env.user.tz or 'US/Central'
            date_string = datetime.now(pytz.timezone(user_tz))

            # For Header Rows
            # company_logo = Image.open(logo,'r').resize((180, 50), Image.ANTIALIAS)
            # company_logo.save('/tmp/company_logo.png')
            # sheet.insert_image('A1:B1', '/tmp/company_logo.png')
            path = os.path.abspath(os.path.join(__file__, '../../../')) + '/warefor_3pl_tus/static/src/img/warefor_logo.png'
            sheet.insert_image('A1:B1', path, {'x_offset': 5, 'y_offset': 4, 'x_scale': 0.09, 'y_scale': 0.1})

            # For First 2 rows
            sheet.merge_range(row, 2, row, 9,
                              self.partner_id.name.upper() + ' - CARRIER PICKUP & DROPOFF REPORT',
                              workbook.add_format(
                                  {'font_size': 16, 'bold': True, 'valign': 'vcenter', 'align': 'center',
                                   'indent': 1, 'border': 0}))
            row += 1
            sheet.write(row, col, 'Last Update', content_center)
            sheet.write(row, col + 1, date_string.date().strftime('%b/%d/%Y'), blue_center)
            sheet.write(row, col + 3, 'Time', content_center)
            sheet.write(row, col + 4, date_string.time().strftime('%I:%M %p'), blue_center)

            row += 1
            sheet.write(row, col, 'From Date', content_center)
            sheet.write(row, col + 1, self.date_from.strftime('%m/%d/%Y'), blue_center)
            sheet.write(row, col + 3, 'To Date', content_center)
            sheet.write(row, col + 4, self.date_to.strftime('%m/%d/%Y'), blue_center)

            row += 1

            # Header Row
            headers = ['Reference #', 'Inbound / Outbound', 'Carrier', 'Schedule Date \nUpdate By',
                       'Schedule Date \nUpdate Date', 'Scheduled Date', 'Check In',
                       'Status', 'Delay (HH:MM)', 'Remarks']
            for head in headers:
                sheet.write(row, col, head, header_center)
                col += 1

            row += 1
            # Sheet data

            for data in records:
                col = 0
                for rec in list(data.values()):
                    if col == 0:
                        style = bold_center
                    elif col in [2,7]:
                        style = blue_left
                    elif col == 8:
                        style = blue_right
                    else:
                        style = content_left
                    sheet.write(row, col, rec, style)
                    col += 1
                row += 1

            self.set_worksheet_column(sheet, row)

            workbook.close()
            output.seek(0)
            filename = f'{self.partner_id.name.upper()} - Carrier Pickup %26 Dropoff Report'

            output = base64.encodebytes(output.read())
            self.write({'detail_file': output})
            return {
                'type': 'ir.actions.act_url',
                'url': 'web/content/?model=carrier.pickup.dropoff.wizard&field=detail_file&download=true&id=%s&filename=%s - ' % (self.id, filename),
                'target': 'new',
            }
        else:
            raise UserError(f'IBL/OBL record not found for {self.partner_id.name}.')
