import base64
import json
import logging
import time
from datetime import datetime
from requests import request
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    shipstation_carrier_id = fields.Many2one('shipstation.delivery.carrier', string='Shipstation Carrier')
    shipstation_delivery_carrier_service_id = fields.Many2one('shipstation.delivery.carrier.service',
                                                              string='Shipstation Delivey Carrier Service')
    delivery_type = fields.Selection(selection_add=[('shipstation', 'Shipstation')],
                                     ondelete={'shipstation': 'set default'})
    delivery_package_id = fields.Many2one('shipstation.delivery.package', string='Shipstation Package Code')
    weight_uom = fields.Selection([('pounds', 'pounds'), ('ounces', 'ounces'), ('grams', 'grams')], default="pounds",
                                  string='Weight UOM')
    shipstation_dimentions = fields.Selection([('inches', 'inches'), ('centimeters', 'centimeters')], default="inches",
                                              string='Shipstation Dimentions')
    confirmation = fields.Selection(
        [('none', 'None'), ('delivery', 'Delivery'), ('signature', 'Signature'), ('adult_signature', 'adult_signature'),
         ('direct_signature', 'direct_signature')], default="none",
        string='Shipstation Confirmation')
    store_id = fields.Many2one('shipstation.store.vts', "Store")
    shipstation_configuration_id = fields.Many2one('shipstation.odoo.configuration.vts',
                                                   string='Shipstation Configuration')

    def get_total_weight(self, weight=1):
        pound_for_kg = 2.20462
        ounce_for_kg = 35.274
        grams_for_kg = 1000
        ounce_for_lb = 16
        grams_for_lb = 453.592
        uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        if self.weight_uom == "pounds" and uom_id.name in ['lb', 'lbs', 'Lb']:
            return round(weight, 3)
        elif self.weight_uom == "pounds" and uom_id.name == 'kg':
            return round(weight * pound_for_kg, 3)
        elif self.weight_uom == "ounces" and uom_id.name in ['lb', 'lbs']:
            return round(weight * ounce_for_lb, 3)
        elif self.weight_uom == "ounces" and uom_id.name == 'kg':
            return round(weight * ounce_for_kg, 3)
        elif self.weight_uom == "grams" and uom_id.name == 'kg':
            return round(weight * grams_for_kg, 3)
        else:
            return round(weight * grams_for_lb, 3)

    def check_order_data(self, order):
        lines_without_weight = order.order_line.filtered(
            lambda line_item: not line_item.product_id.type in ['service',
                                                                'digital'] and not line_item.product_id.weight and not line_item.is_delivery)
        for order_line in lines_without_weight:
            return _("Please define weight in product : \n %s") % order_line.product_id.name
        receiver_address = order.partner_shipping_id
        sender_address = order.warehouse_id.partner_id
        if not receiver_address.zip or not receiver_address.country_id or not receiver_address.city:
            return _("Please define proper receiver address.")
        if not sender_address.zip or not sender_address.country_id or not sender_address.city:
            return _("Please define proper Sender address.")

        return False

    def api_calling_function(self, url_data, body):
        url = self.shipstation_configuration_id.making_shipstation_url(url_data)
        api_secret = self.shipstation_configuration_id.api_secret
        api_key = self.shipstation_configuration_id.api_key
        data = "%s:%s" % (api_key, api_secret)
        encode_data = base64.b64encode(data.encode("utf-8"))
        authrization_data = "Basic %s" % (encode_data.decode("utf-8"))
        headers = {"Authorization": authrization_data,
                   "Content-Type": "application/json"}
        data = json.dumps(body)
        _logger.info("Request Data: %s" % (data))
        try:
            response_body = request(method='POST', url=url, data=data, headers=headers)
        except Exception as e:
            raise ValidationError(e)
        return response_body

    def shipstation_rate_shipment(self, order):
        checked_order_data = self.check_order_data(order)
        shipping_charge_obj = self.env['shipstation.shipping.charge']
        if checked_order_data:
            return {'success': False, 'price': 0.0, 'error_message': checked_order_data,
                    'warning_message': False}
        receiver_address = order.partner_shipping_id
        sender_address = order.warehouse_id.partner_id

        weight = sum(
            [(line.product_id.weight * line.product_uom_qty) for line in order.order_line if not line.is_delivery])
        total_weight = self.get_total_weight(weight)
        dict_rate = {
            "carrierCode": "%s" % (
                    self.shipstation_carrier_id and self.shipstation_carrier_id.code),
            "packageCode": "%s" % (self.delivery_package_id and self.delivery_package_id.package_code),
            "fromPostalCode": "%s" % (sender_address.zip),
            "toState": "%s" % (receiver_address.state_id and receiver_address.state_id.code),
            "toCountry": "%s" % (receiver_address.country_id and receiver_address.country_id.code),
            "toPostalCode": "%s" % (receiver_address.zip),
            "toCity": receiver_address.city,
            "weight": {
                "value": total_weight,
                "units": self.weight_uom or "pounds"
            },
            "dimensions": {
                "units": self.shipstation_dimentions or "inches",
                "length": self.delivery_package_id and self.delivery_package_id.length or 0.0,
                "width": self.delivery_package_id and self.delivery_package_id.width or 0.0,
                "height": self.delivery_package_id and self.delivery_package_id.height or 0.0
            },
            "confirmation": self.confirmation or "none",
            "residential": self.shipstation_delivery_carrier_service_id and self.shipstation_delivery_carrier_service_id.residential_address
        }
        is_website = self.env['ir.module.module'].search([('name', '=', 'website')])
        if is_website and is_website.state == 'installed' and order.website_id:
            dict_rate.update({
                "serviceCode": "%s" % (
                        self.shipstation_delivery_carrier_service_id and self.shipstation_delivery_carrier_service_id.service_code),
            })
        else:
            existing_records = self.env['shipstation.shipping.charge'].search(
                [('sale_order_id', '=', order and order.id)])
            if existing_records:
                existing_records.sudo().unlink()
        try:
            response_data = self.api_calling_function("/shipments/getrates", dict_rate)
            if response_data.status_code == 200:
                responses = response_data.json()
                _logger.info("Response Data: %s" % (responses))
                if is_website and is_website.state == 'installed' and order.website_id:
                    for rate in responses:
                        is_service_available = self.shipstation_delivery_carrier_service_id.search(
                            [("service_code", '=', rate.get('serviceCode'))])
                        if is_service_available:
                            return {'success': True, 'price': rate.get('shipmentCost') or 0.0,
                                    'error_message': False, 'warning_message': False}
                        else:
                            return {'success': False, 'price': 0.0, 'error_message': "Service is not available.",
                                    'warning_message': False}
                self._cr.commit()
                if responses:
                    for response in responses:
                        shipping_charge_obj.sudo().create(
                            {'shipstation_provider': self.shipstation_carrier_id.code,
                             'shipstation_service_code': response.get('serviceCode'),
                             'shipstation_service_name': response.get('serviceName'),
                             'shipping_cost': response.get('shipmentCost', 0.0),
                             'other_cost': response.get('otherCost', 0.0),
                             'sale_order_id': order and order.id})
                        self._cr.commit()
                    shipstation_charge_id = self.env['shipstation.shipping.charge'].search(
                        [('sale_order_id', '=', order and order.id),
                         ('shipstation_service_code', '=', self.shipstation_delivery_carrier_service_id.service_code)],
                        limit=1)
                    if not shipstation_charge_id:
                        shipstation_charge_id = self.env['shipstation.shipping.charge'].search(
                            [('sale_order_id', '=', order and order.id),
                             ('shipstation_provider', '=', self.shipstation_carrier_id.code)], order='shipping_cost',
                            limit=1)
                    order.shipstation_shipping_charge_id = shipstation_charge_id and shipstation_charge_id.id
                    rate_amount = shipstation_charge_id.shipping_cost + shipstation_charge_id.other_cost
                    return {'success': True, 'price': rate_amount or 0.0,
                            'error_message': False, 'warning_message': False}
                else:
                    return {'success': False, 'price': 0.0, 'error_message': "Service Not Supported.",
                            'warning_message': False}

            elif response_data.status_code == 500:
                error_message_details = ""
                if response_data.json():
                    error_response_data = response_data.json()
                    error_message_details = error_response_data.get('ExceptionMessage')
                return {'success': False, 'price': 0.0,
                        'error_message': "%s" % (error_message_details),
                        'warning_message': False}
            else:
                error_code = "%s" % (response_data.status_code)
                error_message = response_data.reason
                error_detail = {'error': error_code + " - " + error_message + " - "}
                return {'success': False, 'price': 0.0, 'error_message': error_detail,
                        'warning_message': False}
        except Exception as e:
            return {'success': False, 'price': 0.0, 'error_message': e,
                    'warning_message': False}

    def generate_label_from_shipstation(self, picking, package_id=False, weight=False):
        picking_receiver_id = picking.partner_id
        picking_sender_id = picking.picking_type_id.warehouse_id.partner_id
        shipstation_carrier_code = self.env['shipstation.delivery.carrier'].search(
            [('code', '=', self.shipstation_carrier_id.code)])
        # weight = picking.shipping_weight
        package_length = package_id.package_type_id.packaging_length if package_id and package_id.package_type_id else self.delivery_package_id.length
        # package_id = package_id and package_id.packaging_id
        shipstation_shipping_charge_id = picking.sale_id.shipstation_shipping_charge_id
        shipstation_service_code = shipstation_shipping_charge_id.shipstation_service_code if picking.sale_id.shipstation_shipping_charge_id else picking.carrier_id.shipstation_delivery_carrier_service_id.service_code
        custom_package_id = package_id and package_id.package_type_id or self.delivery_package_id
        total_weight = self.get_total_weight(weight)
        request_data = {
            "orderId": "%s" % (picking.shipstation_order_id),
            "carrierCode": "%s" % (self.shipstation_carrier_id and self.shipstation_carrier_id.code),
            "serviceCode": "%s" % (shipstation_service_code),
            "packageCode": "%s" % ((
                                       package_id.package_type_id.shipper_package_code if package_id and package_id.package_type_id and package_id.package_type_id else self.delivery_package_id.package_code) or ""),
            "confirmation": self.confirmation or "none",
            "shipDate": "%s" % (time.strftime("%Y-%m-%d")),
            "testLabel": True if not self.prod_environment else False,
            "weight": {
                "value": total_weight,
                "units": self.weight_uom or "pounds",
            },
            "dimensions": {
                "units": self.shipstation_dimentions or "inches",
                "length": package_length or 0.0,
                "width": custom_package_id.width or 0.0,
                "height": custom_package_id.height or 0.0
            },
        }
        if len(shipstation_carrier_code) > 1 and self.shipstation_carrier_id.shipping_provider_id:
            request_data.get('advancedOptions').update({"billToParty": "my_other_account",
                                                        "billToMyOtherAccount": self.shipstation_carrier_id.shipping_provider_id})
        return request_data

    def get_order_item_details(self, picking):
        res = []
        count = 0
        for move_line in picking.move_ids:
            total_weight = self.get_total_weight(move_line.product_id.weight)
            count = count + 1
            item_dict = {
                "lineItemKey": "%s" % (count),
                "sku": "%s" % (move_line.product_id and move_line.product_id.default_code),
                "name": "%s" % (move_line.product_id and move_line.product_id.name),
                "weight": {
                    "value": "%s" % (total_weight),
                    "units": self.weight_uom or "pounds"
                },
                "quantity": int(move_line.product_uom_qty),
                "unitPrice": "%s" % (
                    move_line.sale_line_id.price_unit if move_line.sale_line_id.price_unit else move_line.product_id and move_line.product_id.lst_price),
                "taxAmount": "%s" % (move_line.sale_line_id.price_tax if move_line.sale_line_id.price_tax else 0.0),
                "productId": "%s" % (move_line.product_id and move_line.product_id.id)}
            res.append(item_dict)
        return res

    def create_or_update_order(self, picking):
        store_id = self._context.get('shipstation_store')
        if not store_id:
            store_id = self.carrier_id
        if not store_id:
            raise ValidationError("Store Not Configured!")
        picking_receiver_id = picking.partner_id
        picking_sender_id = picking.picking_type_id.warehouse_id.partner_id
        total_value = picking.sale_id.amount_total if picking.sale_id.amount_total else sum(
            [(line.product_uom_qty * line.product_id.list_price) for line in picking.move_ids]) or 0.0
        warehouse_id = picking and picking.picking_type_id and picking.picking_type_id.warehouse_id and picking.picking_type_id.warehouse_id.shipstation_warehouse_id and picking.picking_type_id.warehouse_id.shipstation_warehouse_id.warehouse_id
        weight = picking.shipping_weight
        total_tax = picking.sale_id.amount_tax
        total_weight = self.get_total_weight(weight)
        shipstation_carrier_code = self.env['shipstation.delivery.carrier'].search(
            [('code', '=', self.shipstation_carrier_id.code)])
        date_order = picking.scheduled_date
        if date_order:
            order_date_formate = datetime.strptime(str(date_order), "%Y-%m-%d %H:%M:%S")
            order_date = order_date_formate.strftime('%Y-%m-%dT%H:%M:%S')
            request_data = {
                "orderNumber": "%s" % (picking.origin if picking.origin else picking.name),
                "orderDate": "%s" % (order_date),
                "shipByDate": "%s" % (order_date),
                "orderStatus": "awaiting_shipment",
                "customerUsername": "%s" % (picking_receiver_id.name),
                "customerEmail": "%s" % (picking_receiver_id.email or ""),
                "billTo": {
                    "name": "%s" % (picking_receiver_id.name),
                    "company": "%s" % (picking_receiver_id.parent_id.name if picking_receiver_id.parent_id else ""),
                    "street1": "%s" % (picking_receiver_id.street or ""),
                    "street2": "%s" % (picking_receiver_id.street2 or ""),
                    "city": "%s" % (picking_receiver_id.city or ""),
                    "state": "%s" % (picking_receiver_id.state_id and picking_receiver_id.state_id.code or ""),
                    "postalCode": "%s" % (picking_receiver_id.zip or ""),
                    "country": "%s" % (picking_receiver_id.country_id and picking_receiver_id.country_id.code or ""),
                    "phone": "%s" % (picking_receiver_id.phone or ""),
                    "residential": self.shipstation_delivery_carrier_service_id and self.shipstation_delivery_carrier_service_id.residential_address
                },
                "shipTo": {
                    "name": "%s" % (picking_receiver_id.name),
                    "company": "%s" % (picking_receiver_id.parent_id.name if picking_receiver_id.parent_id else ""),
                    "street1": "%s" % (picking_receiver_id.street or ""),
                    "street2": "%s" % (picking_receiver_id.street2 or ""),
                    "city": "%s" % (picking_receiver_id.city or ""),
                    "state": "%s" % (picking_receiver_id.state_id and picking_receiver_id.state_id.code or ""),
                    "postalCode": "%s" % (picking_receiver_id.zip or ""),
                    "country": "%s" % (picking_receiver_id.country_id and picking_receiver_id.country_id.code or ""),
                    "phone": "%s" % (picking_receiver_id.phone or ""),
                    "residential": self.shipstation_delivery_carrier_service_id and self.shipstation_delivery_carrier_service_id.residential_address
                },
                "items": self.get_order_item_details(picking),
                "amountPaid": total_value,
                "taxAmount": total_tax,
                "shippingAmount": sum(
                    picking.sale_id.mapped('order_line').filtered(lambda line: line.is_delivery == True).mapped(
                        'price_subtotal')) or 0.0,
                "carrierCode": "%s" % (self.shipstation_carrier_id and self.shipstation_carrier_id.code),
                "serviceCode": "%s" % (
                        self.shipstation_delivery_carrier_service_id and self.shipstation_delivery_carrier_service_id.service_code),
                "packageCode": "%s" % (self.delivery_package_id and self.delivery_package_id.package_code or ""),
                "confirmation": self.confirmation or "none",
                "internalNotes": "{}".format(picking.note or ' '),
                "shipDate": "%s" % (order_date),
                "weight": {
                    "value": total_weight,
                    "units": "%s" % (self.weight_uom)
                },
                "dimensions": {
                    "units": "%s" % (self.shipstation_dimentions),
                    "length": self.delivery_package_id and self.delivery_package_id.length or 0.0,
                    "width": self.delivery_package_id and self.delivery_package_id.width or 0.0,
                    "height": self.delivery_package_id and self.delivery_package_id.height or 0.0,
                },
                "insuranceOptions": {
                    "provider": "%s" % (self.shipstation_carrier_id and self.shipstation_carrier_id.code),
                    "insureShipment": False,
                    "insuredValue": 0
                },
                # "internationalOptions": {
                #     "contents": picking.name,
                #     "customsItems": ""
                # },

                "advancedOptions": {
                    # TODO We need to send when import wh from shipstation "warehouseId": ,
                    "storeId": store_id and store_id.store_id or ""

                },
                "tagIds": [picking.id]
            }
            if warehouse_id:
                request_data.get('advancedOptions').update({"warehouseId": "{}".format(warehouse_id)})
            if len(shipstation_carrier_code) > 1 and self.shipstation_carrier_id.shipping_provider_id:
                request_data.get('advancedOptions').update({"billToParty": "my_other_account",
                                                            "billToMyOtherAccount": self.shipstation_carrier_id.shipping_provider_id})
        custom_items = []
        is_account_intrastat = self.env['ir.module.module'].search([('name', '=', 'account_intrastat')])
        if picking_sender_id and picking_receiver_id and picking_sender_id.country_id and picking_receiver_id.country_id and picking_sender_id.country_id.code != picking_receiver_id.country_id.code and is_account_intrastat and is_account_intrastat.state == 'installed':
            check_commodity = picking.move_line_ids.mapped('product_id').filtered(
                lambda produtct_id: not produtct_id.intrastat_code_id).mapped('name')
            if check_commodity:
                raise ValidationError("You Are Sending International Shipment \n But {} has no commodity code".format(
                    ', '.join(check_commodity)))
            check_origin_country = picking.move_line_ids.mapped('product_id').filtered(
                lambda produtct_id: not produtct_id.intrastat_origin_country_id).mapped('name')
            if check_origin_country:
                raise ValidationError(
                    "You Are Sending International Shipment \n But {} has no country origin code".format(
                        ', '.join(check_commodity)))
            for move in picking.move_ids:
                data = {
                    'description': "%s" % (move.product_id and move.product_id.name),
                    "quantity": "{}".format(int(move and move.product_uom_qty)),
                    "value": "{}".format(move.product_id and move.product_id.lst_price),
                    "harmonizedTariffCode": "{}".format(
                        move and move.product_id.intrastat_code_id and move.product_id.intrastat_code_id.code),
                    "countryOfOrigin": "{}".format(
                        move and move.product_id.intrastat_origin_country_id and move.product_id.intrastat_origin_country_id.code)
                }
                custom_items.append(data)
            if custom_items:
                request_data.update({
                    'internationalOptions': {
                        'contents': 'merchandise',
                        'customsItems': custom_items
                    }
                })
        return request_data

    @api.model
    def shipstation_send_shipping(self, pickings):
        for picking in pickings:
            if any(move.product_id.weight <= 0.0 for move in picking.move_ids):
                raise ValidationError("Need to set Product Weight.")
            if not picking.shipstation_order_id:
                body = self.create_or_update_order(picking)
                try:
                    response_data = self.api_calling_function("/orders/createorder", body)
                except Exception as error:
                    raise ValidationError(error)
                if response_data.status_code == 200:
                    responses = response_data.json()
                    _logger.info("Response Data: %s" % (responses))
                    order_id = responses.get('orderId')
                    order_key = responses.get('orderKey')
                    order_number = responses.get('orderNumber')
                    if order_id:
                        picking.write({'shipstation_order_id': order_id, 'shipstation_order_key': order_key,
                                       'shipstation_sale_order_number': order_number,
                                       'carrier_price': responses.get('shipmentCost', 0.0),
                                       'shipstation_configuration_id': self.shipstation_configuration_id.id})
                        if not (picking and picking.sale_id and picking.sale_id.shipstation_order_number):
                            picking.sale_id.shipstation_order_number = order_number
                            picking.sale_id.shipstation_order_id = order_id
                            picking.sale_id.shipstation_configuration_id = self.shipstation_configuration_id.id
                            picking.sale_id.is_exported_to_shipstation = True
                            picking.sale_id.shipstation_store_id = picking.carrier_id and picking.carrier_id.store_id.id
                    return [{'exact_price': 0.0, 'tracking_number': ''}]
                else:
                    error_code = "%s" % (response_data.status_code)
                    error_message = response_data.reason
                    error_detail = {'error': error_code + " - " + error_message + " - "}
                    # if response_data.json():
                    #     error_detail = {'error': error_code + " - " + error_message + " - %s" % (response_data.json())}
                    raise ValidationError("{}".format(error_detail))
            else:
                return [{'exact_price': 0.0, 'tracking_number': ''}]

    def shipstation_cancel_shipment(self, picking):
        shipment_id = picking.shipstation_shipment_id
        if not shipment_id:
            raise ValidationError("Shipstation Shipment Id Not Available!")
        req_data = {"shipmentId": '{}'.format(shipment_id)}
        try:
            response_data = self.api_calling_function("/shipments/voidlabel", req_data)
            if response_data.status_code == 200:
                responses = response_data.json()
                _logger.info("Response Data: %s" % (responses))
                approved = responses.get('approved')
                if approved:
                    picking.message_post(body=_('Shipment Cancelled In Shipstation %s' % (shipment_id)))
            else:
                error_code = "%s" % (response_data.status_code)
                error_message = response_data.reason
                error_detail = {'error': error_code + " - " + error_message + " - "}
                if response_data.json():
                    error_detail = {'error': error_code + " - " + error_message + " - %s" % (response_data.json())}
                raise ValidationError(error_detail)
        except Exception as e:
            raise ValidationError(e)
        return True

    def shipstation_get_tracking_link(self, pickings):
        res = ""
        for picking in pickings:
            if picking.shipstation_carrier_code:
                shipstation_carrier_id = self.env['shipstation.delivery.carrier'].search([('code','=',picking.shipstation_carrier_code)],limit=1)
                link = "%s" % (
                        shipstation_carrier_id.provider_tracking_link)
            else:
                shipstation_carrier_id = self.shipstation_carrier_id
                link = "%s" % (
                        picking.carrier_id and picking.carrier_id.shipstation_carrier_id and picking.carrier_id and picking.carrier_id.shipstation_carrier_id.provider_tracking_link)
            if not link:
                raise ValidationError("Provider Link Is not available")
            if len(pickings.carrier_tracking_ref.split(',')) > 1:
                if shipstation_carrier_id and shipstation_carrier_id.code in ["ups", "UPS", "ups_walleted",
                                                                                        "UPS_WALLETED"]:
                    res = '%s %s' % (link, pickings.carrier_tracking_ref.replace(",", "%20"))
                elif shipstation_carrier_id and shipstation_carrier_id.code in ["stamps_com", "STAMPS_COM"]:
                    res = '%s %s' % (link, pickings.carrier_tracking_ref.replace(",", "%2C"))
                else:
                    res = '%s %s' % (link, pickings.carrier_tracking_ref.replace(",", "&"))
            else:
                res = '%s %s' % (link, pickings.carrier_tracking_ref)

        return res
