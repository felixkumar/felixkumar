import base64
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
from requests import request

_logger = logging.getLogger(__name__)


class ShipstationOdooIntegationConfig(models.Model):
    _name = "shipstation.odoo.configuration.vts"
    _description = 'Shipstation Configuration'

    api_key = fields.Char(string='API Key', help='Use Your Shipstation API Key.')
    api_secret = fields.Char(string='API Secret', help='Use Your Shipstation Password as API Secret.')
    api_url = fields.Char(string='URL', default="https://ssapi.shipstation.com")
    name = fields.Char(string='Name')
    message = fields.Char(string='Message')

    def create_shipstation_operation_details(self, operation_id, shipstation_response_message, fault_operaion=False):
        shipstation_operation_details = self.env['shipstation.operation.details']
        shipstation_operation_details.create({
            'operation_id': operation_id and operation_id.id,
            'shipstation_response_message': shipstation_response_message,
            'fault_operaion': fault_operaion,
            'shipstation_operation': 'warehouse'
        })

    def action_get_shipstation_stores(self):
        action = self.env.ref('shipstation_shipping_odoo_integration.actionid_shipstation_store_vts').read()[0]
        return action

    def action_action_get_shipstation_providers(self):
        action = self.env.ref('shipstation_shipping_odoo_integration.actionid_shipstation_delivery_carrier_vts').read()[
            0]
        return action

    def action_get_shipstation_services(self):
        action = \
            self.env.ref(
                'shipstation_shipping_odoo_integration.actionid_shipstation_delivery_carrier_service_vts').read()[
                0]
        return action

    def action_get_shipstation_packages(self):
        action = self.env.ref('shipstation_shipping_odoo_integration.actionid_shipstation_delivery_package_vts').read()[
            0]
        return action

    def api_calling_function(self, url):
        data = "%s:%s" % (self.api_key, self.api_secret)
        encode_data = base64.b64encode(data.encode("utf-8"))
        authrization_data = "Basic %s" % (encode_data.decode("utf-8"))
        headers = {"Authorization": "%s" % authrization_data, "Content-Type": "application/json"}
        try:
            response_data = request(method='GET', url=url, headers=headers)
            return response_data
        except Exception as e:
            raise ValidationError(e)

    def making_shipstation_url(self, api_name):
        if self.api_url:
            url = self.api_url + api_name
            return url
        else:
            raise ValidationError(_("URL is not appropriate."))

    def import_store_from_shipstation(self):
        self.store_create_process()
        self.carrier_create_process()
        self.delivery_carrier_service_process()
        self.delivery_carrier_package_process()
        self.import_warehouse_from_shipstation()
        self.message = "Shipstation Import Process Completed Sucessfully.."
        self._cr.commit()
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Import Shipstation Data Successfully!',
                'img_url': '/web/static/img/smile.svg',
                'type': 'rainbow_man',
            }
        }

    def delivery_carrier_package_process(self):
        carrier_name = self.env['shipstation.delivery.carrier'].search([])
        for carrier in carrier_name:
            url = self.making_shipstation_url("/carriers/listpackages?carrierCode=%s" % (carrier.code))
            response = self.api_calling_function(url)
            if response.status_code != 200:
                error = "Error Code : %s - %s" % (response.status_code, response.reason)
            shipstation_operation_detail = self.env['shipstation.operation.detail']
            shipstation_operation_details = self.env['shipstation.operation.details']
            shipstation_delivery_carrier_package = self.env['shipstation.delivery.package']
            operation = False
            if not operation:
                operation_id = shipstation_operation_detail.create({
                    'shipstation_operation': 'carrier_package', 'shipstation_operation_type': 'import',
                    'message': 'Delivery Carrier Package Imported',
                })
            try:
                responses = response.json()
                for response in responses:
                    shipstation_delivery_carrier_package = shipstation_delivery_carrier_package.search(
                        [('package_code', '=', response.get('code')), ('delivery_carrier_id', '=', carrier.id),
                         ('shipstation_configuration_id', '=', self.id)])
                    if not shipstation_delivery_carrier_package:
                        carrier_id = self.env['shipstation.delivery.carrier'].search(
                            [('code', '=', response.get('carrierCode', False)),
                             ('shipstation_configuration_id', '=', self.id)])
                        shipstation_delivery_carrier_package.create({'name': response.get('name', False),
                                                                     'package_code': response.get('code', False),
                                                                     'shipstation_configuration_id': self.id,
                                                                     'service_nature': 'domestic' if response.get(
                                                                         'domestic', False) else 'international',
                                                                     'delivery_carrier_id': carrier_id.id,
                                                                     'supported_domestic': True if response.get(
                                                                         'domestic') else False,
                                                                     'supported_international': True if response.get(
                                                                         'international') else False
                                                                     })
                        shipstation_operation_details.create(
                            {'operation_id': operation_id.id,
                             'shipstation_response_message': "%s Delivery Carrier Service Created" % (
                                 response.get('name')), 'fault_operaion': False,
                             'shipstation_operation': 'carrier_package'})
                    else:
                        shipstation_delivery_carrier_package.write({'shipstation_configuration_id': self.id})
                        shipstation_operation_details.create(
                            {'operation_id': operation_id.id,
                             'shipstation_response_message': "%s Delivery Carrier Service already exist" % (
                                 response.get('name')),
                             'fault_operaion': True,
                             'shipstation_operation': 'carrier_package'})
            except Exception as e:
                shipstation_operation_details.create(
                    {'operation_id': operation_id.id, 'shipstation_response_message': e, 'fault_operaion': True,
                     'shipstation_operation': 'carrier_service'})

    def delivery_carrier_service_process(self):
        carrier_name = self.env['shipstation.delivery.carrier'].search([('shipstation_configuration_id', '=', self.id)])
        shipstation_delivery_carrier_service = self.env['shipstation.delivery.carrier.service']
        shipstation_operation_detail = self.env['shipstation.operation.detail']
        shipstation_operation_details = self.env['shipstation.operation.details']
        for carrier in carrier_name:
            operation = False
            if not operation:
                operation_id = shipstation_operation_detail.create({
                    'shipstation_operation': 'carrier_service', 'shipstation_operation_type': 'import',
                    'message': 'Delivery Carrier Service Imported',
                })
            url = self.making_shipstation_url("/carriers/listservices?carrierCode=%s" % (carrier.code))
            response = self.api_calling_function(url)
            if response.status_code != 200:
                error = "Error Code : %s - %s" % (response.status_code, response.reason)
                responses = response.json()
                shipstation_operation_details.create(
                    {'operation_id': operation_id.id,
                     'shipstation_response_message': responses.get('message'), 'fault_operaion': True,
                     'shipstation_operation': 'carrier_service'})
                continue
            try:
                responses = response.json()
                for response in responses:
                    shipstation_delivery_carrier_service = shipstation_delivery_carrier_service.search(
                        [('name', '=', response.get('name', False)), ('shipstation_configuration_id', '=', self.id)])
                    if not shipstation_delivery_carrier_service:
                        carrier_id = self.env['shipstation.delivery.carrier'].search(
                            [('code', '=', response.get('carrierCode', False)),
                             ('shipstation_configuration_id', '=', self.id)])
                        shipstation_delivery_carrier_service.create({'name': response.get('name', False),
                                                                     'service_code': response.get('code', False),
                                                                     'shipstation_configuration_id': self.id,
                                                                     'service_nature': 'domestic' if response.get(
                                                                         'domestic', False) else 'international',
                                                                     'delivery_carrier_id': carrier_id.id,
                                                                     'supported_domestic': True if response.get(
                                                                         'domestic') else False,
                                                                     'supported_international': True if response.get(
                                                                         'international') else False
                                                                     })
                        shipstation_operation_details.create(
                            {'operation_id': operation_id.id,
                             'shipstation_response_message': "%s Delivery Carrier Service Created" % (
                                 response.get('name')), 'fault_operaion': False,
                             'shipstation_operation': 'carrier_service'})
                    else:
                        shipstation_delivery_carrier_service.write({'shipstation_configuration_id': self.id})
                        shipstation_operation_details.create(
                            {'operation_id': operation_id.id,
                             'shipstation_response_message': "%s Delivery Carrier Service already exist" % (
                                 response.get('name')),
                             'fault_operaion': True,
                             'shipstation_operation': 'carrier_service'})
            except Exception as e:
                shipstation_operation_details.create(
                    {'operation_id': operation_id.id, 'shipstation_response_message': e, 'fault_operaion': True,
                     'shipstation_operation': 'carrier_service'})

    def carrier_create_process(self):
        url = self.making_shipstation_url("/carriers")
        response = self.api_calling_function(url)
        if response.status_code != 200:
            error = "Error Code : %s - %s" % (response.status_code, response.reason)
        shipstation_operation_detail = self.env['shipstation.operation.detail']
        shipstation_operation_details = self.env['shipstation.operation.details']
        shipstation_delivery_carrier = self.env['shipstation.delivery.carrier']
        operation = False
        if not operation:
            operation_id = shipstation_operation_detail.create(
                {'shipstation_operation': 'delivery_carrier', 'shipstation_operation_type': 'import',
                 'message': 'Delivery Carrier Imported',
                 })
        try:
            responses = response.json()
            for response in responses:
                delivery_carrier = shipstation_delivery_carrier.search(
                    [('code', '=', response.get('code', False)), ('shipstation_configuration_id', '=', self.id)])
                if not delivery_carrier:
                    shipstation_delivery_carrier.create({'name': response.get('name', False),
                                                         'shipstation_configuration_id': self.id,
                                                         'code': response.get('code', False),
                                                         'account_number': response.get('accountNumber', False),
                                                         'shipping_provider_id': response.get('shippingProviderId',
                                                                                              False)
                                                         })
                    shipstation_operation_details.create(
                        {'operation_id': operation_id.id,
                         'shipstation_response_message': "%s Delivery Carrier Created" % (response.get('name')),
                         'fault_operaion': False,
                         'shipstation_operation': 'delivery_carrier'})
                else:
                    shipstation_delivery_carrier.write({'shipstation_configuration_id': self.id})
                    shipstation_operation_details.create(
                        {'operation_id': operation_id.id,
                         'shipstation_response_message': "%s Delivery Carrier already exist" % (response.get('name')),
                         'fault_operaion': True,
                         'shipstation_operation': 'delivery_carrier'})
        except Exception as e:
            shipstation_operation_details.create(
                {'operation_id': operation_id.id, 'shipstation_response_message': e, 'fault_operaion': True,
                 'shipstation_operation': 'delivery_carrier'})

    def store_create_process(self):
        url = self.making_shipstation_url("/stores?stores?showInactive=false")
        response = self.api_calling_function(url)
        if response.status_code != 200:
            raise ValidationError("Error Code : %s - %s" % (response.status_code, response.reason))
        shipstation_operation_detail = self.env['shipstation.operation.detail']
        shipstation_operation_details = self.env['shipstation.operation.details']
        shipstation_store = self.env['shipstation.store.vts']
        operation = False
        if not operation:
            operation_id = shipstation_operation_detail.create(
                {'shipstation_operation': 'store', 'shipstation_operation_type': 'import', 'message': 'Store Imported',
                 })
        try:
            responses = response.json()
            for response in responses:
                store = shipstation_store.search(
                    [('store_id', '=', response.get('storeId', False)), ('shipstation_configuration_id', '=', self.id)])
                if not store:
                    shipstation_store.create({'store_id': response.get('storeId', False),
                                              'store_name': response.get('storeName', False),
                                              'marketplace_id': response.get('marketplaceId', False),
                                              'marketplace_name': response.get('marketplaceName', False),
                                              'shipstation_configuration_id': self.id,
                                              'acc_number': response.get('accountName', False)})
                    shipstation_operation_details.create(
                        {'operation_id': operation_id.id,
                         'shipstation_response_message': "%s Store Created" % (response.get('storeName')),
                         'fault_operaion': False,
                         'shipstation_operation': 'store'})
                else:
                    shipstation_store.write({'shipstation_configuration_id': self.id})
                    shipstation_operation_details.create(
                        {'operation_id': operation_id.id,
                         'shipstation_response_message': "%s Store already exist" % (response.get('storeName')),
                         'fault_operaion': True,
                         'shipstation_operation': 'store'})
        except Exception as e:
            shipstation_operation_details.create(
                {'operation_id': operation_id.id, 'shipstation_response_message': e, 'fault_operaion': True,
                 'shipstation_operation': 'store'})

    def import_warehouse_from_shipstation(self):
        self.ensure_one()
        # vals = {}
        shipstation_operation_detail = self.env['shipstation.operation.detail']
        # shipstation_operation_details = self.env['shipstation.operation.details']
        operation_id = shipstation_operation_detail.create({
            'shipstation_operation': 'warehouse', 'shipstation_operation_type': 'import',
            'message': 'Warehouse Import Process',
        })
        try:
            url = self.making_shipstation_url('/warehouses')
            response_data = self.api_calling_function(url)
            if response_data.status_code != 200:
                raise ValidationError("Error Code : %s - %s" % (response_data.status_code, response_data.reason))
            if response_data.status_code == 200:
                responses = response_data.json()
                for warehouse in responses:
                    sh_warehouse = self.env['shipstation.warehouse.detail'].search(
                        [('warehouse_id', '=', warehouse.get('warehouseId')),
                         ('shipstation_configuration_id', '=', self.id)])
                    if not sh_warehouse:
                        warehouse = self.env['shipstation.warehouse.detail'].create(
                            {'name': warehouse.get('warehouseName'), 'shipstation_configuration_id': self.id,
                             'warehouse_id': warehouse.get('warehouseId')})
                        if warehouse:
                            response_msg = "Warehouse Created Updated : {0}".format(warehouse.name)
                            self.create_shipstation_operation_details(operation_id, response_msg, False)
                    else:
                        sh_warehouse.write({'shipstation_configuration_id': self.id})
        except Exception as e:
            response_msg = "%s Warehouse Not Imported %s" % (self.name, e)
            self.create_shipstation_operation_details(operation_id, response_msg, True)
