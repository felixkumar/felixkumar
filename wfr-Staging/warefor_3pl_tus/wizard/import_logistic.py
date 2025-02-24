from odoo import models, fields, exceptions, api, _
from datetime import datetime
import tempfile
import binascii
import logging



_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')
# for xls
try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')


class ImportLogistic(models.TransientModel):
    _name = "import.logistic"
    _description = 'Import Logistic'

    excel_file = fields.Binary('Excel File')
    excel_filename = fields.Char('Excel File Name')

    def import_xls(self):
        context = self._context
        try:
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.excel_file))
            fp.seek(0)
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
            freight_obj = self.env['freight.freight']
            for row_no in range(1, sheet.nrows):
                row_values = sheet.row_values(row_no)
                customer_po = ""
                supplier_id = self.env['res.partner']
                warehouse_id = self.env['stock.warehouse']
                if row_values and row_values[0]:
                    supplier_id = self.env['res.partner'].search([('name', '=', row_values[0].strip())])
                    if not supplier_id:
                        supplier_id = self.env['res.partner'].create({'name': row_values[0].strip()})
                if row_values and row_values[4]:
                    warehouse_id = self.env['stock.warehouse'].sudo().search([('name', '=', row_values[4].strip())])
                if row_values and row_values[3]:
                    customer_po = str(row_values[3]).split('.')[0]

                vals = {'partner_id': supplier_id.id,
                        'reference': row_values and row_values[1] or '',
                        'is_outbound': row_values and int(row_values[2]) or False,
                        'customer_po': customer_po,
                        'warehouse_id': warehouse_id.id,
                        'import_id': supplier_id.id,
                        'is_imported_record': True
                        }

                freight_obj.sudo().create(vals)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': 'Record Successfully Imported',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }}

        except Exception as e:
            raise exceptions.UserError(_("Please Provide Only .xlsx File to Import or Check the Format of the File!!!"))
