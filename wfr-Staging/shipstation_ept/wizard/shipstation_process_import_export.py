import logging
import base64
import csv
import time
from odoo import models, fields, api, _
from io import StringIO
from odoo.exceptions import ValidationError, UserError
from odoo.tools.misc import xlsxwriter
import os
import sys

try:
    import xlrd
except ImportError:
    xlrd = None

PY3 = sys.version_info >= (3, 0)

if PY3:
    basestring = str
    long = int
    xrange = range
    unicode = str

_logger = logging.getLogger(__name__)


class ShipstationProcessImportExport(models.TransientModel):
    """
    class for shipstation import export operations.
    """
    _name = 'shipstation.process.import.export'
    _description = 'Shipstation Process Import Export Operation'

    shipstation_instance_id = fields.Many2one('shipstation.instance.ept', string='Instances')
    process = fields.Selection([('import_product', 'Import Product'),
                                ('export_product', 'Export Product'),
                                ('map_product', 'Map Product'),
                                ('export_orders', 'Export Orders'),
                                ('validate_delivery_order', 'Validate Delivery Orders')], string='Process')
    auto_create_product = fields.Boolean('Auto Create Product?')
    product_start_date = fields.Datetime(string="Start Date")
    product_end_date = fields.Datetime(string="End Date")
    store_ids = fields.Many2many('shipstation.store.ept',
                                 'shipstation_store_import_export_rel',
                                 'process_id', 'name', string='Stores')
    file_name = fields.Char(string='Name')
    choose_file = fields.Binary(string="Select File")
    delimiter = fields.Selection([('\t', 'Tab'), (',', 'Comma'), (';', 'Semicolon')], string='Delimiter',
                                 default=",")
    product_map_attachment_id = fields.Many2one('ir.attachment', string="Attachment Id", readonly=True)

    """Method to get Active instance id from Shipstation Instance Kanban View
    and calls process method import export operations for that particular instance."""

    def import_export_processes(self):
        """
        execute import-export operations in Shipstation.
        @return:
        """
        shipstation_product_obj = self.env['shipstation.product.ept']
        instance = self.shipstation_instance_id
        # Added by [ES] | Task: 182456
        # check credentials at import/export operations
        if instance:
            instance.test_shipstation_connection()

        # Validate the delivery orders.
        if self.process == 'validate_delivery_order':
            self.env['shipstation.instance.ept'].auto_validate_delivery_order({'shipstation_instance_id': instance.id})

        # import products from shipstation process.
        if self.process == 'import_product' or self.auto_create_product:
            shipstation_product_obj.import_product(instance,
                                                   self.auto_create_product,
                                                   self.product_start_date,
                                                   self.product_end_date)

        # export orders to shipstation process.
        if self.process == 'export_orders':
            self.env['shipstation.instance.ept'].export_to_shipstation_cron({'shipstation_instance_id': instance.id},
                                                                            self.store_ids, self.product_start_date,
                                                                            self.product_end_date)

        # create a csv file for products to import in shipstation.
        if self.process == 'export_product':
            return shipstation_product_obj.export_products_csv(instance)
        if self.process == 'map_product':
            return self.import_csv_file()
        return True

    def download_product_map_xlsx(self):
        self.product_map_attachment_id = False
        self.ensure_one()
        result = self.prepare_excel_file_data()
        if not self.product_map_attachment_id:
            new_attachment = self.env["ir.attachment"].create({
                "name": "map_product_{}.xlsx".format(time.strftime("%d_%m_%Y|%H_%M_%S")),
                "datas": result,
                "type": "binary"
            })
            self.write({'product_map_attachment_id': new_attachment.id})
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % self.product_map_attachment_id.id,
            'target': 'self'
        }

    def prepare_product_map_data(self):
        data = []
        products = self.env["shipstation.product.ept"].search(
            [('shipstation_instance_id', '=', self.shipstation_instance_id.id)])
        for product in products:
            data.append([product.shipstation_instance_id.name, product.name, product.shipstation_identification,
                         product.shipstation_sku,
                         product.product_id.default_code])
        return data

    def prepare_excel_file_data(self):
        created_file_path = "/tmp/map_product_{}.xlsx".format(time.strftime("%d_%m_%Y|%H_%M_%S"))
        workbook = xlsxwriter.Workbook(created_file_path)
        worksheet = workbook.add_worksheet()
        header_style = workbook.add_format({'bold': True})
        row_format = workbook.add_format({'font_size': '10'})
        header_fields = ["Instance", "Name", "Shipstation Product", "Shipstation SKU", "Product SKU"]
        for column_number, cell_value in enumerate(header_fields):
            worksheet.write(0, column_number, cell_value, header_style)
        product_datas = self.prepare_product_map_data()
        if not product_datas:
            raise UserError("Nothing to Map!!!!")
        row_no = 1
        for data in product_datas:
            worksheet.write(row_no, 0, data[0], row_format)
            worksheet.write(row_no, 1, data[1], row_format)
            worksheet.write(row_no, 2, data[2], row_format)
            worksheet.write(row_no, 3, data[3], row_format)
            worksheet.write(row_no, 4, data[4], row_format)
            row_no += 1
        workbook.close()
        file = open(created_file_path, 'rb')
        report_data_file = base64.encodestring(file.read())
        file.close()
        os.unlink(created_file_path)
        return report_data_file

    def import_csv_file(self):
        if not self.choose_file:
            raise UserError(_('Please Upload File.'))
        try:
            file_format = self.file_name.split('.')[1]
            if file_format in ['xls', 'xlsx']:
                imp_file = xlrd.open_workbook(file_contents=base64.decodebytes(self.choose_file))
            else:
                imp_file = StringIO(base64.decodebytes(self.choose_file).decode())
        except Exception as e:
            raise UserError(e)
        if file_format == 'csv':
            file_data = csv.reader(imp_file, delimiter=self.delimiter)
        else:
            file_data = self.get_product_map_xlsx_file_data(imp_file)
        self.process_import_data(file_data)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "All products import successfully!",
                'img_url': '/web/static/src/img/smile.svg',
                'type': 'rainbow_man',
            }
        }

    def get_product_map_xlsx_file_data(self, imp_file):
        worksheet = imp_file.sheet_by_index(0)
        try:
            data = []
            for row_index in range(0, worksheet.nrows):
                sheet_data = []
                for col_index in xrange(worksheet.ncols):
                    sheet_data.append(worksheet.cell(row_index, col_index).value)
                data.append(sheet_data)
        except Exception as e:
            error_value = str(e)
            raise ValidationError(error_value)
        return data

    def process_import_data(self, product_datas):
        model_id = self.env['ir.model'].sudo().search([('model', '=', "shipstation.product.ept")]).id
        shipstation_prod_obj = self.env["shipstation.product.ept"]
        product_obj = self.env["product.product"]
        for row_number, data in enumerate(product_datas):
            if len(data) != 5:
                raise UserError("File missing required columns!!!")
            if row_number == 0:
                continue
            if data[3] == 0 or data[3] == '':
                self.create_log_line_for_map_product('export', model_id, row_number, 'Shipstation SKU missing')
                continue
            instance = self.env["shipstation.instance.ept"].search([('name', '=ilike', data[0])], limit=1)
            if not instance:
                self.create_log_line_for_map_product('export', model_id, row_number,
                                                     'No Shipstation instance found for {}'.format(data[0]))
                continue
            product_id = product_obj.search([('default_code', '=ilike', data[4])], limit=1)
            if not product_id:
                self.create_log_line_for_map_product('export', model_id, row_number,
                                                     "Odoo product not found SKU: {}".format(data[4]), product_id)
                continue
            shipstation_prod = shipstation_prod_obj.search([('shipstation_instance_id', '=', instance.id),
                                                            ('shipstation_sku', '=ilike', data[3])], limit=1)
            if not shipstation_prod:
                msg = 'Shipstation product not found, Shipstation SKU: {}, Instance {}'.format(data[3], instance.name)
                self.create_log_line_for_map_product('export', model_id, row_number, msg)
                continue
            shipstation_prod.write({'product_id': product_id.id})
            msg = 'Shipstation Product {} map with product {}, instance {}'.format(
                shipstation_prod.shipstation_identification,
                product_id.default_code or '', instance.name)
            self.create_log_line_for_map_product('export', model_id, row_number, msg, product_id)

    def create_log_line_for_map_product(self, type, model_id, count, msg, product_id=False):
        msg = 'Row: {}, {}'.format(count + 1, msg)
        _logger.info(msg)
        log_line = self.env['common.log.lines.ept']
        vals = {
            'operation_type': type,
            'message': msg,
            'model_id': model_id,
            'module': 'shipstation_ept'
        }
        if product_id:
            vals.update({'product_id': product_id.id,
                         'default_code': product_id.default_code})
        log_line.create(vals)
