import base64
import csv
import os
from io import StringIO, BytesIO

import xlrd
from odoo.exceptions import UserError

from odoo import models, fields, _

class WalmartProcessImportExport(models.TransientModel):
    _name = 'walmart.process.import.export'
    _description = 'Walmart Import Export Process Operations'

    operations = fields.Selection([('map_walmart_offers', 'Map Offers'),
                                   ('sync_walmart_offers', 'Sync Offers'),
                                   ('import_released_orders', 'Import Released Orders'),
                                   ('import_shipped_orders', 'Import Shipped Orders'),
                                   ('import_wfs_orders', 'Import WFS Orders'),
                                   ('import_order_by_id', "Import Order by Remote ID"),
                                   ('import_acknowledge_orders', 'Update Order Acknowledgement to Walmart'),
                                   ('get_reconciliation_report_date', 'Get Reconciliation Report'),
                                   ('is_update_order_status', 'Update Order Status'),
                                   ('is_update_stock', 'Update Stock'),
                                   ('import_wfs_inventory', 'Import WFS Inventory'),
                                   ('is_update_price', 'Update Price')])

    walmart_order_id = fields.Char()
    # Used for Import Released / Shipped Orders
    import_orders_start_date = fields.Datetime(string="Start Date")
    import_orders_end_date = fields.Datetime(string="End Date")

    # Used for Sync Offer
    is_update_image = fields.Boolean()
    is_update_inventory = fields.Boolean()
    is_validate_inventory = fields.Boolean()
    is_pricelist_update = fields.Boolean()
    skip_existing_product = fields.Boolean(help='Check if you want to skip existing product')
    location_id = fields.Many2one('stock.location', string="Source Location",
                                  domain=[('usage', '=', 'internal')])
    walmart_auto_create_product_not_found_in_odoo = fields.Boolean(
            'Auto Create Offer Not Found in Odoo',
            help="If it is ticked it will automatically \
            create offer[product] in odoo as well as in walmart")

    # Used for Import Walmart Offers
    marketplace_id = fields.Many2one('walmart.marketplace.ept', string='Walmart Marketplace',
                                     help="Walmart Marketplace")
    choose_file = fields.Binary()
    filename = fields.Char()
    delimiter = fields.Selection([('tab', 'Tab'), ('semicolon', 'Semicolon'), ('comma', 'Comma')],
                                 string="Separator",
                                 default='comma', required=True)

    auto_apply_adjustments = fields.Boolean(default=False, help="If it is set, the quants will be applied "
                                                                "automatically while importing stock.")

    @staticmethod
    def redirect_to_related_screen(action, queues, message):
        """
        @param message: success message in string
        @param action: action of the related view (dictionary)
        @param queues: list of ids of the related queues
        @return: action dictionary
        """
        action.update({
            "view_mode": 'tree' if len(queues) > 1 else 'form',
            "domain": "[('id', 'in', %s)]" % queues
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Operation completed successfully!'),
                'message': _(message),
                'type': 'success',
                'sticky': False,
                'next': action
            },
        }

    def send_error_display_notification(self, message, log_lines=[]):
        action = self.env["ir.actions.act_window"]._for_xml_id("walmart_ept.action_walmart_log_book_line_ept")
        action.update({
            "view_mode": 'tree' if len(log_lines) > 1 else 'form',
            "domain": "[('id', 'in', %s)]" % log_lines
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Operation failed!'),
                'message': _(message),
                'type': 'danger',
                'sticky': False,
                'next': action if log_lines else {'type': 'ir.actions.act_window_close'}
            },
        }

    def import_export_processes(self):
        """
            This method is used to import walmart sale order as well as to sync walmart offers.
            @param None.
            @return: True
        """
        walmart_offer_obj = self.env['walmart.offer.ept']
        sale_order_obj = self.env['sale.order']
        order_queue = self.env['walmart.order.queue.ept']
        marketplace = self.marketplace_id
        message = ""
        if self.operations == 'map_walmart_offers':
            self.import_products_from_file(walmart_offer_obj, marketplace)
            message = "Your file has been imported successfully..."

        elif self.operations == 'sync_walmart_offers':
            """
            This Sync Walmart Offer to Working with get item report. Previous development remove.
            """
            vals = {
                'auto_create_product': self.walmart_auto_create_product_not_found_in_odoo,
                'walmart_instance_id': self.marketplace_id.id,
                'import_stock': self.is_update_inventory,
                'is_product_image': self.is_update_image,
                'update_price_in_pricelist': self.is_pricelist_update,
                'is_validate_inventory': self.is_validate_inventory,
                'skip_existing_product': self.skip_existing_product,
            }
            product_sync_report = self.env['walmart.product.sync.report.ept']
            product_sync_report_id = product_sync_report.create(vals)
            action = self.env["ir.actions.act_window"]._for_xml_id("walmart_ept.action_walmart_product_sync_tree_ept")
            action.update({
                'view_mode': 'form',
                'views': [(False, 'form')],
                'res_id': product_sync_report_id.id,
            })
            return action

        elif self.operations == 'import_released_orders' \
                or self.operations == 'import_shipped_orders':
            start_date = False
            end_date = False
            order_type = ""
            created_by = "import"
            if self.import_orders_start_date and self.import_orders_end_date:
                start_date = self.import_orders_start_date
                end_date = self.import_orders_end_date

            if self.operations == 'import_released_orders':
                order_status = 'Created'
                action = self.env["ir.actions.act_window"]._for_xml_id("walmart_ept.action_walmart_order_queue_ept")
            else:
                order_status = 'Delivered'
                action = self.env["ir.actions.act_window"]._for_xml_id("walmart_ept.action_walmart_shipped_order_queue_ept")
            order_queues = order_queue.walmart_create_order_queues(marketplace, start_date, end_date, order_status, created_by, order_type)
            message = "Import process completed ..."
            return self.redirect_to_related_screen(action, order_queues, message)

        elif self.operations == 'import_wfs_orders':
            if marketplace.is_selling_on_wfs == False:
                raise UserError(_("First You Need TO Active WFS selling Operation"))
            start_date = False
            end_date = False
            if self.import_orders_start_date and self.import_orders_end_date:
                start_date = self.import_orders_start_date
                end_date = self.import_orders_end_date
            order_status = 'Delivered'
            order_type = 'wfs_order'
            created_by = "import"
            order_queues = order_queue.with_context(wfs_order=True).walmart_create_order_queues(marketplace, start_date, end_date, order_status, created_by, order_type)
            message = "Import process completed ..."
            action = self.env["ir.actions.act_window"]._for_xml_id("walmart_ept.action_walmart_wfs_order_queue_ept")
            return self.redirect_to_related_screen(action, order_queues, message)

        elif self.operations == 'import_order_by_id':
            created_orders, log_lines = sale_order_obj.import_walmart_orders(marketplace, order_ids=self.walmart_order_id)
            if created_orders:
                message = "Order Imported..."
                action = self.env["ir.actions.act_window"]._for_xml_id("walmart_ept.action_walmart_sales_order_ept")
                return self.redirect_to_related_screen(action, created_orders, message)

            message = "Failed to import the given Orders. For more information, please review the log lines!"
            return self.send_error_display_notification(message, log_lines)

        elif self.operations == 'import_acknowledge_orders':
            sale_order_obj.acknowledge_walmart_orders(marketplace)
            message = "Acknowledge process completed ..."

        elif self.operations == 'is_update_order_status':
            sale_order_obj.walmart_update_order_status(marketplace)
            message = "Update order status process completed ..."

        elif self.operations == 'is_update_stock':
            feed_histories, log_lines = walmart_offer_obj.export_stock_in_walmart(marketplace)
            if feed_histories:
                message = "Stock update process completed ..."
                action = self.env["ir.actions.act_window"]._for_xml_id("walmart_ept.action_walmart_feed_submission_history")
                return self.redirect_to_related_screen(action, feed_histories, message)
            message = "Failed to update the stock in Walmart. For more information, please review the log lines!"
            return self.send_error_display_notification(message, [])

        elif self.operations == 'import_wfs_inventory':
            auto_apply_adjustments = self.auto_apply_adjustments,
            walmart_offer_obj.import_wfs_inventory(marketplace, auto_apply_adjustments)
            message = "Import WFS Inventory process completed ..."

        elif self.operations == 'is_update_price':
            feed_histories, log_lines = walmart_offer_obj.export_price_in_walmart(marketplace)
            if feed_histories:
                message = "Price update process completed ..."
                action = self.env["ir.actions.act_window"]._for_xml_id(
                    "walmart_ept.action_walmart_feed_submission_history")
                return self.redirect_to_related_screen(action, feed_histories, message)
            message = "Failed to update the price in Walmart. For more information, please review the log lines!"
            return self.send_error_display_notification(message, [])

        elif self.operations == 'get_reconciliation_report_date':
            accounting_module = self.env["product.product"].search_installed_module_ept('account_accountant')
            if not accounting_module:
                raise UserError(_("You do not have the Accounting module installed."))
            report_ids = self.env['walmart.reconciliation.report.ept'].get_walmart_report_date(marketplace)
            action = {'name': _('Reconciliation Reports'),
                      'type': 'ir.actions.act_window',
                      'res_model': 'walmart.reconciliation.report.ept',
                      'target': 'current',
                      'view_mode': 'tree,form',
                      'domain': [('id', 'in', report_ids.ids)]}
            return action
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Operation Successfully Completed!'),
                'message': _(message),
                'type': 'success',
                'sticky': False,
                # 'next': {
                #     'type': 'ir.actions.client',
                #     'tag': 'reload',
                # }
            },
        }

    def import_products_from_file(self, walmart_offer_obj, marketplace):
        """
        This method is use to import product from csv,xlsx,xls.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 8 January 2022 .
        Task_id: 181483 - Map products
        """
        try:
            if os.path.splitext(self.filename)[1].lower() not in ['.csv', '.xls', '.xlsx']:
                raise UserError(_("Invalid file format. You are only allowed to upload .csv, .xlsx file."))
            if os.path.splitext(self.filename)[1].lower() == '.csv':
                self.import_products_from_csv(walmart_offer_obj, marketplace)
            else:
                self.import_products_from_xls(walmart_offer_obj, marketplace)
        except Exception as error:
            raise UserError(_("Receive the error while import file. %s", error))

    def import_products_from_csv(self, walmart_offer_obj, marketplace):
        """
        This method used to import product using csv file in Walmart offer.
        @author: Nikul Alagiya on Date 08 January 2022.
        """
        file_data = self.read_file()
        self.validate_required_csv_header(file_data.fieldnames)
        self.create_products_from_file(file_data, walmart_offer_obj, marketplace)
        return True

    def import_products_from_xls(self, walmart_offer_obj, marketplace):
        """
        This method used to import product using xls file in Walmart layer.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 08 January 2022 .
        Task_id: 181483 - Map products
        """
        header, product_data = self.read_xls_file()
        self.validate_required_csv_header(header)
        self.create_products_from_file(product_data, walmart_offer_obj, marketplace)
        return True

    def validate_required_csv_header(self, header):
        """ This method is used to validate required csv header while csv file import for products.
            @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 08 January 2022 .
            Task_id: 181483 - Map products
        """
        required_fields = ["Internal Reference", "Walmart SKU", "Product Title"]

        for required_field in required_fields:
            if required_field not in header:
                raise UserError(_("Required column is not available in File."))

    def create_products_from_file(self, file_data, walmart_offer_obj, marketplace):
        """
        This method is used to create products in Walmart Offer layer from the file.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 08 January 2022 .
        Task_id: 181483 - Map products
        """
        common_log_line_obj = self.env["common.log.lines.ept"]
        product_obj = self.env["product.product"]
        row_no = 0
        for record in file_data:
            row_no += 1
            message = ""
            default_code = record["Internal Reference"]
            walmart_sku = record["Walmart SKU"]
            product_title = record["Product Title"]
            if not default_code or not walmart_sku or not product_title:
                message += "Internal Reference Or Walmart SKU Or Product Title Not As Per Odoo Product in file at row " \
                           "%s " % row_no
                common_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                        model_name='walmart.offer.ept',
                                                        log_line_type='fail', mismatch_details=True,
                                                        operation_type="import")
                continue

            self.create_walmart_offer_and_odoo_product(walmart_offer_obj, product_obj, marketplace, default_code,
                                                       walmart_sku, product_title)
            if row_no % 10 == 0:
                self._cr.commit()
        return True

    def create_walmart_offer_and_odoo_product(self, walmart_offer_obj, product_obj, marketplace, default_code,
                                              walmart_sku, product_title):
        """
        This method to use first check walmart offer exist or not. if not then check odoo product
         if exist then create walmart offer otherwise first create odoo product after that walmart offer create.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 08 January 2022 .
        Task_id: 181483 - Map products
        """
        if not walmart_offer_obj.search([('walmart_sku', '=', walmart_sku),
                                         ('marketplace_id', '=', marketplace.id)], limit=1):
            odoo_product = product_obj.search(
                    [('default_code', '=', default_code)], limit=1)
            if not odoo_product:
                odoo_product = product_obj.create({'name': product_title,
                                                   'type': 'product',
                                                   'default_code': default_code})

            walmart_offer_obj.create({'product_id': odoo_product.id,
                                      'marketplace_id': marketplace.id,
                                      'walmart_sku': walmart_sku,
                                      'product_name': product_title,
                                      'state': 'UNPUBLISHED'
                                      })

    def read_file(self):
        """
        This method reads .csv file
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 08 January 2022.
        """
        import_file = BytesIO(base64.decodebytes(self.choose_file))
        file_read = StringIO(import_file.read().decode())
        reader = csv.DictReader(file_read, delimiter=",")

        return reader

    def read_xls_file(self):
        """
        This method is use to read the xlsx file data.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 08 January 2022 .
        Task_id: 181483 - Map products
        """
        validation_header = []
        product_data = []
        sheets = xlrd.open_workbook(file_contents=base64.b64decode(self.choose_file.decode('UTF-8')))
        header = dict()
        is_header = False
        for sheet in sheets.sheets():
            for row_no in range(sheet.nrows):
                if not is_header:
                    headers = [d.value for d in sheet.row(row_no)]
                    validation_header = headers
                    [header.update({d: headers.index(d)}) for d in headers]
                    is_header = True
                    continue
                row = dict()
                [row.update({k: sheet.row(row_no)[v].value}) for k, v in header.items() for c in
                 sheet.row(row_no)]
                product_data.append(row)
        return validation_header, product_data

