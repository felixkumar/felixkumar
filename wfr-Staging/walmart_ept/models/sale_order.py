import json
import logging
from datetime import timedelta, datetime
from itertools import groupby

from odoo.exceptions import ValidationError

from odoo import models, fields, _

_logger = logging.getLogger("walmart_sale_order")

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _compute_get_walmart_status(self):
        """
        This method  Return Back Walmart Order Status.
        @param Noting to Param.
        @return: Set Update Walmart
        """
        for order in self:
            if order.walmart_marketplace_id:
                pickings = order.picking_ids.filtered(lambda x: x.state != "cancel")
                if pickings:
                    outgoing_picking = pickings.filtered(
                            lambda x: x.location_dest_id.usage == "customer")
                    if all(outgoing_picking.mapped("updated_in_walmart")):
                        order.updated_in_walmart = True
                        continue
                if order.state != 'draft' and order.moves_count > 0:
                    move_ids = self.env["stock.move"].search([("picking_id", "=", False),
                                                              ("sale_line_id", "in", order.order_line.ids)])
                    state = set(move_ids.mapped('state'))
                    if len(set(state)) == 1 and 'done' in set(state):
                        order.updated_in_walmart = True
                        continue
                order.updated_in_walmart = False
                continue
            order.updated_in_walmart = False

    def _search_walmart_order_ids(self, operator, value):
        query = """select so.id from stock_picking sp
                       inner join sale_order so on so.procurement_group_id=sp.group_id                   
                       inner join stock_location on stock_location.id=sp.location_dest_id and stock_location.usage='customer'
                       where sp.updated_in_walmart %s true and sp.state != 'cancel'
                   """ % (operator)
        if operator == '=':
            query += """union all
                       select so.id from sale_order as so
                       inner join sale_order_line as sl on sl.order_id = so.id
                       inner join stock_move as sm on sm.sale_line_id = sl.id
                       where sm.picking_id is NULL and sm.state = 'done' and so.walmart_marketplace_id notnull"""
        self._cr.execute(query)
        results = self._cr.fetchall()
        order_ids = []
        for result_tuple in results:
            order_ids.append(result_tuple[0])
        return [('id', 'in', order_ids)]

    walmart_seller_order_ref = fields.Char(string='Walmart SellerOrder Ref', copy=False,
                                           help='A unique ID that is associated with the seller')
    walmart_marketplace_order_ref = fields.Char(string='Walmart MarketplaceOrder Ref', copy=False,
                                                help='The Customer OrderId')

    walmart_marketplace_id = fields.Many2one('walmart.marketplace.ept', copy=False,
                                             string="Walmart Marketplace",
                                             help="Walmart Marketplace")
    is_sent_walmart_acknowledgement = fields.Boolean(string='Is Walmart Sent Acknowledgement',
                                                     copy=False,
                                                     help='Walmart orders are of Acknowledgement')
    walmart_fulfillment_type = fields.Selection(selection=[('wfs_fulfilled', 'WFS Fulfilled'),
                                                                 ('seller_fulfilled', 'Seller Fulfilled')],
                                                      string="Walmart Fulfillment")
    # Added By Harshit
    updated_in_walmart = fields.Boolean(string='Updated in Walmart',
                                        search="_search_walmart_order_ids",
                                        compute="_compute_get_walmart_status")
    _sql_constraints = [('unique_walmart_order',
                         'unique(walmart_seller_order_ref,walmart_marketplace_order_ref,walmart_marketplace_id)',
                         "Walmart order must be Unique.")]

    def import_walmart_orders(self, instance, start_date=False, end_date=False, order_status=False,
                              order_ids=False):
        """
                This method is used to call walmart API for importing orders,
                If Last Sync Time is available then system will take those orders
                after last import time till the current time.Otherwise System will
                take last 30 days orders.
                @param: Instance , Start/End Date, Order Status, Order_id
                @return: True

            """
        walmart_log_line_obj = self.env["common.log.lines.ept"]
        orders_imported = []
        all_log_lines = []
        if not start_date:
            if instance.last_sync_released_order_date:
                start_date = (instance.last_sync_released_order_date - timedelta(days=30)).strftime(
                        "%Y-%m-%dT%H:%M:%S") \
                             + 'Z'
                end_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + 'Z'
            else:
                today = datetime.now()
                start_date = (today - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S") + 'Z'
                end_date = today.strftime("%Y-%m-%dT%H:%M:%S") + 'Z'
        conn_obj = instance.get_walmart_connection()
        if not order_ids:
            _logger.info("Importing Released Orders from Walmart for Dates %s to %s...", start_date,
                         end_date)
            response = conn_obj.orders.all(order_status=order_status, createdStartDate=start_date,
                                           createdEndDate=end_date,
                                           limit=200)
            orders_data = response.get('list', {}).get('elements', {}).get('order', [])
        elif order_ids:
            _logger.info("Import Order with reference :{} ".format(order_ids))
            response = [conn_obj.orders.get(oid).get('order', {}) for oid in order_ids.split(',')]
            orders_data = response
        if not orders_data and not order_ids:
            start_date = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ").strftime(
                    "%Y-%m-%d %H:%M:%S")
            end_date = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%SZ").strftime(
                    "%Y-%m-%d %H:%M:%S")
            message = "Released Orders are not found between {} and {}.".format(start_date,
                                                                                end_date)
            _logger.info(message)
            log_line = walmart_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                            model_name=self._name,
                                                            res_id=False,
                                                            walmart_marketplace_id=instance.id,
                                                            log_line_type='fail',
                                                            mismatch_details=False,
                                                            operation_type="import")
            all_log_lines.append(log_line.id)
        elif not orders_data and order_ids:
            message = "No Orders found at walmart with reference :{}".format(order_ids)
            _logger.info(message)
            log_line = walmart_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                            model_name=self._name,
                                                            res_id=False,
                                                            walmart_marketplace_id=instance.id,
                                                            log_line_type='fail',
                                                            mismatch_details=True,
                                                            operation_type="import")
            all_log_lines.append(log_line.id)
        else:
            created_orders, log_lines = self.create_walmart_sale_order(orders_data, instance, conn_obj)
            orders_imported.extend(created_orders)
            all_log_lines.extend(log_lines)

            # more than 200 orders
            next_cursor = isinstance(response, dict) and \
                          response.get('list', {}).get('meta', {}).get('nextCursor', '')
            while next_cursor:
                _logger.info("Importing Orders from Walmart next_cursor...".format(next_cursor))
                response = conn_obj.orders.all(status=order_status, nextCursor=next_cursor,
                                               limit=200)
                if response:
                    if next_cursor == response.get('list', {}).get('meta', {}).get('nextCursor',
                                                                                   ''):
                        break
                    orders_data = response.get('list', {}).get('elements', {}).get('order', [])
                    next_cursor = response.get('list', {}).get('meta', {}).get('nextCursor', '')
                    created_orders, log_lines = self.create_walmart_sale_order(orders_data, instance, conn_obj)
                    orders_imported.extend(created_orders)
                    all_log_lines.extend(log_lines)

        return orders_imported, all_log_lines

    def create_walmart_sale_order(self, order_data_lines, instance, conn_obj):
        """
        This method processes the data and creates Orders from that.
        @author: Nikul Alagiya on Date 13/01/2022.
        """
        total_orders = len(order_data_lines)
        walmart_log_line_obj = self.env['common.log.lines.ept']
        created_orders = []
        all_log_lines = []
        for count, order_data_line in enumerate(order_data_lines, start=1):
            if isinstance(order_data_line,dict):
                order = order_data_line
            else:
                order_data = order_data_line.order_data
                order = json.loads(order_data)
            walmart_seller_order_ref = order.get('purchaseOrderId', '').strip()
            _logger.info("Importing Order:{} {} out of {}".format(
                    walmart_seller_order_ref, count, total_orders))
            walmart_marketplace_order_ref = order.get('customerOrderId', '').strip()

            if walmart_seller_order_ref and walmart_marketplace_order_ref:
                order_exist = self.search(
                        [('walmart_seller_order_ref', '=', walmart_seller_order_ref),
                         ('walmart_marketplace_order_ref', '=', walmart_marketplace_order_ref),
                         ('walmart_marketplace_id', '=', instance.id)])
                if order_exist:
                    created_orders.append(order_exist.id)
                    message = "Order {} already exists with walmart reference {}".format(
                            order_exist.name, walmart_seller_order_ref)
                    log_line_id = walmart_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                                    model_name=self._name, res_id=order_exist,
                                                                    order_ref=walmart_marketplace_order_ref,
                                                                    walmart_marketplace_id=instance.id,
                                                                    log_line_type='fail', mismatch_details=False,
                                                                    operation_type="import")
                    all_log_lines.append(log_line_id.id)
                    not isinstance(order_data_line,dict) and log_line_id.write({'walmart_order_queue_line_id':
                                                                                order_data_line.id})
                    _logger.info(message)
                    not isinstance(order_data_line,dict) and order_data_line.write({"state": "done", "processed_at":
                        datetime.now()})
                    continue

                order_lines = order.get('orderLines', {}).get('orderLine', [])

                if isinstance(order_lines, dict):
                    order_lines = [order_lines]
                if not order_lines:
                    message = "No Order lines with walmart reference {}".format(walmart_seller_order_ref)
                    log_line_id = walmart_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                                                  model_name=self._name,
                                                                                  res_id=order_exist,
                                                                                  order_ref=walmart_seller_order_ref,
                                                                                  walmart_marketplace_id=instance.id,
                                                                                  log_line_type='fail',
                                                                                  mismatch_details=False,
                                                                                  operation_type="import")
                    all_log_lines.append(log_line_id.id)
                    not isinstance(order_data_line,dict) and log_line_id.write({'walmart_order_queue_line_id':
                                                                                order_data_line.id})
                    _logger.info(message)
                    not isinstance(order_data_line,dict) and order_data_line.write({"state": "failed", "processed_at":
                        datetime.now()})
                    continue

                skip_order, log_lines = self.check_products_exists(instance, conn_obj, order_lines,
                                                                   walmart_seller_order_ref)
                all_log_lines.extend(log_lines)
                if log_lines and not isinstance(order_data_line, dict):
                    self.env['common.log.lines.ept'].browse(log_lines).write(
                            {'walmart_order_queue_line_id': order_data_line.id})

                if skip_order:
                    order_data_line.write({"state": "failed", "processed_at": datetime.now()})
                    continue

                queue_type = order_data_line.walmart_order_queue_id.queue_type
                customer = self.create_walmart_partner(instance, order)
                order_vals = self.prepare_walmart_sale_order_vals(customer, instance, order,
                                                                  order_lines, queue_type)
                sale_order = self.create(order_vals)
                _logger.info("Sale Order %s for %s is Created.", sale_order.name,
                             walmart_marketplace_order_ref)

                # Count Lead time
                ship_date = datetime.fromtimestamp(
                        order.get('shippingInfo', {}).get('estimatedShipDate', '') / 1e3)
                order_date = datetime.fromtimestamp(order.get('orderDate', '') / 1e3)
                lead_time = (ship_date.date() - order_date.date()).days
                self.create_walmart_sale_order_lines(
                        order_lines, sale_order, instance, lead_time)
                not isinstance(order_data_line,dict) and order_data_line.write({"state": "done", "processed_at":
                    datetime.now()})
                _logger.info("Starting Workflow process for order:{}-{}".format(
                        sale_order.name, sale_order.client_order_ref))
                # Delivery Done if Order is Shipped
                order_type = order.get('shipNode') and order.get('shipNode').get('type')
                if order_type in ['WFSFulfilled','Delivered'] or \
                        (not isinstance(order_data_line, dict) and \
                        order_data_line.walmart_order_queue_id.queue_type == 'Shipped'):
                    for create_order in sale_order:
                        create_order.auto_workflow_process_id.shipped_order_workflow_ept(create_order)
                    sale_order.write({'is_sent_walmart_acknowledgement': True})
                # if order_data_line.walmart_order_queue_id.queue_type == 'Shipped':
                #     sale_order.auto_workflow_process_id.shipped_order_workflow_ept(sale_order)
                #     sale_order.write({'is_sent_walmart_acknowledgement': True})
                # elif order_data_line.walmart_order_queue_id.queue_type == 'WFSOrder':
                #     sale_order.auto_workflow_process_id.shipped_order_workflow_ept(sale_order)
                #     sale_order.write({'is_sent_walmart_acknowledgement': True})
                else:
                    sale_order.process_orders_and_invoices_ept()
                sale_order and created_orders.append(sale_order.id)
                self._cr.commit()

        # Acknowledge Orders after importing released orders.
        _logger.info("Started Acknowledging Orders...")
        self.acknowledge_walmart_orders(instance)
        return created_orders, all_log_lines

    def check_products_exists(self, instance, conn_obj, order_lines, order_ref):
        """
        This method checks if all offers of the order exists or not.
        @author: Nikul Alagiya on Date 13/01/2022.
        """
        skip_order = False
        walmart_offer_obj = self.env["walmart.offer.ept"]
        product_obj = self.env["product.product"]
        walmart_log_line_obj = self.env['common.log.lines.ept']
        log_lines = []
        for order_line in order_lines:
            sku = order_line.get('item', {}).get('sku', '').strip()
            offer, odoo_product = walmart_offer_obj.search_walmart_offer_odoo_product(sku,
                                                                                      instance)
            if not offer or not odoo_product:
                skip_order, message = self.check_walmart_product_config(sku, odoo_product,
                                                                        instance)
                if skip_order:
                    log_line_id = walmart_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                                                  model_name=self._name,
                                                                                  res_id=False, default_code=sku,
                                                                                  order_ref=order_ref,
                                                                                  product_id=odoo_product.id,
                                                                                  walmart_marketplace_id=instance.id,
                                                                                  log_line_type='fail',
                                                                                  mismatch_details=False,
                                                                                  operation_type="import")
                    log_lines.append(log_line_id.id)
                    break
                else:
                    log_line_id = walmart_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                                                  model_name=self._name,
                                                                                  res_id=False, default_code=sku,
                                                                                  order_ref=order_ref,
                                                                                  product_id=odoo_product.id,
                                                                                  walmart_marketplace_id=instance.id,
                                                                                  log_line_type='success',
                                                                                  mismatch_details=False,
                                                                                  operation_type="import")
                    log_lines.append(log_line_id.id)
                    offer_response = conn_obj.items.get(id=sku)
                    if offer_response and offer_response.get('ItemResponse', []):
                        offer_details = offer_response.get('ItemResponse', [])[
                            0] if offer_response.get('ItemResponse', []) else {}
                        name = offer_details.get("productName", sku)

                        if not odoo_product:
                            odoo_product = product_obj.create({"name": name, "type": "product",
                                                               "default_code": sku})
                            _logger.info("Odoo Product {} is created while importing order {}".format(name, order_ref))

                        if not offer:

                            offer_vals = walmart_offer_obj.prepare_offer_vals(offer_details,
                                                                              instance)
                            if instance.environment == 'sandbox':
                                name = order_line.get('item', {}).get('productName')
                                sku = order_line.get('item', {}).get('sku')
                                offer_vals['product_name'] = name
                                offer_vals['walmart_sku'] = sku
                            offer_vals.update({"product_id": odoo_product.id})
                            walmart_offer_obj.create(offer_vals)
                    else:
                        skip_order = True
                        message = "Order %s is not imported due to\
                                                 Product response of [%s] not found." % (order_ref, sku)
                        _logger.info(message)
                        log_line_id = walmart_log_line_obj.create_common_log_line_ept(message=message,
                                                                                      module='walmart_ept',
                                                                                      model_name=self._name,
                                                                                      res_id=False, default_code=sku,
                                                                                      order_ref=order_ref,
                                                                                      product_id=odoo_product.id,
                                                                                      walmart_marketplace_id=instance.id,
                                                                                      log_line_type='fail',
                                                                                      mismatch_details=False,
                                                                                      operation_type="import")
                        log_lines.append(log_line_id.id)

        return skip_order, log_lines

    def check_walmart_product_config(self, sku, odoo_product, instance):
        """
        This method checks if odoo product exists or need to create.
        @author: Nikul Alagiya on Date 13/01/2022.
        """
        skip_order = False
        if odoo_product:
            message = 'Offer %s will created. Odoo Product already exists.' % sku
        elif not instance.auto_create_product_not_found_in_odoo:
            skip_order = True
            message = 'Order is not imported due to Product %s not found.' % sku
        else:
            message = 'Offer and Odoo Product Created for %s.' % sku
        # self.env['common.log.lines.ept'].create_common_log_line_ept(message=message, module='walmart_ept',
        #                                                               model_name=self._name,
        #                                                               res_id=False, default_code=sku,
        #                                                               product_id=odoo_product.id,
        #                                                               walmart_marketplace_id=instance.id,
        #                                                               log_line_type='fail',
        #                                                               mismatch_details=False,
        #                                                               operation_type="import")
        _logger.info(message)
        return skip_order, message

    def create_walmart_partner(self, marketplace, order):
        """
        It will search for customer, creates new if not found.
        @author: Nikul Alagiya on Date 13/01/2022.
        """
        res_partner_obj = self.env['res.partner']
        partner_vals = order.get('shippingInfo', {}).get('postalAddress', {})
        partner_vals = res_partner_obj.walmart_prepare_partner_vals(partner_vals)
        domain = partner_vals.keys()
        ship_partner_id = res_partner_obj._find_partner_ept(partner_vals, key_list=domain)
        if not ship_partner_id:
            partner_vals.update(
                    {"is_walmart_customer": True, "walmart_instance_id": marketplace.id})
            ship_partner_id = res_partner_obj.create(partner_vals)

        return ship_partner_id

    def prepare_walmart_sale_order_vals(self, customer, instance, order, order_lines, queue_type):
        """
        This method is used to prepare values for creating sale order.
        @author: Nikul Alagiya on Date 13/01/2022.
        """
        delivery_carrier_obj = self.env['delivery.carrier']
        seller_order_ref = order.get('purchaseOrderId', '').strip()

        if order.get('orderDate', False):
            order_date = datetime.fromtimestamp(order.get('orderDate', False) / 1e3).strftime(
                    '%Y-%m-%d %H:%M:%S')
        else:
            order_date = datetime.strftime('%Y-%m-%d %H:%M:%S')

        order_vals = {'partner_id': customer.id,
                      'warehouse_id': instance.warehouse_id.id or False,
                      'date_order': order_date,
                      'partner_invoice_id': customer.id,
                      'partner_shipping_id': customer.id,
                      'picking_policy': instance.walmart_auto_workflow_id.picking_policy or False,
                      'pricelist_id': instance.pricelist_id.id or False,
                      'payment_term_id': instance.payment_term_id.id or False,
                      'company_id': instance.company_id.id or False,
                      'team_id': instance.team_id.id or False,
                      "client_order_ref": seller_order_ref}
        if order.get('shipNode') and order.get('shipNode').get('type') == 'WFSFulfilled':
            order_vals.update({'warehouse_id' : instance.wfs_warehouse_id.id})
        # order_vals = self.create_sales_order_vals_ept(order_vals)

        if queue_type == 'WFSOrder':
            order_vals.update({'walmart_fulfillment_type': 'wfs_fulfilled'})
        else:
            order_vals.update({'walmart_fulfillment_type': 'seller_fulfilled'})

        if not instance.is_default_odoo_sequence_in_sales_order:
            order_vals.update(
                    {'name': "{} {}".format(instance.order_prefix and instance.order_prefix + '_' or '',
                                            seller_order_ref)})

        order_statuses = order_lines[0].get('orderLineStatuses', {}).get('orderLineStatus', [])
        order_status = order_statuses and order_statuses[0].get('status', '')
        is_acknowledged = order_status.lower() in ['shipped', 'delivered']
        method_code = order.get('shippingInfo', {}).get('methodCode', '').strip()
        carrier = delivery_carrier_obj.search(
                [('walmart_shipping_method_code', '=ilike', method_code)], limit=1)

        order_vals.update(
                {'walmart_seller_order_ref': seller_order_ref,
                 'walmart_marketplace_order_ref': order.get('customerOrderId',
                                                            '').strip(),
                 'walmart_marketplace_id': instance.id,
                 'auto_workflow_process_id': instance.walmart_auto_workflow_id.id or False,
                 'carrier_id': carrier.id,
                 'is_sent_walmart_acknowledgement': is_acknowledged
                 })

        return order_vals

    def create_walmart_sale_order_lines(self, order_lines, sale_order, instance, lead_time):
        """
        This method will create sale order lines.
        @author: Nikul Alagiya on Date 13/01/2022.
        """
        walmart_offer_obj = self.env["walmart.offer.ept"]
        sale_line_obj = self.env['sale.order.line']
        order_lines_list = []

        def key_func(k):
            return k['item']['sku']

        order_lines = sorted(order_lines, key=key_func)

        for key, values in groupby(order_lines, key=key_func):
            walmart_line_data = []
            price = shipping_total_amount = quantity = tax_amount = 0.0
            tax_id = instance.walmart_tax_id
            _logger.info("Creating Sale Order Line for order:{}-{}".format(
                    sale_order.name, sale_order.client_order_ref))
            item_sku = key
            total_product_lines = 0
            for order_line in list(values):
                total_product_lines += 1
                quantity += float(order_line.get('orderLineQuantity', {}).get('amount', 0.0) or 0.0)
                walmart_line_data.append(
                        (0, 0, {'line_number': order_line.get('lineNumber', '')}))
                charges = order_line.get('charges', {}).get('charge', [])
                for charge in charges:
                    charge_type = charge.get('chargeType', '').strip()
                    charge_amount = charge.get('chargeAmount', {}).get('amount', 0.0)
                    tax = charge.get('tax', {}) or {}
                    tax_amount += float(tax.get('taxAmount', {}).get('amount', 0.0) or 0.0)
                    if charge_type == 'PRODUCT':
                        price = float(charge_amount or 0.0)
                    else:
                        shipping_total_amount += float(charge_amount or 0.0)
                if not tax_id or tax_id.price_include:
                    price = price + float(tax.get('taxAmount', {}).get('amount', 0.0) or 0.0)
            if tax_id and float(tax_amount) > 0:
                item_tax_percent = ((float(tax_amount) * 100) / float(price)) / total_product_lines
            else:
                item_tax_percent = 0.0
            offer_id = walmart_offer_obj.search_walmart_offer_odoo_product(item_sku, instance)[0]

            if not offer_id:
                break

            order_line_vals = {'order_id': sale_order.id,
                               'product_id': offer_id.product_id.id or False,
                               'name': offer_id.product_name,
                               'product_uom_qty': float(quantity),
                               'price_unit': float(price),
                               'company_id': sale_order.company_id.id,
                               }
            # sale_line_vals = sale_line_obj.create_sale_order_line_ept(order_line_vals)
            sale_line_vals = order_line_vals
            sale_line_vals.update({'lead_time': lead_time,
                                   "walmart_order_line_ids": walmart_line_data,
                                   })
            if tax_id:
                sale_line_vals.update({'tax_id': [(6, 0, tax_id.ids)]})
            if hasattr(sale_line_obj, 'line_tax_amount_percent'):
                sale_line_vals.update({'line_tax_amount_percent': item_tax_percent})

            order_lines_list.append(sale_line_vals)

            # Add Shipping Line
            if shipping_total_amount > 0.0:
                _logger.info("Creating Shipping Order Line...")
                sale_line_vals = {'order_id': sale_order.id,
                         'product_id': instance.shipping_product_id.id,
                         'name': instance.shipping_product_id.name,
                         'product_uom_qty': 1.0,
                         'price_unit': shipping_total_amount}
                order_lines_list.append(sale_line_vals)
        sale_line_obj.create(order_lines_list)
        return True

    def cancel_sale_order_in_walmart(self):
        """
        This method will Cancel Order in Walmart
        :return:
        """
        walmart_cancel_order_obj = self.env['walmart.cancel.order.ept']
        walmart_cancel_list = []
        if self.state == 'draft':
            self.cancel_order_in_walmart()
        else:
            pickings = self.picking_ids.filtered(
                    lambda m: m.state not in ['waiting', 'cancel'])
            line_vals = []
            for move in pickings.mapped('move_lines'):
                sale_line_id = move.sale_line_id
                if not sale_line_id and move.state == 'done':
                    continue
                line_vals.append([(0, 0, {
                    'product_id': sale_line_id.product_id.id,
                    'quantity': "1",
                    "walmart_line_number":
                        sale_line_id.walmart_order_line_ids.mapped('line_number')}
                                   )])
            walmart_cancel_list.append(
                    walmart_cancel_order_obj.create(
                            {
                                'sale_order_id': self.id,
                                'walmart_cancel_order_line_ids': line_vals
                            }
                    ).id
            )

        if not walmart_cancel_list:
            raise ValidationError(_("There are no products found for the Cancel in Walmart  !!"))
        return {'type': 'ir.actions.act_window',
                'res_model': 'walmart.cancel.order.ept',
                'view_type': 'form',
                'view_mode': 'form',
                'context': {'default_sale_order_id': self.id,
                            'default_walmart_cancel_order_line_ids': [
                                (6, 0, walmart_cancel_list)]},
                'target': 'new'}

    def cancel_order_in_walmart(self):
        """
        This method will cancel Order in walmart.
        :return: True
        """
        walmart_log_obj = self.env['common.log.book.ept']
        walmart_log_lines_obj = self.env['common.log.lines.ept']
        model_id = walmart_log_lines_obj.get_model_id(self._name)
        order_line_number_list = []
        if self.walmart_marketplace_id:
            purchase_order_id = self.walmart_seller_order_ref
            instance_id = self.walmart_marketplace_id
            log_book_id = walmart_log_obj.create_common_log_book(
                    model_id=model_id,
                    instance_field='walmart_marketplace_id',
                    instance=instance_id, process_type='export', module='walmart_ept'
            )
            walmart_conn_obj = instance_id.get_walmart_connection()
            for order_line in self.order_line.filtered(
                    lambda line: line.product_id.type == 'product'
            ):
                order_line_number_list = [str(lno) for lno in
                                          order_line.walmart_order_line_ids.mapped('line_number')]
            if purchase_order_id and order_line_number_list:
                try:
                    response = walmart_conn_obj.orders.cancel(
                            purchase_order_id, order_line_number_list)
                    if response.status_code != 200:
                        message = '%d - %s .' % (
                            response.status_code, response.content.decode("utf-8"))
                        walmart_log_lines_obj.create_log_lines(
                                log_book_id=log_book_id,
                                model_id=log_book_id.model_id.id,
                                message=message,
                                res_id=False,
                                order_ref=purchase_order_id
                        )
                    else:
                        json_result = response
                        status = json_result.get("ns4:errors", {}).get("ns4:rror", {}).get(
                                "ns4:severity", "")
                        if status == 'ERROR':
                            message = '%s .' % (json_result)
                            walmart_log_lines_obj.create_log_lines(
                                    log_book_id=log_book_id,
                                    model_id=log_book_id.model_id.id,
                                    message=message,
                                    res_id=False,
                                    order_ref=purchase_order_id
                            )


                except Exception as err:
                    _logger.exception(err)
                    walmart_log_lines_obj.create_log_lines(
                            log_book_id=log_book_id,
                            model_id=log_book_id.model_id.id,
                            message=err,
                            res_id=False,
                            order_ref=purchase_order_id
                    )
                    raise ValidationError(_(err))

        return True

    def acknowledge_walmart_orders(self, instance):
        """
        This method acknowledges the orders which are not acknowledged yet.
        @author: Nikul Alagiya on Date 13/01/2022.
        """
        acknowledge_remain_orders = self.search([('is_sent_walmart_acknowledgement', '=', False),
                                                 ('walmart_marketplace_id', '=', instance.id)])
        conn_obj = instance.get_walmart_connection()

        for order in acknowledge_remain_orders:
            _logger.info("Acknowledging Order %s with Ref %s...", order.name,
                         order.walmart_seller_order_ref)
            response = conn_obj.orders.acknowledge(order.walmart_seller_order_ref)
            if not response or not response.get('order', {}):
                self.env['common.log.lines.ept'].create_common_log_line_ept(
                    message="Order not being Acknowledged due to response not received from Walmart", module='walmart_ept',
                    model_name=self._name, res_id=False, order_ref=order.walmart_seller_order_ref,
                    walmart_marketplace_id=instance.id, log_line_type='fail', mismatch_details=False, operation_type="export")
                order.update({'is_sent_walmart_acknowledgement': True})
                self._cr.commit()
            order.update({'is_sent_walmart_acknowledgement': True})
            self._cr.commit()
        return True

    def walmart_update_order_status(self, instance):
        """
        This method updates order status into Walmart.
        @author: Nikul Alagiya on Date 18/01/2022.
        """
        _logger.info("Started Update Order Status Process...")
        conn_obj = instance.get_walmart_connection()

        sales_pickings = self.find_not_updated_order_status(instance)

        self.sale_orders_update_status(conn_obj, instance, sales_pickings)
        return True

    def sale_orders_update_status(self, conn_obj, instance, sales_pickings):
        """
        This method updates order status into Walmart.
        @author: Nikul Alagiya on Date 18/01/2022.
        """
        if not sales_pickings:
            self.env['common.log.lines.ept'].create_common_log_line_ept(
                message='No orders are there for updating order status.', module='walmart_ept',
                model_name=self._name, res_id=False, walmart_marketplace_id=instance.id,
                log_line_type='fail', mismatch_details=True, operation_type="export")
            _logger.info("No Orders found for Update Order Status.")
            return True

        for sale_id, picking_ids in sales_pickings.items():
            # out_pickings = sale_order.picking_ids.filtered(
            #         lambda x: not x.updated_in_walmart and x.picking_type_id.code == 'outgoing' and \
            #                   x.state == 'done' and x.location_dest_id.usage == 'customer')
            # if not out_pickings:
            #     _logger.info("No Picking found of Order %s for Update Order Status.",
            #                  sale_order.name)
            #     self.env['common.log.lines.ept'].create_common_log_line_ept(
            #         message='No Picking found of Order %s for Update Order Status.' % sale_order.name,
            #         module='walmart_ept', model_name=self._name, res_id=False, walmart_marketplace_id=instance.id,
            #         log_line_type='fail', mismatch_details=True, operation_type="export")
            #     continue
            sale_order = self.env['sale.order'].browse(sale_id)
            out_pickings = self.env['stock.picking'].browse(picking_ids)

            lines = []
            self.update_walmart_line_export(out_pickings, lines)
            order_ref = sale_order.walmart_seller_order_ref
            _logger.info("Updating Order Status of %s for Ref %s...", sale_order.name, order_ref)
            self.create_shipment_order_and_status(conn_obj, order_ref, lines, sale_order, instance, out_pickings)

    def create_shipment_order_and_status(self, conn_obj, order_ref, lines, sale_order, instance, out_pickings):
        """
        This method create shipment order and status into Walmart.
        @author: Nikul Alagiya on Date 18/01/2022.
        """
        response = {}
        if order_ref and lines:
            try:
                response = conn_obj.orders.create_shipment(order_ref, lines)
            except Exception as error:
                _logger.exception(error)
            if not isinstance(response, dict):
                self.env['common.log.lines.ept'].create_common_log_line_ept(
                    message="The order status has not been updated since Walmart has not provided data in json format!",
                    module='walmart_ept', model_name=self._name, res_id=sale_order.id,
                    walmart_marketplace_id=instance.id, order_ref=order_ref,
                    log_line_type='fail', mismatch_details=True, operation_type="export")
                return False
            if response:
                line_statuses = \
                    response.get('order', {}).get('orderLines', {}).get('orderLine', [])[
                        0].get('orderLineStatuses')
                if line_statuses:
                    out_pickings.write({'updated_in_walmart': True})
                    _logger.info("Order Status Updated of %s...", sale_order.name)
            elif response and response.status_code != 400:
                _logger.info("Order Status Not Updated of %s for Ref %s...",
                             sale_order.name, order_ref)
                self.env['common.log.lines.ept'].create_common_log_line_ept(
                    message='Order Status not updated as response was not fetched from Walmart',
                    module='walmart_ept', model_name=self._name, res_id=sale_order.id,
                    walmart_marketplace_id=instance.id, order_ref=order_ref,
                    log_line_type='fail', mismatch_details=True, operation_type="export")
        return True

    def update_walmart_line_export(self, out_pickings, lines):
        """
        This method updates order status into Walmart.
        and lines list prepare.
        @author: Nikul Alagiya on Date 18/01/2022.
        """
        for out_picking in out_pickings:
            carrier_code = out_picking.carrier_id.walmart_carrier_code
            tracking_ref = out_picking.carrier_tracking_ref.split(',')[0] if out_picking.carrier_tracking_ref else ''

            if out_picking.date_done:
                ship_date = out_picking.date_done
            else:
                ship_date = datetime.now()

            data = {
                'seller_order_id': '',
                'uom': 'EACH',
                'status': "Shipped",
                'ship_time': ship_date,
                'tracking_number': tracking_ref,
                'carrier_service': out_picking.carrier_id.walmart_shipping_method_code or '',
                "carrier": carrier_code if carrier_code else "",
                "other_carrier": "" if carrier_code else out_picking.carrier_id.name or "",
                "tracking_url": "" if carrier_code else out_picking.carrier_tracking_url \
                                                        or "",
            }
            data.update(self.get_return_center_address())
            order_lines = out_picking.move_ids.mapped("sale_line_id")
            self.prepare_order_line(order_lines, data, lines)

    def prepare_order_line(self, order_lines, data, lines):
        """
        This method updates order status into Walmart.
        and lines list prepare.
        @author: Nikul Alagiya on Date 18/01/2022.
        """
        for order_line in order_lines:
            quantity = 0.0
            for walmart_line in order_line.walmart_order_line_ids:
                if order_line.qty_delivered == quantity:
                    break
                if walmart_line.exported_in_walmart:
                    continue
                line_data = data.copy()
                line_data.update({'line_number': str(walmart_line.line_number),
                                  'quantity': 1.0})
                lines.append(line_data)
                #walmart_line.exported_in_walmart = True
                quantity += 1.0

    def find_not_updated_order_status(self, instance):
        """
        This method is used to search sale orders, which are not updated in Walmart.
        @author: Nikul Alagiya on Date 13/10/2022.
        """
        #return self.search([('warehouse_id', '=', instance.warehouse_id.id),
        #                    ('walmart_marketplace_order_ref', '!=', False),
        #                    ('walmart_seller_order_ref', '!=', False),
        #                    ('walmart_marketplace_id', '=', instance.id), ('state', '!=', 'cancel'),
         #                   ('updated_in_walmart', '=', False)], order='date_order')
        location_obj = self.env["stock.location"]
        stock_picking_obj = self.env["stock.picking"]
        customer_locations = location_obj.search([("usage", "=", "customer")])
        picking_ids = stock_picking_obj.search([("walmart_instance_id", "=", instance.id),
                                                ("updated_in_walmart", "=", False),
                                                ("state", "=", "done"),
                                                ("location_dest_id", "in", customer_locations.ids)],
                                               order="date")
        sales_pickings = {}
        def prepare_sale_pickings_dict(picking):
            sale_id = picking.sale_id.id
            existing_picking = sales_pickings.get(sale_id, [])
            existing_picking.append(picking.id)
            sales_pickings.update({sale_id: existing_picking})
            return sale_id


        list(map(prepare_sale_pickings_dict, picking_ids))

        # order_ids = picking_ids.mapped('sale_id')
        return sales_pickings

    def get_return_center_address(self):
        """
        It prepares return address for shipped order.
        @author: Nikul Alagiya on Date 18/01/2022.
        """
        partner = self.warehouse_id.partner_id
        if not partner:
            partner = self.env.user.company_id.partner_id

        return {'name': partner.name,
                'address1': partner.street or '',
                'address2': partner.street2 if partner.street2 else 'null',
                'city': partner.city or '',
                'state': partner.state_id.code or '',
                'postalCode': partner.zip or '',
                'country': partner.country_id.walmart_marketplace_code or '',
                'dayPhone': partner.phone or '',
                'emailId': partner.email or ''}

    def _prepare_invoice(self):
        """
        Add walmart_instance_idWhen invoice create
        @author: Nikul Alagiya
        :return:
        """
        res = super(SaleOrder, self)._prepare_invoice()
        res.update(({'walmart_instance_id': self.walmart_marketplace_id.id}))
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    lead_time = fields.Integer(string="Walmart lead time")
    walmart_order_line_ids = fields.One2many("walmart.order.line.ept", "order_line_id", copy=False)


class WalmartOrderLine(models.Model):
    _name = "walmart.order.line.ept"
    _description = "Walmart Order Line"
    _rec_name = "line_number"

    line_number = fields.Integer(help="Walmart Order Line Number")
    order_line_id = fields.Many2one("sale.order.line", ondelete="cascade")
    exported_in_walmart = fields.Boolean()
