"""
Emipro Technologies Private Limited
Author : Ravi Kotadiya | ravik@emiprotechnologies.com
Date : Oct-26-2021
"""

import json
from unittest.mock import patch

import requests
from odoo.modules.module import get_module_resource

from .common import TestShipStationCommon


class TestGetRates(TestShipStationCommon):
    """

    """

    def setUp(self):
        super(TestGetRates, self).setUp()
        self.shipstation_product = self.env['shipstation.product.ept'].create({
            'name': "ShipStation Product",
            'product_id': self.product.id,
            'shipstation_identification': 1234,
            'shipstation_sku': "PRD",
            'shipstation_instance_id': self.instance.id
        })

    def test_get_rates(self):
        self.order = self.env['sale.order'].create({
            'partner_id': self.customer_1.id,
            'team_id': self.sales_team.id,
            'order_line': [
                (0, False, {
                    'product_id': self.product.id,
                    'name': '10 Product A',
                    'product_uom': self.uom_unit.id,
                    'product_uom_qty': 1.0,
                })
            ]
        })
        self.order.action_confirm()
        picking = self.order.picking_ids[0]

        def _mock_get_response_get_rates(*_args, **_kwargs):
            data = open(get_module_resource("shipstation_ept", "tests",
                                            "responses/get_rates.json"), mode="rt").read()
            response = requests.Response()
            response.status_code = 200
            return json.loads(data), response

        with patch("odoo.addons.shipstation_ept.models.shipstation_instance_ept.ShipstationInstanceEpt.get_connection",
                   new=_mock_get_response_get_rates):
            picking.get_rates()

        self.assertTrue(picking.delivery_rate_ids, "No rates lines created for picking.")
