"""
Emipro Technologies Private Limited
Author : Ravi Kotadiya | ravik@emiprotechnologies.com
Date : Oct-26-2021
"""

import json
from unittest.mock import patch

import requests
from odoo.modules.module import get_module_resource
from odoo.tests.common import HttpCase

CONNECTION_PATH = "odoo.addons.shipstation_ept.models.shipstation_instance_ept.ShipstationInstanceEpt.get_connection"

class TestShipStationCommon(HttpCase):

    def setUp(self):
        super(TestShipStationCommon, self).setUp()

        self.instance = self.env["shipstation.instance.ept"].create({
            "name": "ShipStation Test Instance",
            "provider": "shipstation_ept",
            "shipstation_api_key": "4854007c555346c08640a8a9f9ca7f82",
            "shipstation_api_secret_key": "4394b105d9344df4adf6932bd08bd5c9",
            "company_id": self.env.company.id
        })

        def _mock_get_response_stores(*_args, **_kwargs):
            data = open(get_module_resource("shipstation_ept", "tests",
                                            "responses/stores.json"), mode="rt").read()
            response = requests.Response()
            response.status_code = 200
            return json.loads(data), response

        with patch(CONNECTION_PATH,
                   new=_mock_get_response_stores):
            self.instance.get_shipstation_stores()

        def _mock_get_response_carriers(*_args, **_kwargs):
            data = open(get_module_resource("shipstation_ept", "tests",
                                            "responses/carriers.json"), mode="rt").read()
            response = requests.Response()
            response.status_code = 200
            return json.loads(data), response

        with patch(CONNECTION_PATH, new=_mock_get_response_carriers):
            self.instance.get_shipstation_carriers()

        def _mock_get_response_packages(*_args, **_kwargs):
            data = open(get_module_resource("shipstation_ept", "tests",
                                            "responses/packages.json"), mode="rt").read()
            response = requests.Response()
            response.status_code = 200
            return json.loads(data), response

        with patch(CONNECTION_PATH, new=_mock_get_response_packages):
            self.instance.get_shipstation_packages()

        def _mock_get_response_services(*_args, **_kwargs):
            data = open(get_module_resource("shipstation_ept", "tests",
                                            "responses/services.json"), mode="rt").read()
            response = requests.Response()
            response.status_code = 200
            return json.loads(data), response

        with patch(CONNECTION_PATH, new=_mock_get_response_services):
            self.instance.get_shipstation_services()

        def _mock_get_response_warehouses(*_args, **_kwargs):
            data = open(get_module_resource("shipstation_ept", "tests",
                                            "responses/warehouses.json"), mode="rt").read()
            response = requests.Response()
            response.status_code = 200
            return json.loads(data), response

        with patch(CONNECTION_PATH, new=_mock_get_response_warehouses):
            self.instance.get_shipstation_warehouses()

        product_id = self.env['product.product'].search([('default_code', '=', 'SHIP_SHIPSTATION'),
                                                         ('company_id', '=', self.env.company.id)])
        if not product_id:
            product_id = self.env['product.product'].create({'name': 'Shipstation Shipping and Handling',
                                                             'type': 'service',
                                                             'default_code': 'SHIP_SHIPSTATION',
                                                             'list_price': 0.0,
                                                             'standard_price': 0.0,
                                                             'company_id': self.env.company.id
                                                             })

        self.test_carrier = self.env['delivery.carrier'].create({
            'name': "test carrier ShipStation",
            'integration_level': "rate_and_ship",
            'product_id': product_id.id,
            'delivery_type': "shipstation_ept",
            'shipstation_instance_id': self.instance.id,
            'shipstation_weight_uom_id': self.env['uom.uom'].search([('name', '=', 'g')], limit=1).id,
            'ept_shipstation_carrier_id': self.env['shipstation.carrier.ept'].search(
                [('shipstation_instance_id', '=', self.instance.id)], limit=1).id,
            'shipstation_service_id': self.env['shipstation.services.ept'].search(
                [('shipstation_instance_id', '=', self.instance.id)], limit=1).id,
            'shipstation_package_id': self.env['stock.package.type'].search(
                [('shipstation_instance_id', '=', self.instance.id)], limit=1).id,
            'shipstation_weight_uom': "grams",
            'package_unit_default': "inches"
        })
        self.store_id = self.env['shipstation.store.ept'].search([('shipstation_instance_id', '=', self.instance.id)],
                                                                 limit=1)
        self.sales_team = self.env["crm.team"].create({
            "name": "test sales team",
            "store_id": self.store_id.id,
            "delivery_carrier_id": self.test_carrier.id
        })
        self.customer_1 = self.env['res.partner'].create({
            'name': "customer1",
            'is_company': 0,
            'street': "street-1, near MG road",
            'street2': "street-1",
            'city': "city1",
            'state_id': self.env.ref('base.state_us_5').id,
            'zip': 54616,
            'country_id': self.env.ref('base.us').id,
            'email': "customer1@gmail.com",
        })
        self.uom_unit = self.env.ref('uom.product_uom_kgm')
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
            'default_code': "PRD",
            'uom_id': self.uom_unit.id,
            'uom_po_id': self.uom_unit.id,
            'weight': 1,
        })
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': self.stock_location.id,
            'quantity': 20.0,
        })
