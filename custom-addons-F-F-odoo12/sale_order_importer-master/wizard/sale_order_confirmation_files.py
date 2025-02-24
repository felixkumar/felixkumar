# -*- coding: utf-8 -*-
import io

from odoo import _, api, fields, models
from odoo.exceptions import UserError

import base64
import pathlib
import openpyxl
import werkzeug.exceptions

ALLOWED_EXTENSIONS = [".csv", ".xls", ".xlsx", ".odt"]
SO_STATES_TO_CONFIRM = ["draft", "sent"]
SO_CONFIRM_STATE = "sale"

class SaleOrderConfirmationFiles(models.TransientModel):

    _name = "sale.order.confirmation.files"
    _description = "Sale Order Confirmation Files"

    so_confirm_file_data = fields.Binary(string='File')
    so_confirm_file_name = fields.Char(string='Load File Name')

    @api.multi
    def action_apply(self):
        """
            Read loaded file and confirm
            :return:
        """
        try:
            file_reader_generator = self._import_file_reader()

            for row in file_reader_generator:
                sale_order = self.env['sale.order'].search([('name', '=', row[0])])

                if sale_order and sale_order.state in SO_STATES_TO_CONFIRM:
                    sale_order.write({'state': SO_CONFIRM_STATE})
        except ValueError:
            raise werkzeug.exceptions.BadRequest('Invalid file format, pleas use .csv, .osd, .xls or .xlsx format')

        return True

    @api.multi
    def _import_file_reader(self):
        """
            Create a base_import object and read file
'            :return: _(file_extension).reader object
'        """
        file_extension = pathlib.Path(self.so_confirm_file_name).suffix
        if file_extension in ALLOWED_EXTENSIONS:
            if file_extension == '.xlsx':
                xlsx_data = io.BytesIO(base64.b64decode(self.so_confirm_file_data))
                workbook = openpyxl.load_workbook(xlsx_data)
                first_sheet = workbook.get_sheet_names()[0]
                worksheet = workbook.get_sheet_by_name(first_sheet)
                return (value for value in worksheet.values)
            else:
                return self.env['base_import.import'].create({
                    'file_name': self.so_confirm_file_name,
                    'file_type': file_extension,
                    'file': base64.b64decode(self.so_confirm_file_data)
                }).get_file_data({'quoting': '"'})
        else:
            raise UserError(_('Error: Invalid file format, pleas use .csv, .osd, .xls or .xlsx format'))
