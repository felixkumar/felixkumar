from odoo import fields, models, api
import io
import xlsxwriter
from datetime import datetime
import base64
import pytz


# import calendar

class business_appointment(models.Model):
    _inherit = "business.appointment"

    def action_ibl_obl_droupout_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Sheet1")
        headers = ["Reference", "Inbound/Outbound", "Scheduled Date", "Scheduled Time",
                   "Pick-up or Delivery Status", "Remarks"]
        row = 0
        col = 0
        header_common_bg_style = workbook.add_format(
            {'valign': 'vcenter', 'align': 'center', 'border': 1, 'bg_color': '#b8b8b8', 'font_size': 10})
        data_style = workbook.add_format(
            {'valign': 'vcenter', 'align': 'center', 'border': 1, 'font_size': 10})
        for header in headers:
            sheet.set_column(row, col, 20)
            sheet.write(row, col, header, header_common_bg_style)
            col += 1

        data_dict = []
        appointment_ids = self.search([])
        for rec in appointment_ids:
            if rec.x_oz_cbaf_3.is_outbound:
                status = "Outbound"
            else:
                status = "Inbound"
            vals = {
                "Reference": rec.x_oz_cbaf_3.reference or 'N/A',
                "Inbound/Outbound": status,
                "Scheduled Date": rec.datetime_start and rec.datetime_start.date().strftime("%m/%d/%Y") or 'N/A',
                "Scheduled Time": rec.datetime_start and rec.datetime_start.time().strftime("%H:%M %p") or 'N/A',
                "Pick-up or Delivery Status": rec.state or 'N/A',
                "Remarks": rec.description or 'N/A'
            }
            data_dict.append(vals)
        row += 1
        for data in data_dict:
            col = 0
            for rec in list(data.values()):
                sheet.write(row, col, rec, data_style)
                col += 1
            row += 1
        workbook.close()
        output.seek(0)

        output = base64.encodebytes(output.read())
        xlsx_file = "IBL_OBL_Droupout_Report_{}.xlsx".format(fields.Date.today())
        new_attach = {
            'name': xlsx_file,
            'type': "binary",
            'mimetype': 'application/zip',
            'datas': output,
            'res_model': self._name,
            # 'res_id': self.id,
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
