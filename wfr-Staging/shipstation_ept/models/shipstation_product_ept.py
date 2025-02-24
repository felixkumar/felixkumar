import datetime
import logging
import base64

from csv import DictWriter
from io import StringIO
from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ShipstationProduct(models.Model):
    _name = 'shipstation.product.ept'
    _description = 'Shipstation Product'

    name = fields.Char(string='Name')
    product_id = fields.Many2one('product.product', string='Product')
    shipstation_identification = fields.Integer(string='Shipstation Product')
    shipstation_sku = fields.Char(string='Shipstation SKU')
    shipstation_instance_id = fields.Many2one('shipstation.instance.ept', string="Instance")
    height = fields.Float(string='Height')
    width = fields.Float(string='Width')
    length = fields.Float(string='Length')
    weight = fields.Float(string='Weight')

    def import_product(self, instance, auto_create_product, product_start_date='',
                       product_end_date=''):
        """
            ShipStation Product Import operation.
        """
        model_id = self.env['ir.model'].search([('model', '=', self._name)]).id
        product_model_id = self.env['ir.model'].search([('model', '=', 'product.product')]).id
        log_line = self.env['common.log.lines.ept']
        product_obj = self.env['product.product']

        if instance and not product_start_date and instance.last_import_product:
            product_start_date = instance.last_import_product
            product_end_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        querystring = {'page': 1}
        if product_start_date and product_end_date:
            querystring = {'startDate': product_start_date,
                           'endDate': product_end_date,
                           'page': 1}

        while True:
            response, code = instance.get_connection(url='/products', params=querystring, method="GET")
            if code.status_code != 200:
                raise UserError('%s' % code.content.decode('utf-8'))
            if not response.get('products', []):
                break
            for res in response.get('products', []):
                product_id = res.get('productId', False)
                sku = res.get('sku', False)
                shipstation_product_name = res.get('name', False)
                product_height = res.get('height', False)
                product_width = res.get('width', False)
                product_length = res.get('length', False)
                product_weight = res.get('weightOz', False)

                if not product_id:
                    log_line.create_common_log_line_ept(operation_type='import',
                                                        model_id=model_id, module='shipstation_ept',
                                                        message="Product ID not found in Response "
                                                                "from API",
                                                        log_line_type='fail')
                    continue

                if not sku:
                    log_line.create_common_log_line_ept(message="SKU not found in Response from API"
                                                        , operation_type='import',
                                                        model_id=model_id, module='shipstation_ept',
                                                        log_line_type='fail')
                    continue

                if product_id and sku:
                    # code to update the shipstation_id in shipstation product if it exists.
                    existing_shipstation_product = self.search(
                        [('shipstation_sku', '=', sku),
                         ('shipstation_instance_id', '=', instance.id)])
                    if existing_shipstation_product and \
                            not existing_shipstation_product.shipstation_identification:
                        log_line.create_common_log_line_ept(
                            message="Shipstation Product for {} sku Adding shipstation Id.".format(
                                sku), model_id=model_id, operation_type='import',
                            module='shipstation_ept', log_line_type='success',
                            res_id=existing_shipstation_product.id)
                        existing_shipstation_product.write({'shipstation_identification': product_id})
                        continue
                    # ----------------------------------------------------------------------

                    shipstation_product = self.search(
                        [('shipstation_identification', '=', product_id),
                         ('shipstation_sku', '=', sku),
                         ('shipstation_instance_id', '=', instance.id)])
                    if shipstation_product:
                        continue
                    odoo_product = product_obj.search(['|', ('default_code', '=', sku),
                                                       ('barcode', '=', sku)], limit=1)
                    if odoo_product:
                        shipstaion_product_id = self.create({
                            'name': shipstation_product_name,
                            'product_id': odoo_product.id,
                            'shipstation_identification': product_id,
                            'shipstation_sku': sku,
                            'height': product_height,
                            'width': product_width,
                            'length': product_length,
                            'weight': product_weight or odoo_product.weight or False,
                            'shipstation_instance_id': instance.id
                        })
                        if odoo_product.weight == 0.0:
                            odoo_product.update({'weight': product_weight})
                        log_line.create_common_log_line_ept(
                            message="Shipstation Product for {} sku created".format(sku),
                            model_id=model_id, res_id=shipstaion_product_id.id,
                            operation_type='import', module='shipstation_ept',
                            log_line_type='success')
                    else:
                        if not auto_create_product:
                            log_line.create_common_log_line_ept(
                                message="Internal referance {} not found in ERP".format(sku),
                                model_id=model_id, operation_type='import',
                                module='shipstation_ept', log_line_type='fail')
                        else:
                            product = product_obj.create({
                                'name': shipstation_product_name,
                                'type': 'product',
                                'weight': product_weight or False,
                                'default_code': sku
                            })
                            log_line.create_common_log_line_ept(
                                message="Odoo Product for {} sku created".format(sku),
                                model_id=product_model_id, res_id=product.id,
                                product_id=product.id, operation_type='import',
                                module='shipstation_ept', log_line_type='success')

                            self.create({
                                'name': shipstation_product_name,
                                'product_id': product.id,
                                'shipstation_identification': product_id,
                                'shipstation_sku': sku,
                                'height': product_height,
                                'width': product_width,
                                'length': product_length,
                                'weight': product_weight or product.weight or False,
                                'shipstation_instance_id': instance.id
                            })
                            log_line.create_common_log_line_ept(
                                message="Shipstation Product for %s sku created" % sku,
                                model_id=product_model_id, res_id=product.id,
                                product_id=product.id, operation_type='import',
                                module='shipstation_ept', log_line_type='success')
            querystring['page'] += 1
        instance.sudo().write({'last_import_product': datetime.datetime.now()})
        return True

    def export_products_csv(self, instance):
        """
        to create a csv file of the shipstation products to import in shipstation front-end.
        @param instance: object of the shipstation.instance.ept
        @return: action that downloads the prepared file.
        """
        buffer = StringIO()
        delimiter, field_names = self.prepare_csv_file_header_and_delimiter()

        csv_writer = DictWriter(buffer, field_names, delimiter=delimiter)
        csv_writer.writer.writerow(field_names)

        products = self.search([('shipstation_instance_id', '=', instance.id)])
        rows = []
        for product in products:
            rows.append(product.prepare_row_data_for_csv())

        csv_writer.writerows(rows)
        buffer.seek(0)
        file_data = buffer.read().encode()
        attachment = self.env['ir.attachment'].create({
            'datas': base64.encodebytes(file_data),
            'name': "shipstation_export_product.csv",
        })

        res = {
            "type": "ir.actions.act_url",
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
            'nodestroy': False
        }

        return res

    def prepare_csv_file_header_and_delimiter(self):
        delimiter = ","
        field_names = ["SKU", "Name", "WarehouseLocation", "WeightOz", "Category", "Tag1", "Tag2", "Tag3", "Tag4",
                       "Tag5", "CustomsDescription", "CustomsValue", "CustomsTariffNo", "CustomsCountry",
                       "ThumbnailUrl", "UPC", "FillSKU", "Length", "Width", "Height", "UseProductName", "Active",
                       "ParentSKU", "IsReturnable"]

        return delimiter, field_names

    def prepare_row_data_for_csv(self):
        row = {
            "SKU": self.shipstation_sku,
            "Name": self.name,
            "WarehouseLocation": "",
            "WeightOz": self.weight,
            "Category": "",
            "Tag1": "",
            "Tag2": "",
            "Tag3": "",
            "Tag4": "",
            "Tag5": "",
            "CustomsDescription": "",
            "CustomsValue": "",
            "CustomsTariffNo": "",
            "CustomsCountry": "",
            "ThumbnailUrl": "",
            "UPC": "",
            "FillSKU": "",
            "Length": self.length,
            "Width": self.width,
            "Height": self.length,
            "UseProductName": "",
            "Active": "True",
            "ParentSKU": "",
            "IsReturnable": "False",
        }
        return row
