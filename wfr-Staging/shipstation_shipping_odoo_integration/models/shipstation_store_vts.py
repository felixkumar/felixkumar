# -*- coding: utf-8 -*-
import csv
import base64
import logging
import json
import os
import os.path
from contextlib import contextmanager
from io import StringIO
from csv import DictWriter
from odoo import fields, models, api, _, registry, SUPERUSER_ID
from datetime import datetime
from requests import request
from threading import Thread
from dateutil.relativedelta import relativedelta
import time
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger("Shipstation")


class shipstation_store_vts(models.Model):
    _name = 'shipstation.store.vts'
    _description = 'Shipstation Store'
    _rec_name = 'store_name'

    store_id = fields.Char(string='Store Id')
    store_name = fields.Char(string='Store Name')
    marketplace_id = fields.Char(string='MarkerPlace Id')
    marketplace_name = fields.Char(string='MarkerPlace Name')
    acc_number = fields.Char(string='Account Number')
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse")

    shipstation_to_date = fields.Datetime(string='To Date')
    last_modification_date = fields.Datetime(string="From Date")
    process_msg = fields.Char(string='Message')
    shipstation_order_status = fields.Selection([('awaiting_payment', 'awaiting_payment'),
                                                 ('awaiting_shipment', 'awaiting_shipment'),
                                                 ('shipped', 'shipped'),
                                                 ('on_hold', 'on_hold'),
                                                 ('cancelled', 'cancelled')], default="shipped",
                                                string="Shipstation Import Order Status",
                                                help="When Order will import at that time we are condidering this shipment status.")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse")
    import_shipstation_shipment = fields.Boolean("Is Automatic Import Shipstation Shipment.?", default=False,
                                                 copy=False,
                                                 help="If True then auto import tracking number and shipping cost from shipstation.")
    import_shipstation_order = fields.Boolean("Is Automatic Import Shipstation orders.?", default=False, copy=False,
                                              help="If True then auto import Orders in odoo from shipstation.")
    pricelist_id = fields.Many2one('product.pricelist', string='Product Pricelist')
    add_vat_line = fields.Boolean(string='Add VAT ?')
    create_customer_from_data = fields.Boolean(string='Is Create Customer From Data?')
    carrier_id = fields.Many2one('delivery.carrier', string='Shipping Method')
    shipstation_configuration_id = fields.Many2one('shipstation.odoo.configuration.vts',
                                                   string='Shipstation Configuration')

    def import_sale_orders_using_cron(self):
        store_ids = self.search([('import_shipstation_order', '=', True)])
        for store_id in store_ids:
            _logger.info("{0} Shipstation Import Order Process Cron Start".format(store_id.store_name))
            store_id.sudo().import_order_from_shipstation_using_cron()
            _logger.info("{0} Shipstation Import Order Process Cron Finish".format(store_id.store_name))
            store_id.sudo().write({'process_msg': ' Shipstation Order Import Process Completed.'})
            time.sleep(8)
        _logger.info("Shipstation Import Order order Cron Finished")
        return True

    def import_order_from_shipstation_with_thred(self):
        dbname = self.env.cr.dbname
        db_registry = registry(dbname)
        with api.Environment.manage(), db_registry.cursor() as cr:
            env_thread1 = api.Environment(cr, SUPERUSER_ID, self._context)
            t = Thread(target=self.import_order_from_shipstation, args=())
            t.start()
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "Yeah! Shipstation Import Process Started.",
                'img_url': '/web/static/img/smile.svg',
                'type': 'rainbow_man',
            }
        }

    def create_product_from_shipstation(self, product_name, product_sku):
        category_id = self.env.ref('product.product_category_all')

        type = 'product'
        if 'discount' in product_name.lower() or 'ship' in product_name.lower() or 'vat' in product_name.lower():
            type = 'service'

        vals = {
            'name': product_name,
            'type': type,
            'categ_id': category_id and category_id.id
        }
        if product_sku == 'null':
            vals.update({
                "default_code": product_name
            })
        else:
            vals.update({
                "default_code": product_sku
            })
        logistic_company_ids = self.env["res.company"].search([('is_logistics', '=', True)])
        company_ids = list(set(self.env.company.ids + logistic_company_ids.ids))
        vals.update({'company_ids': [(6, 0, company_ids)]})
        _logger.info("########################Product Vals#######################{}".format(vals))
        return vals

    def import_customer_from_shipstation(self, configuration, customer_id, operation_id):
        self.ensure_one()
        try:
            url = configuration.making_shipstation_url('/customers/{}'.format(customer_id))

            # api_secret = configuration.api_secret
            # api_key = configuration.api_key
            # data = "{0}:{1}".format(api_key, api_secret)
            # encode_data = base64.b64encode(data.encode("utf-8"))
            # authrization_data = "Basic {}".format(encode_data.decode("utf-8"))
            # headers = {"Authorization": authrization_data,
            #            "Content-Type": "application/json"}
            try:
                response_data = configuration.api_calling_function(url)
            except Exception as e:
                response_msg = "Shipstation Import Customer Issue %s" % (e)
                self.create_shipstation_operation_details(operation_id, response_msg, True, 'customer')
                return False
            vals = {}
            _logger.info('Customer Import Response Status Code {}'.format(response_data.status_code))
            if response_data.status_code == 200:
                cust_response = response_data.json()
                customer_id = cust_response.get('customerId')
                customerEmail = cust_response.get('email', '')
                name = cust_response.get('name')
                street = cust_response.get('street1', '')
                street2 = cust_response.get('street2', '')
                city = cust_response.get('city', '')
                state = cust_response.get('state', '')
                zip = cust_response.get('postalCode', '')
                country_code = cust_response.get('countryCode', '')

                country_id = self.env['res.country'].search([('code', '=', country_code)], limit=1)
                state_id = self.env['res.country.state'].search(
                    [('code', '=', state), ('country_id', '=', country_id.id)], limit=1)

                vals.update({'name': name,
                             'street': street and street.title() or "",
                             'street2': street2 and street2.title() or "",
                             'city': city and city.title() or "",
                             'state_id': state_id and state_id.id,
                             'country_id': country_id and country_id.id,
                             'zip': zip,
                             'email': customerEmail and customerEmail.lower() or '',
                             'shipstation_customerId': customer_id,
                             'imported_from_shipstation': True
                             })
                partner_obj = self.env['res.partner'].create(vals)
                _logger.info('Partner Created {}'.format(partner_obj.name))
                response_msg = "Partner Created : {0}".format(partner_obj.name)
                self.create_shipstation_operation_details(operation_id, response_msg, False, 'customer')
                self._cr.commit()
                return partner_obj
        except Exception as e:
            response_msg = "Customer Not Imported %s" % (e)
            _logger.error(response_msg)
            if operation_id:
                self.create_shipstation_operation_details(operation_id, response_msg, True, 'customer')
            return False

    def create_sales_order_from_shipstation(self, vals):
        sale_order = self.env['sale.order']
        pricelist_id = self.env['product.pricelist'].search(
            [('id', '=', self.pricelist_id.id)])
        order_vals = {
            'company_id': vals.get('company_id'),
            'partner_id': vals.get('partner_id'),
            'partner_invoice_id': vals.get('partner_invoice_id'),
            'partner_shipping_id': vals.get('partner_shipping_id'),
            'warehouse_id': vals.get('warehouse_id'),
            'shipstation_warehouse_id': vals.get('shipstation_warehouse_id'),
            'shipstation_delivery_price': vals.get('delivery_price'),
            'postal_code': vals.get('zip'),
        }
        new_record = sale_order.new(order_vals)
        # new_record._onchange_partner_id()
        order_vals = sale_order._convert_to_write({name: new_record[name] for name in new_record._cache})
        new_record = sale_order.new(order_vals)
        # new_record.with_context(with_company=vals.get('company_id')).onchange_partner_shipping_id()
        order_vals = sale_order._convert_to_write({name: new_record[name] for name in new_record._cache})
        order_vals.update({
            'company_id': vals.get('company_id'),
            'picking_policy': 'direct',
            'partner_invoice_id': vals.get('partner_invoice_id'),
            'partner_shipping_id': vals.get('partner_shipping_id'),
            'partner_id': vals.get('partner_id'),
            'date_order': vals.get('date_order', ''),
            'state': 'draft',
            'carrier_id': vals.get('carrier_id', ''),
        })
        return order_vals

    def create_sale_order_line_from_shipstation(self, vals):
        sale_order_line = self.env['sale.order.line']
        order_line = {
            'order_id': vals.get('order_id'),
            'product_id': vals.get('product_id', ''),
            'company_id': vals.get('company_id', ''),
            'name': vals.get('description'),
            'product_uom': vals.get('product_uom')
        }
        new_order_line = sale_order_line.new(order_line)
        # new_order_line.product_id_change()
        order_line = sale_order_line._convert_to_write(
            {name: new_order_line[name] for name in new_order_line._cache})
        order_line.update({
            'order_id': vals.get('order_id'),
            'product_uom_qty': vals.get('order_qty', 0.0),
            'price_unit': vals.get('price_unit', 0.0),
            'discount': vals.get('discount', 0.0),
            'state': 'draft',
        })
        return order_line

    def create_shipstation_operation_details(self, operation_id, shipstation_response_message, fault_operaion,
                                             shipstation_operation="sale_order"):
        shipstation_operation_details = self.env['shipstation.operation.details']
        shipstation_operation_details.create({
            'operation_id': operation_id and operation_id.id,
            'shipstation_response_message': shipstation_response_message,
            'fault_operaion': fault_operaion,
            'shipstation_operation': shipstation_operation
        })

    def shipstation_order_api_calling_function(self, configuration=False, url=False, operation_id=False):
        response_data = False
        data = "{0}:{1}".format(configuration.api_key, configuration.api_secret)
        encode_data = base64.b64encode(data.encode("utf-8"))
        authrization_data = "Basic {}".format(encode_data.decode("utf-8"))
        headers = {"Authorization": authrization_data, "Content-Type": "application/json"}
        _logger.info('Import Order Request Data {}'.format(url))
        try:
            response_data = request(method='GET', url=url, headers=headers)
            _logger.info('Import Order Response >>>>>> {}'.format(response_data))
        except Exception as e:
            response_msg = "Shipstation Import Order Issue %s" % (e)
            _logger.error(response_msg)
            if operation_id:
                self.create_shipstation_operation_details(operation_id, response_msg, True, 'sale_order')
        return response_data

    def shipstation_order_managing_function(self, configuration=False, orders=[], operation_id=False,
                                            product_operation_id=False, product_datas=False, csvwriter=False,
                                            customer_csvwriter=False, customer_operation_id=False):
        shipstation_product_data_obj = self.env['shipstation.product.data']
        api_data = False
        if self._context.get('api_data'):
            api_data = self._context.get('api_data')
        for order in orders:
            shipstation_order_id = order.get('orderId')
            shipstation_order_number = order.get('orderNumber')
            sale_order = self.env['sale.order'].search(
                [('shipstation_order_id', '=', shipstation_order_id), ('state', '!=', 'cancel'),
                 ('shipstation_store_id', '=', self.id)], limit=1, order='date_order desc')
            warehouse_id = False
            date_time_str = order.get('orderDate')
            _logger.info('Date Time Str {0} Type : {1}'.format(date_time_str, type(date_time_str)))
            date = date_time_str[0:10]
            time = date_time_str[11:19]
            date_time = "{0} {1}".format(date, time)
            date_time_obj = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
            order_date = fields.Datetime.to_string(date_time_obj)
            if sale_order:
                # self.update_tracking_carrier(sale_order, configuration, operation_id)
                _logger.info('Order is already exist {0} Order : {1}'.format(sale_order.shipstation_order_number, sale_order))
                continue
                # sale_order = sale_order.filtered(lambda so: so.date_order.strftime("%Y-%m-%d") == date)

            customerEmail = order.get('customerEmail')
            customerId = order.get('customerId')

            cust_response = order.get("shipTo")
            customer_name = cust_response.get('name')
            street = cust_response.get('street1', '')
            street2 = cust_response.get('street2', '')
            city = cust_response.get('city', '')
            state = cust_response.get('state', '')
            zip = cust_response.get('postalCode')
            country_code = cust_response.get('country')
            country_id = self.env['res.country'].search([('code', '=', country_code)], limit=1)
            state_id = self.env['res.country.state'].search(
                [('code', '=', state), ('country_id', '=', country_id.id)], limit=1)
            if customer_csvwriter:
                customer_csvwriter.writer.writerow(
                    [customer_name, self.id, street, city, zip, state, country_code, customerEmail])

            if customerId == None or self.create_customer_from_data:
                partner_obj = self.env['res.partner'].search(
                    [('imported_from_shipstation', '=', True), ('street', '=', street),
                     ('name', '=', customer_name), ('zip', '=', zip), ('city', '=', city),
                     ('email', '=', customerEmail)], limit=1)
                if not partner_obj:
                    customer_vals = {'name': customer_name and customer_name.title() or "",
                                     'street': street and street.title() or "",
                                     'street2': street2 and street2.title() or "",
                                     'city': city and city.title() or "",
                                     'state_id': state_id and state_id.id,
                                     'country_id': country_id and country_id.id,
                                     'zip': zip,
                                     'email': customerEmail.lower() if not customerEmail == None else "",
                                     'shipstation_customerId': "",
                                     'imported_from_shipstation': True}
                    partner_obj = self.env['res.partner'].create(customer_vals)
                    _logger.info('Partner Created {}'.format(partner_obj.name))
                    response_msg = "Partner Created : {0}".format(partner_obj.name)
                    self.create_shipstation_operation_details(customer_operation_id, response_msg, False,
                                                              'customer')
            else:
                partner_obj = self.env['res.partner'].search([('shipstation_customerId', '=', customerId)],
                                                             limit=1)
            if not partner_obj:
                partner_obj = self.import_customer_from_shipstation(configuration, customerId,
                                                                    customer_operation_id)
                if not partner_obj:
                    message = "Customer Is Not Found In Order Response! Shipstation Order ID : {0}, Shipstation Order Number : {1}".format(
                        shipstation_order_id, shipstation_order_number)
                    _logger.info(message)

                    self.create_shipstation_operation_details(customer_operation_id, order, True, 'sale_order')
                    continue

            shipping_partner_state = order.get('shipTo').get('state')
            shipping_partner_country = order.get('shipTo').get('country')
            country_id = self.env['res.country'].search([('code', '=', shipping_partner_country)], limit=1)
            state_id = self.env['res.country.state'].search(
                [('code', '=', shipping_partner_state), ('country_id', '=', country_id.id)], limit=1)
            vals = {
                'name': order.get('shipTo').get('name', '') and order.get('shipTo').get('name', '').title() or "",
                'street': order.get('shipTo').get('street1', '') and order.get('shipTo').get('street1', '').title(),
                'street2': order.get('shipTo').get('street2', '') and order.get('shipTo').get('street2',
                                                                                              '').title(),
                'city': order.get('shipTo').get('city', '') and order.get('shipTo').get('city', '').title(),
                'state_id': state_id and state_id.id or False,
                'country_id': country_id and country_id.id or False,
                'phone': order.get('shipTo').get('phone'),
                'zip': order.get('shipTo').get('postalCode'),
                'type': 'delivery',
                'parent_id': partner_obj.id}

            carrierCode, serviceCode, packageCode = order.get('carrierCode'), order.get('serviceCode'), order.get(
                'packageCode')
            # serviceCode = order.get('serviceCode')
            # packageCode = order.get('packageCode')
            # carrier_id = order.shipstation_store_id.carrier_id
            carrier_id = self.env['delivery.carrier'].search(
                [('shipstation_carrier_id.code', '=', carrierCode),
                 ('shipstation_configuration_id', '=',
                  self.shipstation_configuration_id and self.shipstation_configuration_id.id),
                 ('shipstation_delivery_carrier_service_id.service_code', '=', serviceCode)], limit=1)
            # if not carrier_id:
            # carrier_id = self.env['delivery.carrier'].search(
            #  [('shipstation_carrier_id.code', '=', carrierCode),
            #   ('shipstation_configuration_id', '=',
            #    self.shipstation_configuration_id and self.shipstation_configuration_id.id),
            #   ('shipstation_delivery_carrier_service_id.service_code', '=', serviceCode)], limit=1)
            if not carrier_id and not carrierCode == None and not serviceCode == None:
                shipstation_carrier_id = self.env['shipstation.delivery.carrier'].search(
                    [('code', '=', carrierCode),
                     ('shipstation_configuration_id', '=',
                      self.shipstation_configuration_id and self.shipstation_configuration_id.id)])
                shipstation_service_id = self.env['shipstation.delivery.carrier.service'].search(
                    [('service_code', '=', serviceCode), ('shipstation_configuration_id', '=',
                                                          self.shipstation_configuration_id and self.shipstation_configuration_id.id)])
                if shipstation_carrier_id and shipstation_service_id:
                    delivery_package_id = self.env['shipstation.delivery.package'].search(
                        [('package_code', '=', packageCode)], limit=1)
                    carrier_id = self.env['delivery.carrier'].create({"name": serviceCode,
                                                                      "delivery_type": "shipstation",
                                                                      "store_id": self.id,
                                                                      "integration_level": "rate",
                                                                      "shipstation_carrier_id": shipstation_carrier_id.id,
                                                                      'shipstation_configuration_id': self.shipstation_configuration_id and self.shipstation_configuration_id.id,
                                                                      'delivery_package_id': delivery_package_id.id,
                                                                      "shipstation_delivery_carrier_service_id": shipstation_service_id.id,
                                                                      "product_id": self.env.ref(
                                                                      'shipstation_shipping_odoo_integration.shipstation_service_product').id
                                                                      })

            shipstation_warehouse_id = order.get('advancedOptions') and order.get('advancedOptions').get(
                'warehouseId')
            _logger.info(" Advance Option >>>>>>>>>>>>>>>>>>>>>{}".format(order.get('advancedOptions')))
            shipstation_warehouse_obj = self.env['shipstation.warehouse.detail'].sudo().search(
                [('warehouse_id', '=', shipstation_warehouse_id)], limit=1)
            _logger.info(
                "Shipstation Warehouse : {0} Shipstation Warehouse obj:{1}".format(shipstation_warehouse_id,
                                                                                   shipstation_warehouse_obj))
            warehouse_id = False
            if shipstation_warehouse_obj:
                warehouse_id = self.env['stock.warehouse'].sudo().search(
                    [('shipstation_warehouse_id', '=', shipstation_warehouse_obj.id)], limit=1)
            s_warehouse_id = warehouse_id if warehouse_id else self.warehouse_id
            warehouse_id = self.warehouse_id
            if not warehouse_id:
                response_msg = "Warehouse  is not availabel :{0} ".format(shipstation_warehouse_id)
                _logger.info(response_msg)
                self.create_shipstation_operation_details(operation_id, response_msg, True, 'sale_order')
                continue

            delivery_price = order.get('shippingAmount', 0.0)
            if not delivery_price:
                configuration_t = self.shipstation_configuration_id or configuration
                if configuration_t:
                    url = configuration_t.making_shipstation_url("/shipments?orderId={}".format(shipstation_order_id))
                    response_data = configuration_t.api_calling_function(url)
                    if response_data.status_code == 200:
                        responses = response_data.json()
                        if responses.get('shipments'):
                            for shipment in responses.get('shipments'):
                                delivery_price += shipment.get('shipmentCost')
            vals.update({'partner_id': partner_obj.id,
                         'partner_invoice_id': partner_obj and partner_obj.id,
                         'partner_shipping_id': partner_obj and partner_obj.id,
                         'date_order': order_date,
                         'carrier_id': carrier_id and carrier_id.id,
                         'company_id': warehouse_id.company_id.id or self.env.company.id or self.env.user.company_id.id,
                         'warehouse_id': warehouse_id.id,
                         'shipstation_warehouse_id': s_warehouse_id.id,
                         'carrierCode': carrierCode,
                         'serviceCode': serviceCode,
                         'delivery_price': delivery_price
                         })
            is_create_order = True
            customField1 = order.get('advancedOptions').get('customField1') if order.get('advancedOptions').get(
                'customField1') else ""
            customField2 = order.get('advancedOptions').get('customField2') if order.get('advancedOptions').get(
                'customField2') else ""
            customField3 = order.get('advancedOptions').get('customField3') if order.get('advancedOptions').get(
                'customField3') else ""
            customField_deatils = "{0} : {1} : {2}".format(customField1, customField2, customField3)

            product_error_message = []
            for order_line in order.get('items'):
                option_name = ""
                product_name = order_line.get('name')
                product_sku = order_line.get("sku")
                product_qty = order_line.get("quantity")
                product_item_id = order_line.get("orderItemId")
                _logger.info("Order Items : {}".format(order_line))
                for option in order_line.get('options'):
                    option_name += option.get('name') + " " + option.get('value')
                if not product_sku:
                    product_id = self.env['product.product'].search([('default_code', '=', product_name.lower())],
                                                                    limit=1)
                    _logger.info(" IF CONDITION : {}".format(product_id))
                else:
                    product_id = self.env['product.product'].search([('default_code', '=', product_sku)], limit=1)
                    _logger.info("ELSE CONDITION : {}".format(product_id))
                if not product_id and product_sku:
                    _logger.info(" ************ Identical SKU *************** : {}".format(product_sku))
                    product_ids = self.env['product.product'].search([('identical_sku', '!=', False)])
                    product_id = product_ids.filtered(lambda p: product_sku in p.identical_sku)
                    if product_id:
                        product_id = product_id[0]
                    _logger.info("ELSE 2 CONDITION : {}".format(product_id))
                if not product_id and order_line.get('name'):
                    product_id = self.env['product.product'].search(
                        [('detailed_type', '=', 'service'), ('name', '=', order_line.get('name'))], limit=1, order='id desc')
                    _logger.info(" IF CONDITION Service : {}".format(product_id))
                if not product_id:
                    product_ids = self.env['product.product'].search([('identical_sku', '!=', False)])
                    product_id = product_ids.filtered(lambda p: product_sku in p.identical_sku)
                    if product_id:
                        product_id = product_id[0]
                    _logger.info("ELSE 2 CONDITION : {}".format(product_id))

                if not product_id:
                    # vals
                    product_vals = self.create_product_from_shipstation(product_name, product_sku)
                    _logger.info("*********1 Product Vals {}".format(product_vals))
                    # product_template_id = self.env['product.template'].create(vals)
                    product_template_id = self.env['product.template'].create(product_vals)
                    _logger.info("*********1 Product Created {}".format(product_template_id.sudo().company_ids))
                    product_id = self.env['product.product'].search(
                        [('product_tmpl_id', '=', product_template_id.id)])
                    response_msg = "{0} Product Created".format(product_id.name)
                    self.create_shipstation_operation_details(product_operation_id, response_msg, True,
                                                              'product')
                if not product_id:
                    response_msg = "Sale Order : {2} Prouduct Not Found  Product SKU : {0} and  Name : {1}".format(
                        product_sku, product_name, shipstation_order_number)
                    self.create_shipstation_operation_details(product_operation_id, response_msg, True,
                                                              'product')
                    is_create_order = False
                    product_error_message.append(order_line)
                    if not shipstation_product_data_obj.sudo().search(
                            [('store_id', '=', self.id), ('product_sku', '=', product_sku)]):
                        csvwriter.writer.writerow([product_item_id, product_sku, product_qty, product_name])
                        vals = {'store_id': self.id, 'product_sku': product_sku}
                        logistic_company_ids = self.env["res.company"].search([('is_logistics', '=', True)])
                        company_ids = list(set(self.env.company.ids + logistic_company_ids.ids))
                        vals.update({'company_ids': [(6, 0, company_ids)]})
                        shipstation_product_data_obj.create(vals)
                    product_datas = True
                    continue

            if is_create_order:
                order_vals = self.sudo().create_sales_order_from_shipstation(vals)
                shipstation_ship_date = order.get('shipDate')
                shipstation_ship_date = shipstation_ship_date and datetime.strptime("%s 00:00:00"% shipstation_ship_date, '%Y-%m-%d %H:%M:%S') or False
                # shipstation_warehouse_address_id = self.shipstation_configuration_id.shipstation_warehouse_address_id

                order_vals.update({'shipstation_order_id': shipstation_order_id,
                                   'name': shipstation_order_number,
                                   'shipstation_order_number': shipstation_order_number,
                                   'shipstation_store_id': self.id,
                                   'shipstation_store': self.id,
                                   'serviceCode': serviceCode,
                                   'carrierCode': carrierCode,
                                   'gift_note': order.get('giftMessage', ''),
                                   'customer_note': order.get('customerNotes', ''),
                                   'shipstation_configuration_id': self.shipstation_configuration_id and self.shipstation_configuration_id.id,
                                   # 'order_custom_data': customField_deatils,
                                   'orderStatus': order.get('orderStatus'),
                                   'shipstation_ship_date': fields.Datetime.to_string(shipstation_ship_date)
                                   })
                if self.shipstation_order_status == 'shipped' and order.get(
                        'requestedShippingService') and not order.get('shipDate'):
                    order_vals.update({'do_not_confirm': True})
                order_id = self.env['sale.order'].sudo().create(order_vals)

                # # Add Shipping Cost In Order
                # if order_id:
                #     order_id.add_shipping_cost_line()

                # processed_orders += order_id and 1 or 0
                if api_data and order_id:
                    api_data.processed_orders = api_data.processed_orders + 1

                response_msg = "Sale Order Created {0}".format(order_id.name)
                _logger.info("Sale Order Created {0}".format(order_id.name))
                self.sudo().create_shipstation_operation_details(operation_id, response_msg, False,
                                                                 'sale_order')
                if carrier_id and carrier_id.delivery_type == 'shipstation':
                    # rate_record = carrier_id.shipstation_rate_shipment(order=order_id)
                    # base_shipping_cost = order.get('shippingAmount', 0.0)  # rate_record.get('price')
                    order_id.set_delivery_line(carrier_id, delivery_price)
                for order_line in order.get('items'):
                    _logger.info("ORDER ITEMS : {}".format(order_line))
                    option_name = ""
                    product_name = order_line.get('name')

                    product_sku = order_line.get("sku")
                    if not product_sku:
                        product_id = self.env['product.product'].search(
                            [('default_code', '=', product_name.lower())], limit=1)
                        _logger.info(" IF CONDITION : {}".format(product_id))
                    else:
                        product_id = self.env['product.product'].sudo().search(
                            [('default_code', '=', product_sku)], limit=1)
                        _logger.info("ELSE CONDITION : {}".format(product_id))
                    if not product_id and product_sku:
                        _logger.info(" ************ Identical SKU *************** : {}".format(product_sku))
                        product_ids = self.env['product.product'].search([('identical_sku', '!=', False)])
                        product_id = product_ids.filtered(lambda p: product_sku in p.identical_sku)
                        if product_id:
                            product_id = product_id[0]
                        _logger.info("ELSE 2 CONDITION : {}".format(product_id))
                    if not product_id and order_line.get('name'):
                        product_id = self.env['product.product'].search(
                            [('detailed_type', '=', 'service'), ('name', '=', order_line.get('name'))], limit=1, order='id desc')
                        _logger.info(" IF CONDITION Service : {}".format(product_id))
                    if not product_id:
                        product_ids = self.env['product.product'].search([('identical_sku', '!=', False)])
                        product_id = product_ids.filtered(lambda p: product_sku in p.identical_sku)
                        if product_id:
                            product_id = product_id[0]
                        _logger.info("ELSE 2-2 CONDITION : {}".format(product_id))
                    if not product_id:
                        vals = self.create_product_from_shipstation(product_name, product_sku)
                        _logger.info("*********2 Product Vals {}".format(vals))
                        # product_template_id = self.env['product.template'].create(vals)
                        product_template_id = self.env['product.template'].create(vals)
                        _logger.info("*********2 Product Created {}".format(product_template_id.sudo().company_ids))
                        product_id = self.env['product.product'].search(
                            [('product_tmpl_id', '=', product_template_id.id)])
                        response_msg = "{0} Product Created".format(product_id.name)
                        self.create_shipstation_operation_details(product_operation_id, response_msg, True,
                                                                  'product')

                    if not product_id:
                        continue

                    quantity = order_line.get('quantity')
                    price = order_line.get('unitPrice')

                    for option in order_line.get('options'):
                        option_name += option.get('name') + ":" + option.get('value') + "\n"
                    if price < 0:
                        product_id = self.env.ref('shipstation_shipping_odoo_integration.shipstation_discount')
                    vals = {'product_id': product_id.id, 'price_unit': price, 'order_qty': quantity,
                            'order_id': order_id.id, 'description': product_name + "\n" + option_name,
                            'product_uom': product_id.uom_id and product_id.uom_id.id,
                            'company_id': self.env.company.id or self.env.user.company_id.id}

                    order_line = self.sudo().create_sale_order_line_from_shipstation(vals)
                    if option_name:
                        order_line.update({'name': option_name})
                    self.env['sale.order.line'].sudo().create(order_line)
                if order_id.shipstation_store_id.add_vat_line:
                    vat_price = order.get('taxAmount', 0.0)
                    if vat_price > 0:
                        vat_product_id = self.env.ref('shipstation_shipping_odoo_integration.shipstation_vat')
                        taxline_vals = {'product_id': vat_product_id.id, 'price_unit': vat_price,
                                        'product_uom_qty': 1,
                                        'order_id': order_id.id, 'name': vat_product_id.name,
                                        'company_id': order_id.company_id.id
                                        }
                        self.env['sale.order.line'].sudo().create(taxline_vals)

                # try:
                #     order_id.action_confirm()
                #     self.update_tracking_carrier(order_id, configuration, operation_id)
                #     print(order_id)
                # except Exception as e:
                #     continue
                self._cr.commit()
            else:
                message = "Shipstation Order ID : {0}, Shipstation Order Number : {1}, Order Is Not Created In Odoo Beacuse of Some Order Products Are Not Available In Odoo. Product Information : {2}".format(
                    shipstation_order_id, shipstation_order_number, product_error_message)
                self.create_shipstation_operation_details(operation_id, message, True, 'sale_order')
                self._cr.commit()
            # else:
            #     message = "Order Is Already Exist {}".format(sale_order and sale_order.name)
            #     self.create_shipstation_operation_details(operation_id, message, True, 'sale_order')
            #     self._cr.commit()

        return product_datas

    def create_csv_file(self, files_path, file_path, headers):
        buffer = StringIO()
        csvwriter = DictWriter(buffer, headers, delimiter=",")
        csvwriter.writer.writerow(headers)
        buffer.seek(0)
        file_data = buffer.read().encode()
        datas = base64.b64encode(file_data)
        csv_file = StringIO(base64.decodebytes(datas).decode())
        directory = os.path.dirname(files_path)
        try:
            os.stat(directory)
        except:
            os.system("mkdir %s" % (files_path))

        file_write = open(file_path, 'w+')
        file_write.writelines(csv_file.getvalue())
        file_write.close()
        os.system("rm -R %s" % (directory))
        return datas

    def _initialize_import_process(self, from_cron=False):
        self.write({'process_msg': 'Shipstation Process Started.....'})
        shipstation_operation_detail = self.env['shipstation.operation.detail']
        last_modification_date = self.last_modification_date - relativedelta(hours=10)
        shipstation_to_date = datetime.now() + relativedelta(hours=2)
        operation_id = shipstation_operation_detail.create({
            'shipstation_operation': 'sale_order', 'shipstation_operation_type': 'import',
            'message': 'Sale Order Import Process Running...', 'shipstation_store_id': self.id,
            'import_order_from_date': from_cron and last_modification_date or self.last_modification_date,
            'import_order_to_date': from_cron and shipstation_to_date or self.shipstation_to_date})
        self._cr.commit()

        product_operation_id = shipstation_operation_detail.create({
            'shipstation_operation': 'product', 'shipstation_operation_type': 'import',
            'message': 'Product Import Process Running...', 'shipstation_store_id': self.id,
            'import_order_from_date': self.last_modification_date,
            'import_order_to_date': self.shipstation_to_date})
        customer_operation_id = shipstation_operation_detail.create({
            'shipstation_operation': 'customer', 'shipstation_operation_type': 'import',
            'message': 'Customer Import Process Running...', 'shipstation_store_id': self.id,
            'import_order_from_date': self.last_modification_date,
            'import_order_to_date': self.shipstation_to_date})

        return operation_id, product_operation_id, customer_operation_id

    def import_order_from_shipstation_using_cron(self):
        self.ensure_one()
        operation_id, product_operation_id, customer_operation_id = self._initialize_import_process(from_cron=True)
        shipstation_to_date = datetime.now() + relativedelta(days=1)

        try:
            configuration = self.shipstation_configuration_id
            if not configuration:
                self.create_shipstation_operation_details(operation_id,
                                                          "Shipstation Configuration Missing",
                                                          True,
                                                          'sale_order')
                return
            to_date = shipstation_to_date.strftime("%Y-%m-%d")
            to_time = shipstation_to_date.strftime("%H:%M:%S")
            shipstation_to_date = "{}T{}.0000000".format(to_date, to_time)
            shipstation_to_date_temp = self.last_modification_date or datetime.now()
            last_modification_date = shipstation_to_date_temp - relativedelta(days=2)
            last_modify_date = last_modification_date.strftime("%Y-%m-%d")
            last_modify_time = last_modification_date.strftime("%H:%M:%S")
            last_modification_date = "{}T{}.0000000".format(last_modify_date, last_modify_time)
            _logger.info("Last Modification Date >>>>>> {0} Today Date : {1}".format(last_modification_date,
                                                                                     shipstation_to_date))

            url = configuration.making_shipstation_url(
                '/orders?orderDateStart={0}&orderDateEnd={1}&storeId={2}&orderStatus={3}&pageSize=100&sortBy={4}'.format(
                    last_modification_date, shipstation_to_date, self.store_id, self.shipstation_order_status,
                    'OrderDate'))

            response_data = self.shipstation_order_api_calling_function(configuration, url, operation_id)
            _logger.info(
                ">>>>> Response Data Status {0} >> {1}".format(response_data.status_code, response_data.json()))
            buffer = StringIO()
            #            operation_id.total_orders = response_data.get('total')
            csvwriter = DictWriter(buffer, [], delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csvwriter.writer.writerow(['orderItemId', 'SKU', 'Quantity', 'Name'])
            create_csv_file = False

            # customer Information csv File

            customer_buffer = StringIO()
            customer_csvwriter = DictWriter(customer_buffer, [], delimiter=",", quotechar='"',
                                            quoting=csv.QUOTE_MINIMAL)
            customer_csvwriter.writer.writerow(
                ['CustomerName', 'Store', 'Street', 'City', 'Zip', 'State', 'Country', 'email'])

            if response_data.status_code == 200:
                responses = response_data.json()
                total_pages = responses.get("pages")
                operation_id.total_orders = responses.get('total')
                # self.total_orders = responses.get('total')
                if total_pages >= 1 and responses.get('total', 0) != 0:
                    for total_page in range(1, total_pages + 1, 1):
                        if total_page <= 0:
                            continue
                        page_url = "{0}&orderStatus={1}&pageSize=100&page={2}&sortBy={3}".format(url,
                                                                                                 self.shipstation_order_status,
                                                                                                 total_page,
                                                                                                 'OrderDate')
                        response_data = self.shipstation_order_api_calling_function(configuration, page_url,
                                                                                    operation_id)
                        if response_data.status_code == 200:
                            responses = response_data.json()
                            orders = responses.get('orders')
                            if not orders:
                                response_msg = "In Shipstation Import Order process, Not found Orders!  {0}".format(
                                    responses)
                                self.create_shipstation_operation_details(operation_id, response_msg, True,
                                                                          'sale_order')
                                # total_pages = total_pages - 1
                                continue
                            if isinstance(orders, dict):
                                orders = [orders]
                            product_datas = self.shipstation_order_managing_function_create(
                                str(total_page) + ' ' + shipstation_to_date,
                                configuration, orders,
                                operation_id,
                                product_operation_id,
                                customer_operation_id)
                            if product_datas:
                                create_csv_file = True
                        else:
                            error_code = "%s" % (response_data.status_code)
                            error_message = response_data.reason
                            error_detail = {'error': error_code + " - " + error_message + " - "}
                            if response_data.json():
                                error_detail = {
                                    'error': error_code + " - " + error_message + " - %s" % (response_data.json())}
                            response_msg = "1 >>>>>>> Getting an Issue in the  Imported  Process %s" % (
                                error_detail)
                            self.create_shipstation_operation_details(operation_id, response_msg, True,
                                                                      'sale_order')
                            self.process_msg = ' Process InCompleted Please Check Log'
                            _logger.info(response_msg)
                        self._cr.commit()
                    # if create_csv_file:
                    #     files_path = "/tmp/product_Details_{}/".format(fields.Date.today())
                    #     file_path = ("{}productDetails.csv".format(files_path))
                    #
                    #     csv_data = self.create_csv_file(files_path, file_path, [])
                    #
                    #     self.env['ir.attachment'].create({
                    #         'datas': csv_data,
                    #         'name': 'product_Details_{}.csv'.format(fields.Date.today()),
                    #         'res_model': 'shipstation.operation.detail',
                    #         'res_id': product_operation_id.id
                    #     })
                    #
                    # # For Customer import file in job
                    # customer_files_path = "/tmp/Customer_Details_{}/".format(fields.Date.today())
                    # customer_file_path = ("{}Customer_Details.csv".format(customer_files_path))
                    #
                    # customer_csv_data = self.create_csv_file(customer_files_path, customer_file_path, [])
                    #
                    # self.env['ir.attachment'].create({
                    #     'datas': customer_csv_data,
                    #     'name': 'Customer_Details_{}.csv'.format(fields.Date.today()),
                    #     'res_model': 'shipstation.operation.detail',
                    #     'res_id': operation_id.id
                    # })

                else:
                    response_msg = "In Shipstation Import Order process, Not found Orders!  {0}".format(responses)
                    self.create_shipstation_operation_details(operation_id, response_msg, True, 'sale_order')
            else:
                error_code = "%s" % (response_data.status_code)
                error_message = response_data.reason
                error_detail = {'error': error_code + " - " + error_message + " - "}
                if response_data.json():
                    error_detail = {'error': error_code + " - " + error_message + " - %s" % (response_data.json())}
                response_msg = "2 >>>>>>>> Getting an Issue in the  Imported  Process %s" % (error_detail)
                self.create_shipstation_operation_details(operation_id, response_msg, True, 'sale_order')
                self.process_msg = 'Process InCompleted Please Check Log'
                _logger.info(response_msg)
                self._cr.commit()
        except Exception as e:
            response_msg = "3 >>>>>>>>>> Getting an Issue in the  Imported  Process %s" % (e)
            self.process_msg = ' Process InCompleted Please Check Log'
            _logger.info(response_msg)
            self.create_shipstation_operation_details(operation_id, response_msg, True, 'sale_order')
            self._cr.commit()
        from_order_date = datetime.now() - relativedelta(days=2)
        self.last_modification_date = from_order_date
        to_order_date = datetime.now() + relativedelta(days=1)
        _logger.info("Current Date >>>> {}".format(to_order_date))
        to_order_date = to_order_date.strftime("%Y-%m-%d")  # %H:%M:%S
        self.shipstation_to_date = "{} 23:59:59".format(to_order_date)
        operation_id.message = 'Order Import Process Completed.'
        customer_operation_id.message = 'Customer Import Process Completed.'
        product_operation_id.message = 'Product Import Process Completed.'
        # self.write({})

        # Unlink all product data, was store data in this model because of remove file data duplication.
        # shipstation_product_data_obj = self.env['shipstation.product.data']
        # shipstation_product_data_ids = shipstation_product_data_obj.search([('store_id', '=', self.id)])
        # shipstation_product_data_ids.unlink()
        #
        # shipstation_operation_data_obj = self.env['shipstation.operation.detail']
        # shipstation_operation_data_ids = shipstation_operation_data_obj.search([])
        # shipstation_process_ids = shipstation_operation_data_ids.filtered(lambda op: len(op.operation_ids) <= 0)
        # shipstation_process_ids.unlink()

        self._cr.commit()

    def shipstation_order_managing_function_create(self, shipstation_to_date, configuration, orders, operation_id,
                                                   product_operation_id,
                                                   customer_operation_id):
        shipstation_api_data_obj = self.env['shipstation.api.data']
        if not any([shipstation_to_date, orders, configuration, operation_id]):
            return []
        sale = self.env['sale.order']
        shipstation_orders = []
        [shipstation_orders.append(order.get('orderId')) for order in orders]
        shipstation_order_ids = sale.search([('shipstation_order_id', 'in', shipstation_orders)])
        if len(shipstation_orders) == len(shipstation_order_ids):
            _logger.info("Order are already exists from this response: {}".format(shipstation_order_ids))
            return True
        vals = {
            'name': shipstation_to_date,
            'data': orders,
            'shipstation_configuration_id': configuration.id,
            'operation_id': operation_id.id,
            'product_operation_id': product_operation_id.id,
            'customer_operation_id': customer_operation_id.id,
            'store_id': self.id,
            'stage_id': 'draft',
            'total_orders': len(orders),
        }
        shipstation_api_data_obj.create(vals)
        return True

    def update_tracking_carrier(self, sale_order, configuration, operation_id):
        if not sale_order.carrier_tracking_ref and sale_order.shipstation_order_id:
            url = configuration.making_shipstation_url(
                '/shipments?orderId={0}'.format(sale_order.shipstation_order_id))
            response_data = self.shipstation_order_api_calling_function(configuration, url, operation_id)
            if response_data and response_data.status_code in [200, 204] and hasattr(sale_order, "freight_id"):
                shipment_data = response_data.json()
                cost = 0
                carrier_code = ''
                for shipment in shipment_data.get('shipments'):
                    if shipment.get('trackingNumber'):
                        self._cr.execute("""update sale_order set carrier_tracking_ref = '{}' where id={} """.format(
                            shipment.get('trackingNumber'), sale_order.id))
                        if sale_order.freight_id:
                            sale_order.freight_id.bol_number = shipment.get('trackingNumber')
                            cost += shipment.get('shipmentCost', 0) or 0
                            carrier_code = shipment.get('carrierCode', '')
                # ToDo: Commented code to stop the feature that adding the Billing rules for shipping rate on OBL record
                if carrier_code and sale_order and sale_order.company_id.company_code != "CAR":
                    product_id = self.env['product.product'].search(
                        [('name', 'ilike', carrier_code), ('detailed_type', '=', 'service')], limit=1)
                    if not product_id:
                        _logger.info("Product is not available as carrier code {}, sale order {}".format(carrier_code, sale_order))
                        out_id = sale_order.picking_ids.filtered(
                            lambda p: p.picking_type_code == 'outgoing' and p.company_id.id == sale_order.company_id.id)
                        product_id = out_id.sudo().carrier_id.product_id
                        _logger.info("Product from the transfer {}, sale order {}".format(product_id, sale_order))
                    rate_margin = sale_order.company_id.rate_margin
                    rate_margin = rate_margin and rate_margin / 100 or 0
                    if product_id:
                        vals = {
                            'product_id': product_id.id,
                            'total_unit': 1,
                            'product_uom': product_id.uom_id.id,
                            'unit_price': round(cost + (cost * rate_margin), 2),
                            'transit_app_id': sale_order.freight_id.id,
                        }
                        self.env['pallet.vas.cost'].create(vals)

    def import_order_from_shipstation(self):
        with api.Environment.manage():
            new_cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=new_cr))
            self.ensure_one()
            self.write({'process_msg': 'Shipstation Process Started.....'})
            shipstation_operation_detail = self.env['shipstation.operation.detail']
            # shipstation_operation_details = self.env['shipstation.operation.details']
            operation_id, product_operation_id, customer_operation_id = self._initialize_import_process(from_cron=False)

            # operation_id = shipstation_operation_detail.create({
            #     'shipstation_operation': 'sale_order', 'shipstation_operation_type': 'import',
            #     'message': 'Sale Order Import Process Running...', 'shipstation_store_id': self.id,
            #     'import_order_from_date': self.last_modification_date,
            #     'import_order_to_date': self.shipstation_to_date})
            # self._cr.commit()
            #
            # product_operation_id = shipstation_operation_detail.create({
            #     'shipstation_operation': 'product', 'shipstation_operation_type': 'import',
            #     'message': 'Product Import Process Running...', 'shipstation_store_id': self.id,
            #     'import_order_from_date': self.last_modification_date,
            #     'import_order_to_date': self.shipstation_to_date})
            #
            # customer_operation_id = shipstation_operation_detail.create({
            #     'shipstation_operation': 'customer', 'shipstation_operation_type': 'import',
            #     'message': 'Customer Import Process Running...', 'shipstation_store_id': self.id,
            #     'import_order_from_date': self.last_modification_date,
            #     'import_order_to_date': self.shipstation_to_date})

            try:
                configuration = self.shipstation_configuration_id
                if not configuration:
                    self.create_shipstation_operation_details(operation_id, "Shipstation Configuration Missing",
                                                              True, 'sale_order')
                    return
                today_date = datetime.now()
                if self.shipstation_to_date:
                    to_date = self.shipstation_to_date.strftime("%Y-%m-%d")
                    to_time = self.shipstation_to_date.strftime("%H:%M:%S")
                    shipstation_to_date = "{}T{}.0000000".format(to_date, to_time)
                else:
                    shipstation_to_date = datetime.now()
                date = self.last_modification_date.strftime("%Y-%m-%d")
                time = self.last_modification_date.strftime("%H:%M:%S")
                last_modification_date = "{}T{}.0000000".format(date, time)
                _logger.info("Last Modification Date >>>>>> {0} Today Date : {1}".format(last_modification_date,
                                                                                         shipstation_to_date))

                url = configuration.making_shipstation_url(
                    '/orders?orderDateStart={0}&orderDateEnd={1}&storeId={2}&orderStatus={3}&pageSize=100'.format(
                        last_modification_date, shipstation_to_date, self.store_id, self.shipstation_order_status))

                response_data = self.shipstation_order_api_calling_function(configuration, url, operation_id)
                _logger.info(
                    ">>>>> Response Data Status {0} >> {1}".format(response_data.status_code, response_data.json()))
                # product_datas = []
                # headers = []
                buffer = StringIO()
                #  operation_id.total_orders = response_data.get('total')
                csvwriter = DictWriter(buffer, [], delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csvwriter.writer.writerow(['orderItemId', 'SKU', 'Quantity', 'Name'])
                create_csv_file = False

                # customer Information csv File

                # customer_headers = []
                customer_buffer = StringIO()
                customer_csvwriter = DictWriter(customer_buffer, [], delimiter=",", quotechar='"',
                                                quoting=csv.QUOTE_MINIMAL)
                customer_csvwriter.writer.writerow(
                    ['CustomerName', 'Store', 'Street', 'City', 'Zip', 'State', 'Country', 'email'])

                if response_data.status_code == 200:
                    responses = response_data.json()
                    total_pages = responses.get("pages")
                    operation_id.total_orders = responses.get('total')
                    # self.total_orders = responses.get('total')
                    if total_pages >= 1:
                        for total_page in range(1, total_pages + 1, 1):
                            if total_page <= 0:
                                continue
                            page_url = "{0}&orderStatus={1}&pageSize=100&page={2}&sortBy={3}".format(url,
                                                                                                     self.shipstation_order_status,
                                                                                                     total_page,
                                                                                                     'OrderDate')
                            response_data = self.shipstation_order_api_calling_function(configuration, page_url,
                                                                                        operation_id)
                            if response_data and response_data.status_code == 200:
                                responses = response_data.json()
                                orders = responses.get('orders')
                                if not orders:
                                    response_msg = "In Shipstation Import Order process, Not found Orders!  {0}".format(
                                        responses)
                                    self.create_shipstation_operation_details(operation_id, response_msg, True,
                                                                              'sale_order')
                                    # total_pages = total_pages - 1
                                    continue
                                if isinstance(orders, dict):
                                    orders = [orders]
                                product_datas = self.shipstation_order_managing_function_create(
                                    str(total_page) + ' ' + shipstation_to_date,
                                    configuration, orders,
                                    operation_id,
                                    product_operation_id,
                                    customer_operation_id)
                                if product_datas:
                                    create_csv_file = True
                            else:
                                error_code = "%s" % (response_data.status_code)
                                error_message = response_data.reason
                                error_detail = {'error': error_code + " - " + error_message + " - "}
                                if response_data.json():
                                    error_detail = {
                                        'error': error_code + " - " + error_message + " - %s" % (
                                            response_data.json())}
                                response_msg = "1 >>>>>>> Getting an Issue in the  Imported  Process %s" % (
                                    error_detail)
                                self.create_shipstation_operation_details(operation_id, response_msg, True,
                                                                          'sale_order')
                                self.process_msg = ' Process InCompleted Please Check Log'
                                _logger.info(response_msg)
                            self._cr.commit()

                            # if create_csv_file:
                            #     files_path = "/tmp/product_Details_{}/".format(fields.Date.today())
                            #     file_path = ("{}productDetails.csv".format(files_path))
                            #
                            #     csv_data = self.create_csv_file(files_path, file_path, [])
                            #     self.env['ir.attachment'].create({
                            #         'datas': csv_data,
                            #         'name': 'product_Details_{}.csv'.format(fields.Date.today()),
                            #         'res_model': 'shipstation.operation.detail',
                            #         'res_id': product_operation_id.id
                            #     })
                            #
                            # # For Customer import file in job
                            #
                            # customer_files_path = "/tmp/Customer_Details_{}/".format(fields.Date.today())
                            # customer_file_path = ("{}Customer_Details.csv".format(customer_files_path))
                            #
                            # customer_csv_data = self.create_csv_file(customer_files_path, customer_file_path, [])
                            # self.env['ir.attachment'].create({
                            #     'datas': customer_csv_data,
                            #     'name': 'Customer_Details_{}.csv'.format(fields.Date.today()),
                            #     'res_model': 'shipstation.operation.detail',
                            #     'res_id': operation_id.id
                            # })
                    else:
                        response_msg = "In Shipstation Import Order process, Not found Orders!  {0}".format(
                            responses)
                        self.create_shipstation_operation_details(operation_id, response_msg, True, 'sale_order')
                else:
                    error_code = "%s" % (response_data.status_code)
                    error_message = response_data.reason
                    error_detail = {'error': error_code + " - " + error_message + " - "}
                    if response_data.json():
                        error_detail = {
                            'error': error_code + " - " + error_message + " - %s" % (response_data.json())}
                    response_msg = "2 >>>>>>>> Getting an Issue in the  Imported  Process %s" % (error_detail)
                    self.create_shipstation_operation_details(operation_id, response_msg, True, 'sale_order')
                    self.process_msg = 'Process InCompleted Please Check Log'
                    _logger.info(response_msg)
                    self._cr.commit()
            except Exception as e:
                import traceback
                _logger.info(traceback.format_exc())
                response_msg = "3 >>>>>>>>>> Getting an Issue in the  Imported  Process %s" % (e)
                self.process_msg = ' Process InCompleted Please Check Log'
                _logger.info(response_msg)
                self.create_shipstation_operation_details(operation_id, response_msg, True, 'sale_order')
                self._cr.commit()
            from_order_date = datetime.now() - relativedelta(days=2)
            if not self.is_locked_date:
                self.last_modification_date = from_order_date
            _logger.info("Last Modification Date  >>>> {0}".format(self.last_modification_date))
            to_order_date = datetime.now() + relativedelta(hours=1)
            _logger.info("Current Date >>>> {}".format(to_order_date))
            to_order_date = to_order_date.strftime("%Y-%m-%d")  # %H:%M:%S
            self.shipstation_to_date = "{} 23:59:59".format(to_order_date)
            _logger.info("To Order Date  >>>> {0}".format(to_order_date))
            operation_id.message = 'Order Import Process Completed.'
            customer_operation_id.message = 'Customer Import Process Completed.'
            product_operation_id.message = 'Product Import Process Completed.'
            self.write({'process_msg': ' Shipstation Order Import Process Completed.'})

            # Unlink all product data, was store data in this model because of remove file data duplication.
            # shipstation_product_data_obj = self.env['shipstation.product.data']
            # shipstation_product_data_ids = shipstation_product_data_obj.search([('store_id', '=', self.id)])
            # shipstation_product_data_ids.unlink()
            #
            # shipstation_operation_data_obj = self.env['shipstation.operation.detail']
            # shipstation_operation_data_ids = shipstation_operation_data_obj.search([])
            # shipstation_process_ids = shipstation_operation_data_ids.filtered(lambda op: len(op.operation_ids) <= 0)
            # shipstation_process_ids.unlink()

            self._cr.commit()

    def action_view_shipstation_orders(self):
        action = self.env.ref('sale.action_quotations_with_onboarding').read()[0]
        action['domain'] = [('shipstation_store', '!=', False)]
        action['context'] = {'default_shipstation_store': self.id}
        return action

    def action_view_shipstation_customers(self):
        action = self.env.ref('base.action_partner_form').read()[0]
        action['domain'] = [('shipstation_customerId', '!=', False)]
        action['context'] = {'default_imported_from_shipstation': True}
        return action

    def action_view_shipstation_message_detail(self):
        action = self.env.ref('shipstation_shipping_odoo_integration.action_shipstation_operation_detail').read()[0]
        action['domain'] = [('shipstation_store_id', '=', self.id)]
        action['context'] = {'default_shipstation_store_id': self.id}
        return action


class ShipstationApiData(models.Model):
    _name = 'shipstation.api.data'
    _description = 'Shipstation API Data'

    name = fields.Char("Name")
    shipstation_configuration_id = fields.Many2one('shipstation.odoo.configuration.vts',
                                                   string='Shipstation Configuration')
    data = fields.Text("Data")
    operation_id = fields.Many2one("shipstation.operation.detail", "details")
    product_operation_id = fields.Many2one("shipstation.operation.detail", "product details")
    customer_operation_id = fields.Many2one("shipstation.operation.detail", "customer details")
    store_id = fields.Many2one("shipstation.store.vts", "Store")
    count = fields.Integer("Count")
    stage_id = fields.Selection(
        [('draft', 'Draft'), ('in_progress', 'In Progress'), ('done', 'Done'), ('error', 'Error')])
    active = fields.Boolean(
        'Active', default=True,
        help="To Archive api data")
    total_orders = fields.Integer(strin="Total Orders")
    processed_orders = fields.Integer(string="Processed Orders")

    def import_sale_orders_from_data_using_cron(self):
        data_ids = self.search([('stage_id', '=', 'in_progress')], order='id', limit=5)
        if not data_ids:
            data_ids = self.search([('stage_id', '=', 'draft')], order='id', limit=5)
        for record in data_ids:
            company_id = record.store_id.warehouse_id.company_id
            if record.count >= 5 or not record.data:
                record.stage_id = 'error'
                continue
            record.count += 1
            record.stage_id = 'in_progress'
            data = safe_eval(record.data)
            record.store_id.with_company(company_id).with_context(api_data=record).shipstation_order_managing_function(
                record.shipstation_configuration_id, data,
                record.operation_id, record.product_operation_id, False,
                False, False, record.customer_operation_id)

            record.stage_id = 'done'
            record.active = False

    def confirm_sale_orders_from_data_using_cron(self):
        shipstation_store_vts_obj = self.env['shipstation.store.vts']
        # data_ids = self.sudo().search([('active', 'in', [True, False])])
        # shipstationOrderIds = []
        # for record in data_ids:
        #     for data in safe_eval(record.data):
        #         shipstationOrderIds.append(data.get('orderId'))
        #     record.active = False
        exclude_sku_list = self.env["shipstation.exclude.skus"].sudo().get_param("shipstation.exclude_sku")

        sales_order = self.env['sale.order'].sudo().search(
            [('shipstation_order_id', '!=', False), ('state', '=', 'draft')], limit=70)
        if sales_order:
            for sale in sales_order:
                try:
                    exclude_sku = sale._is_exclude_sku(exclude_sku_list)
                    if exclude_sku:
                        continue
                    sale.with_company(sale.company_id).action_confirm()
                    _logger.info("Sales Order Confirmed  >>>> {0}".format(sale.name))
                    shipstation_store_vts_obj.with_company(sale.company_id).update_tracking_carrier(sale,
                                                                                                    sale.shipstation_configuration_id,
                                                                                                    False)
                    _logger.info("Sales Order Tracking Ref Updated  >>>> {0}".format(sale.carrier_tracking_ref))
                    # self._cr.commit()
                except Exception as e:
                    _logger.warning("Sales Order not Confirmed  >>>> {0} due to >>>> {1}".format(sale.name, e))
