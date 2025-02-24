import base64
import io
import logging
from csv import DictWriter
from datetime import datetime
from io import StringIO

from odoo.exceptions import UserError
from odoo.tools.misc import xlsxwriter

from odoo import models, fields, _

_logger = logging.getLogger("Walmart Layer")

class PrepareProductForExport(models.TransientModel):
    """
    Model for adding Odoo products into Walmart Layer.
    @author: Nikul Alagiya on Date 07-January-2022.
    """
    _name = "walmart.prepare.product.for.export.ept"
    _description = "Prepare product for export in Walmart"

    export_method = fields.Selection([("direct", "Export in Walmart Layer"),
                                      ("csv", "Export in CSV file"), ("xlsx", "Export in XLSX file")],
                                     default="direct")
    walmart_instance_id = fields.Many2one("walmart.marketplace.ept")
    choose_file = fields.Binary(help="Select CSV file to upload.")
    file_name = fields.Char(help="Name of CSV file.")

    def prepare_product_for_export(self):
        """
        This method is used to export products in walmart layer as per selection.
        If "direct" is selected, then it will direct export product into walmart layer.
        If "csv" is selected, then it will export product data in CSV file, if user want to do some
        modification in name, description, etc. before importing into walmart.
        """
        _logger.info("Starting product exporting via %s method...", self.export_method)

        active_template_ids = self._context.get("active_ids", [])
        templates = self.env["product.template"].browse(active_template_ids)
        product_templates = templates.filtered(lambda template: template.detailed_type == "product")
        if not product_templates:
            raise UserError(_("It seems like selected products are not Storable products."))

        if self.export_method == "direct":
            return self.export_direct_in_walmart(product_templates)
        elif self.export_method == "csv":
            return self.export_csv_file(product_templates)
        else:
            return self.export_xlsx_file(product_templates)

    def export_direct_in_walmart(self, product_templates):
        """
        Creates new products or updates existing products in the walmart layer using the direct export method.
        @author: Nikul Alagiya on Date 07-January-2022.
        """
        walmart_instance = self.walmart_instance_id

        for product in product_templates.product_variant_ids:
            if product.default_code:
                self.create_or_update_walmart_layer_offer(walmart_instance, product)
        return True

    def create_or_update_walmart_layer_offer(self, walmart_instance, product):
        """ This method is used to create or update the walmart offer layer.
            @return: walmart_template
            @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 07 January 2022 .
        """
        walmart_template_obj = self.env["walmart.offer.ept"]

        walmart_template = walmart_template_obj.search([
            ("marketplace_id", "=", walmart_instance.id),
            ("walmart_sku", "=", product.default_code)], limit=1)

        walmart_product_vals = self.prepare_template_val_for_export_product_in_layer(product,
                                                                                     walmart_instance)
        if not walmart_template:
            walmart_template = walmart_template_obj.create(walmart_product_vals)
        else:
            walmart_template.write(walmart_product_vals)

        return walmart_template

    def prepare_template_val_for_export_product_in_layer(self, product, walmart_instance):
        """ This method is used to prepare a template Vals for export/update product
            from Odoo products to the walmart products layer.
            :param product: Record of odoo template.
            :param walmart_instance: Record of instance.
            @return: offer_vals
            @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 07 January 2020 .
        """
        offer_vals = {"product_id": product.id,
                      "marketplace_id": walmart_instance.id,
                      "product_name": product.name,
                      'walmart_sku': product.default_code,
                      'state': 'UNPUBLISHED'}
        return offer_vals

    def prepare_product_data_for_file(self, product_templates):
        """
        This method is use to prepare product data for export csv/xlsx file.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 07 January 2022 .
        """
        product_data_list = []
        for product in product_templates.product_variant_ids:
            if product.default_code:
                product_data = self.prepare_row_data_for_file(product)
                product_data_list.append(product_data)

        if not product_data_list:
            raise UserError(_("No data found to be exported.\n - SKU(s) are not set properly."))
        return product_data_list

    def export_csv_file(self, product_templates):
        """
        This method is used for export the odoo products in csv file.
        :param self: It contains the current class Instance
        :param product_templates: Records of odoo template.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 07 January 2022
        """
        product_data = self.prepare_product_data_for_file(product_templates)
        buffer = StringIO()
        field_names = list(product_data[0].keys())
        csv_writer = DictWriter(buffer, field_names, ",")
        csv_writer.writer.writerow(field_names)
        csv_writer.writerows(product_data)
        buffer.seek(0)
        file_data = buffer.read().encode()
        self.write({
            "choose_file": base64.encodebytes(file_data),
            "file_name": "walmart_export_product_"
        })

        return {
            "type": "ir.actions.act_url",
            "url": "web/content/?model=walmart.prepare.product.for.export.ept&id=%s&field=choose_file&download=true&"
                   "filename=%s.csv" % (self.id, self.file_name + str(datetime.now().strftime("%d/%m/%Y:%H:%M:%S"))),
            "target": self
        }

    def export_xlsx_file(self, product_templates):
        """
        This method is used to export the product data in xlsx file.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 07 January 2022 .
        """
        product_data = self.prepare_product_data_for_file(product_templates)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Map Product')
        header = list(product_data[0].keys())
        header_format = workbook.add_format({'bold': True, 'font_size': 10})
        general_format = workbook.add_format({'font_size': 10})
        worksheet.write_row(0, 0, header, header_format)
        index = 0
        for product in product_data:
            index += 1
            worksheet.write_row(index, 0, list(product.values()), general_format)
        workbook.close()
        b_data = base64.b64encode(output.getvalue())
        self.write({
            "choose_file": b_data,
            "file_name": "walmart_export_product_"
        })
        return {
            "type": "ir.actions.act_url",
            "url": "web/content/?model=walmart.prepare.product.for.export.ept&id=%s&field=choose_file&download=true&"
                   "filename=%s.xlsx" % (self.id, self.file_name + str(datetime.now().strftime("%d/%m/%Y:%H:%M:%S"))),
            "target": self
        }

    def prepare_row_data_for_file(self, product):
        """ This method is used to prepare a row data of csv file.
            @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 07 January 2022 .
        """
        row = {
            "Internal Reference": product.default_code,
            "Walmart SKU": product.default_code,
            "Product Title": product.name
        }
        return row
