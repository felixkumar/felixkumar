import base64
import csv
import io
import logging
import os
import zipfile
import requests
from datetime import datetime
from io import StringIO, BytesIO

from odoo.exceptions import ValidationError

from odoo import api, models, fields, _

_logger = logging.getLogger("walmart_logger_ept")

class WalmartProductSyncReport(models.Model):
    _name = 'walmart.product.sync.report.ept'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Walmart Product Sync Report Offers'

    name = fields.Char('Reference')
    requested_date = fields.Datetime(string="Requested Date", help='Product Sync request date enter')
    attachment_id = fields.Many2one('ir.attachment', string='Attachment File', help='select Attachment file')
    auto_create_product = fields.Boolean(default=False, copy=False, help='Product not in products then create')
    walmart_instance_id = fields.Many2one('walmart.marketplace.ept', string='Instance', help='Walmart Instance')
    state = fields.Selection(selection=[('draft', "Draft"), ('request_sent', "Sent"),
                                        ('downloaded', "Downloaded"), ('processed', "Processed")],
                             default='draft', help='Product sync status', tracking=True)
    update_price_in_pricelist = fields.Boolean(default=False, copy=False, help='Update price in price list')
    user_id = fields.Many2one('res.users', string='Requested User', default=lambda self: self.env.user,
                              help='Select customer')
    is_product_image = fields.Boolean(default=False, copy=False, help='Update Product Image ?')
    import_stock = fields.Boolean(string='Create Product Inventory?', default=False, copy=False,
                                  help='Create Product Inventory')
    log_book_id = fields.Many2one('common.log.book.ept', string='Log Book', help='Select Log Book here')
    is_validate_inventory = fields.Boolean(default=False, copy=False, help='Import stock after validate'
                                                                           ' inventory or not.')
    skip_existing_product = fields.Boolean(help='Check if you want to skip existing product')
    report_request_id = fields.Char(string="Report Request Id",
                                    help="It is request id returned by the Create Report Request API")
    request_status = fields.Char(string="Request Status", help="Request status of the report returned from the Walmart API!")

    def create_report_request(self):
        instance = self.walmart_instance_id
        walmart_conn_obj = instance.get_walmart_connection()
        walmart_log_line_obj = self.env['common.log.lines.ept']
        try:
            response = walmart_conn_obj.create_report_request('ITEM', 'v3').post()
            if not response:
                message = 'Something went wrong while creating the Report Request in Walmart...!'
                walmart_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                               model_name=self._name, walmart_marketplace_id=instance.id,
                                                               log_line_type='fail', mismatch_details=False,
                                                               operation_type="import")
            request_id = response.get("requestId", False)
            if request_id:
                self.write({"report_request_id": request_id, 'state': 'request_sent'})
        except Exception as error:
            message = 'An Exception occurred while creating report request!\n%s' % str(error)
            walmart_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                            model_name=self._name, walmart_marketplace_id=instance.id,
                                                            log_line_type='fail', mismatch_details=False,
                                                            operation_type="import")

    def report_request_status(self):
        instance = self.walmart_instance_id
        walmart_conn_obj = instance.get_walmart_connection()
        walmart_log_line_obj = self.env['common.log.lines.ept']
        try:
            request_id = self.report_request_id
            response = walmart_conn_obj.report_request_status(request_id).all()
            if not response:
                message = 'Something went wrong while checking the status of Item Report Request in Walmart...!'
                walmart_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                                model_name=self._name,
                                                                walmart_marketplace_id=instance.id,
                                                                log_line_type='fail', mismatch_details=False,
                                                                operation_type="import")
            request_status = response.get("requestStatus", False)
            self.write({'request_status': request_status})
            if request_status == 'READY':
                self.download_report_url()
            elif request_status == 'ERROR':
                message = 'Returned Error while fetching Item report status from Walmart...!'
                walmart_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                                model_name=self._name,
                                                                walmart_marketplace_id=instance.id,
                                                                log_line_type='fail', mismatch_details=False,
                                                                operation_type="import")
            elif not request_status:
                message = 'Cannot be able to get the item request status from the Walmart...!'
                walmart_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                                model_name=self._name,
                                                                walmart_marketplace_id=instance.id,
                                                                log_line_type='fail', mismatch_details=False,
                                                                operation_type="import")

        except Exception as error:
            message = 'An Exception occurred while getting report request status from Walmart!\n%s' % str(error)
            walmart_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                            model_name=self._name,
                                                            walmart_marketplace_id=instance.id,
                                                            log_line_type='fail', mismatch_details=False,
                                                            operation_type="import")

    def download_report_url(self):
        instance = self.walmart_instance_id
        walmart_conn_obj = instance.get_walmart_connection()
        walmart_log_line_obj = self.env['common.log.lines.ept']
        try:
            request_id = self.report_request_id
            response = walmart_conn_obj.download_report_url().all(requestId=request_id)
            response = requests.get(response.get('downloadURL'))
            # response = walmart_conn_obj.send_request('GET', response.get('downloadURL'))
            if not response:
                message = 'Something went wrong while downloading the Item report from Walmart...!'
                walmart_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                                model_name=self._name,
                                                                walmart_marketplace_id=instance.id,
                                                                log_line_type='fail', mismatch_details=False,
                                                                operation_type="import")
            else:
                path = "/tmp"
                z = zipfile.ZipFile(io.BytesIO(response.content))
                z.extractall(path=path)
                for filename in reversed(z.namelist()):
                    if os.path.splitext(filename)[1].lower() == '.csv':
                        file_obj = open('/tmp/%s' % filename, 'rb')
                        attachment = self._create_attachment(filename, 'walmart.product.sync.report.ept', self.id,
                                                             file_obj)
                        self.write({'attachment_id': attachment.id, 'state': 'downloaded'})
                        file_obj.close()
                        self.message_post(body=_("<b>Product Sync Report Downloaded</b>"),
                                          attachment_ids=attachment.ids)
                return True
        except Exception as error:
            message = 'An Exception occurred while downloading Item report from Walmart!\n%s' % str(error)
            walmart_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                            model_name=self._name,
                                                            walmart_marketplace_id=instance.id,
                                                            log_line_type='fail', mismatch_details=False,
                                                            operation_type="import")

    @api.model_create_multi
    def create(self, vals_list):
        """         Sequence number wise record create
                    @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 06 January 2022 .
                    Task_id: 181481 - Configuration settings & Instance settings
                """
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('walmart.product.sync.report.sequence.or.ept')
        results = super(WalmartProductSyncReport, self).create(vals_list)
        for res in results:
            res.create_report_request()
        return results

    def walmart_product_process_report(self):
        """        This method is to use downloaded csv file read and process in product.
                   @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 06 January 2022 .
                   Task_id: 181482 - Sync product from Walmart (Based on report)
               """

        self._validate_report()
        walmart_offer = self.env['walmart.offer.ept']
        system_product = self.env['product.product']

        def get_return_date(date):
            """
            Fetch to formatted date.
            :param date:
            :return: formatted date.
            """
            return datetime.strptime(date.replace('/', '-'), '%m-%d-%Y').date() if date else ''

        instance = self.walmart_instance_id

        # Read CSV File
        import_file = BytesIO(base64.decodebytes(self.attachment_id.datas))
        csv_file = StringIO(import_file.read().decode())
        product_sync_reports_data = csv.DictReader(csv_file, delimiter=',')
        rows = list(product_sync_reports_data)
        total_rows = len(rows)
        # Walmart Product Process for Walmart Product Update or Create
        stock_inventory = self.walmart_product_process(rows, total_rows, walmart_offer, instance, get_return_date,
                                                       system_product)
        self.import_walmart_stock(instance, stock_inventory)
        self.state = 'processed'
        return True

    def auto_create_item_request_report(self, **args):
        instance_id = args.get('instance_id')
        product_sync_report = self.env['walmart.product.sync.report.ept']
        if instance_id:
            instances = self.env['walmart.marketplace.ept'].browse(instance_id)
            for instance in instances:
                vals = {
                    'auto_create_product': True,
                    'walmart_instance_id': instance.id,
                    'import_stock': True,
                    'is_product_image': instance.update_product_image,
                    'update_price_in_pricelist': True,
                    'is_validate_inventory': instance.create_product_inventory,
                    'skip_existing_product': True,
                }

                product_sync_report.create(vals)
        return True

    def auto_process_item_request_report(self, **args):
        instance_id = args.get('instance_id')
        product_sync_report = self.env['walmart.product.sync.report.ept']
        if instance_id:
            instances = self.env['walmart.marketplace.ept'].browse(instance_id)
            for instance in instances:
                offer_reports = self.search([('walmart_instance_id', '=', instance.id)])
                for offer_report in offer_reports:
                    offer_report.report_request_status()
                    offer_report.walmart_product_process_report()
        return True


    def import_walmart_stock(self, instance, stock_inventory):
        """        This method to use import walmart stock to odoo.
                   :param instance :Selected Marketplace
                   :param stock_inventory : like {'product_id':Qty, 52:20, 53:60, 89:23} to import stock
                   @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 06 January 2022 .
                   Task_id: 181482 - Sync product from Walmart (Based on report)
               """
        if self.import_stock and stock_inventory:
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1)
            inventory_name = 'Inventory For Instance "%s" And Walmart Location "%s"' % (
                instance.name, warehouse.lot_stock_id.name)
            self.env["stock.quant"].create_inventory_adjustment_ept(stock_inventory, warehouse.lot_stock_id,
                                                                    self.is_validate_inventory, inventory_name)

    def walmart_product_process(self, rows, total_rows, walmart_offer, instance, get_return_date, system_product):
        """ This method to use walmart product process.
            @return: stock_inventory like {'product_id':Qty, 52:20, 53:60, 89:23}
            @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 06 January 2022 .
            Task_id: 181482 - Sync product from Walmart (Based on report)
        """
        stock_inventory = {}
        product_ids_list = []
        number = 0
        walmart_log_line_obj = self.env['common.log.lines.ept']

        for count, item_report in enumerate(rows, start=1):
            number += 1
            if number == 10:
                self._cr.commit()
                number = 0

            walmart_product_sku = item_report.get('SKU', '').strip()
            fulfillment_type = item_report.get('FULFILLMENT TYPE')
            _logger.info("Processing item report product:{} row {} out of {}".format(
                    walmart_product_sku, count, total_rows))
            walmart_product = walmart_offer.search([('walmart_sku', '=', walmart_product_sku),
                                                    ('marketplace_id.id', '=', instance.id),
                                                    ('fulfillment_by','=',fulfillment_type)], limit=1)
            if self.skip_existing_product and walmart_product:
                continue
            elif walmart_product and walmart_product.product_id and not self.skip_existing_product:
                walmart_product_price, walmart_product = self._create_update_walmart_offer(item_report,
                                                                                           get_return_date,
                                                                                           walmart_product,
                                                                                           walmart_product.product_id)
                self.prepare_update_price_list_and_inventory_and_image(walmart_product, walmart_product_price,
                                                                       instance,
                                                                       item_report, product_ids_list,
                                                                       stock_inventory)
            else:
                odoo_product = system_product.search([('default_code', '=', walmart_product_sku),'|',
                                                      ('active','=',False),('active','=',True)],
                                                     limit=1)
                if odoo_product:
                    walmart_product_price, walmart_product = self._create_update_walmart_offer(item_report,
                                                                                               get_return_date,
                                                                                               walmart_product,
                                                                                               odoo_product)
                    self.prepare_update_price_list_and_inventory_and_image(walmart_product, walmart_product_price,
                                                                           instance, item_report, product_ids_list,
                                                                           stock_inventory)
                else:
                    if self.auto_create_product:
                        product = self._create_odoo_product(item_report, odoo_product)
                        walmart_product_price, walmart_product = self._create_update_walmart_offer(item_report,
                                                                                                   get_return_date,
                                                                                                   walmart_product,
                                                                                                   product)
                        self.prepare_update_price_list_and_inventory_and_image(walmart_product,
                                                                               walmart_product_price,
                                                                               instance, item_report,
                                                                               product_ids_list, stock_inventory)
                    else:
                        message = "Walmart product not found with SKU:{} at row number:{}".format(
                                walmart_product_sku, count)
                        walmart_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                                        model_name=self._name,
                                                                        walmart_marketplace_id=instance.id,
                                                                        log_line_type='fail', mismatch_details=False,
                                                                        operation_type="import")

        return stock_inventory

    def prepare_update_price_list_and_inventory_and_image(self, walmart_product, walmart_product_price, instance,
                                                          item_report, product_ids_list, stock_inventory):
        """ This method to use odoo product price-list update, stock inventory and Odoo product image.
        :param walmart_product browse object of walmart product
        :param walmart_product_price Walamart price to import in price-list
        :param instance walmart marketplace
        :param item_report csv file to one ny one report in item report
        :param product_ids_list list of product ids in walmart product
        :param stock_inventory to diction of product and Quantity used in prepare_val_stock_inventory method.
            @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 06 January 2022 .
            Task_id: 181482 - Sync product from Walmart (Based on report)
        """
        self.update_price_list(walmart_product, walmart_product_price, instance)
        self.prepare_val_stock_inventory(item_report, walmart_product, product_ids_list, stock_inventory)
        self.update_odoo_product_image(walmart_product, item_report)

    def select_product_category(self, item_report):
        """
        This method to use product category selection.
        @return walmart product category
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 06 January 2022 .
        Task_id: 181482 - Sync product from Walmart (Based on report)
        """
        product_category_id = self.env['walmart.product.type.ept']
        product_category = item_report.get("Product Category", '').strip()
        if product_category:
            product_category_id = product_category_id.search([('name', '=ilike', product_category)])
            if not product_category_id:
                product_category_id = product_category_id.create({'name': product_category})
        return product_category_id

    def walmart_get_product_report(self):
        """
          This method to use get Walmart product report.
          @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 06 January 2022 .
          Task_id: 181482 - Sync product from Walmart (Based on report)
        """
        self._get_item_report_ept(self.walmart_instance_id)
        self.requested_date = fields.Datetime.now()
        self.state = 'downloaded'
        message = "Download completed."
        return {
            'effect': {
                'fadeout': 'slow',
                'message': message,
                'img_url': '/web/static/src/img/smile.svg',
                'type': 'rainbow_man',
            }
        }

    def walmart_mismatch_details(self):
        """
        This method to use Walmart mismatch details to Error Occur.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 06 January 2022 .
        Task_id: 181482 - Sync product from Walmart (Based on report)
        """
        action = self.env["ir.actions.act_window"]._for_xml_id("walmart_ept.action_walmart_log_book_ept")
        action.update({
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_id': self.log_book_id.id,
        })
        return action

    def _get_item_report_ept(self, instance):
        """
        This method to use get Walmart item report.
        @param : walmart instance
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 06 January 2022 .
        Task_id: 181482 - Sync product from Walmart (Based on report)
        """
        walmart_log_line_obj = self.env['common.log.lines.ept']

        walmart_conn_obj = instance.get_walmart_connection()

        try:
            response = walmart_conn_obj.report(report_type='ITEM', report_version='v3').all()
            if not response:
                message = 'Item Report not found from Walmart...!'
                walmart_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                               model_name=self._name, walmart_marketplace_id=instance.id,
                                                               log_line_type='fail', mismatch_details=False,
                                                               operation_type="import")
            else:
                path = "/tmp"
                z = zipfile.ZipFile(io.BytesIO(response))
                z.extractall(path=path)
                for filename in reversed(z.namelist()):
                    if os.path.splitext(filename)[1].lower() == '.csv':
                        file_obj = open('/tmp/%s' % filename, 'rb')
                        attachment = self._create_attachment(filename, 'walmart.product.sync.report.ept', self.id,
                                                             file_obj)
                        self.write({'attachment_id': attachment.id})
                        file_obj.close()
                        self.message_post(body=_("<b>Product Sync Report Downloaded</b>"),
                                          attachment_ids=attachment.ids)
        except Exception as error:
            _logger.exception(error)
            raise ValidationError(str(error))

        return True

    def _create_attachment(self, file_name, model_name, sync_id, file_read):
        attachment_id = self.env['ir.attachment'].create(
                {'name': file_name,
                 'res_name': file_name,
                 'res_model': model_name,
                 'res_id': sync_id,
                 'datas': base64.b64encode(file_read.read()),
                 })
        return attachment_id

    def _validate_report(self):
        if not self.attachment_id:
            raise ValidationError(_("There is no any files are attached with this record."))
        return True

    def _create_update_walmart_offer(self, item_report, get_return_date, walmart_product, odoo_product):
        """ This method to use create and update walmart offer.
            @return walmart offer price
            @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 06 January 2022 .
            Task_id: 181482 - Sync product from Walmart (Based on report)
        """
        product_name = item_report.get("Product Name", '').strip()
        sku = item_report.get("SKU", '').strip()
        instance_id = self.walmart_instance_id.id
        gtin = item_report.get("GTIN", '').strip()
        upc = item_report.get("UPC", '').strip()
        wpid = item_report.get("WPID", '').strip()
        status_reason = item_report.get("Status Change Reason", '').strip()
        lifecycle_status = item_report.get("Lifecycle Status", '').strip()
        walmart_product_item_id = item_report.get("Item ID", '').strip()
        offer_start_date = get_return_date(item_report.get("Offer Start Date", '').strip())
        offer_end_date = get_return_date(item_report.get("Offer End Date", '').strip())
        offer_creation_date = get_return_date(item_report.get("Item Creation Date", '').strip())
        offer_last_update_date = get_return_date(item_report.get("Item Last Updated", '').strip())
        walmart_product_url = item_report.get("Item Page URL", '').strip()
        review_count = item_report.get("Reviews Count", '').strip()
        avg_rating = item_report.get("Average Rating", '').strip()
        walmart_product_price = item_report.get("Price", '').strip()
        publish_status = item_report.get("Publish Status", '').strip()
        fulfillment_type = item_report.get('Fulfillment Type')
        if walmart_product:
            walmart_product.write(
                    {"product_category": self.select_product_category(item_report).id,
                     "walmart_product_status_reason": status_reason,
                     "walmart_product_lifecycle_status": lifecycle_status,
                     "walmart_product_item_id": walmart_product_item_id,
                     "walmart_product_offer_start_date": offer_start_date or False,
                     "walmart_product_offer_end_date": offer_end_date or False,
                     "walmart_product_offer_creation_date": offer_creation_date or False,
                     "walmart_product_offer_last_update_date": offer_last_update_date or False,
                     "walmart_product_url": walmart_product_url,
                     "walmart_product_review_count": review_count,
                     "walmart_product_avg_rating": avg_rating,
                     "fulfillment_by" : fulfillment_type,
                     "state": publish_status,
                     "exported_in_walmart" : True})
            if not walmart_product.product_id:
                walmart_product.write({"product_id": odoo_product.id})
        else:
            walmart_product = walmart_product.create(
                    {"product_name": product_name,
                     "marketplace_id": instance_id,
                     "walmart_sku": sku,
                     "gtin": gtin,
                     "upc": upc,
                     "wpid": wpid,
                     "fulfillment_by": fulfillment_type,
                     "product_id": odoo_product.id,
                     "product_category": self.select_product_category(item_report).id,
                     "walmart_product_status_reason": status_reason,
                     "walmart_product_lifecycle_status": lifecycle_status,
                     "walmart_product_item_id": walmart_product_item_id,
                     "walmart_product_offer_start_date": offer_start_date or False,
                     "walmart_product_offer_end_date": offer_end_date or False,
                     "walmart_product_offer_creation_date": offer_creation_date or False,
                     "walmart_product_offer_last_update_date": offer_last_update_date or False,
                     "walmart_product_url": walmart_product_url,
                     "walmart_product_review_count": review_count,
                     "walmart_product_avg_rating": avg_rating,
                     "state": publish_status,
                     "exported_in_walmart" : True})
        return walmart_product_price, walmart_product

    def _create_walmart_log_book(self, model, instance):
        """
        This method use for any error occur then first one time create book. 
        """
        walmart_log_book_obj = self.env['common.log.book.ept']
        log_book_id = walmart_log_book_obj.create_common_log_book(
                model_id=model, module='walmart_ept', process_type='import',
                instance_field='walmart_marketplace_id', instance=instance)
        return log_book_id

    def update_price_list(self, walmart_product, walmart_product_price, instance):
        """
        This method for product price-list item update price-list otherwise create price-list item.
        use set_product_price_ept method in common connector.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 06 January 2022 .
        Task_id: 181482 - Sync product from Walmart (Based on report)
        """
        if self.update_price_in_pricelist:
            pricelist_id = instance.pricelist_id
            if pricelist_id:
                pricelist_id.set_product_price_ept(
                        walmart_product.product_id.id, walmart_product_price)

    def update_odoo_product_image(self, walmart_product, item_report):
        """
        This method to odoo product image not found then update product image.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 06 January 2022 .
        Task_id: 181482 - Sync product from Walmart (Based on report)
        """
        if self.is_product_image:
            odoo_product = walmart_product.product_id
            walmart_product_image_url = item_report.get("Primary Image URL", '').strip()
            try:
                walmart_image = self.env['common.product.image.ept'].get_image_ept(walmart_product_image_url)
                if not odoo_product.image_1920:
                    odoo_product.write({"image_1920": walmart_image})
            except Exception as err:
                _logger.exception(
                        "Got an exception while fetching image {}".format(err))

    def _create_odoo_product(self, item_report, odoo_product):
        """
                    This method is use to create Odoo product.
                    @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 06 January 2022 .
                    Task_id: 181482 - Sync product from Walmart (Based on report)
                    """
        product_name = item_report.get("Product Name", '').strip()
        sku = item_report.get("SKU", '').strip()

        product = odoo_product.create(
                {"name": product_name,
                 "default_code": sku,
                 "detailed_type": "product"})
        return product

    def prepare_val_stock_inventory(self, item_report, walmart_product, product_ids_list, stock_inventory):
        """ This method is used to walmart product base on the inventory count.
                @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 06 January 2022 .
                Task_id: 181482 - Sync product from Walmart (Based on report)
            """
        product_quantity = item_report.get("INVENTORY COUNT", '').strip()
        product_id = walmart_product.product_id
        if product_id not in product_ids_list:
            stock_inventory_line = {
                product_id.id: product_quantity,
            }
            stock_inventory.update(stock_inventory_line)
            product_ids_list.append(product_id)
