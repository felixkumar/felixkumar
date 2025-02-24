"""
Emipro Technologies Private Limited
Ravi Kotadiya | ravik@emiprotechnologies.com
Date : Oct-26-2021
"""

import json
from unittest.mock import patch

import requests
from odoo.modules.module import get_module_resource

from .common import TestShipStationCommon


class TestGenerateLabel(TestShipStationCommon):
    """

    """

    def setUp(self):
        super(TestGenerateLabel, self).setUp()

    def test_generate_label(self):
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
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty

        def _mock_get_response_label(*_args, **_kwargs):
            data = open(get_module_resource("shipstation_ept", "tests",
                                            "responses/label.json"), mode="rt").read()
            response = requests.Response()
            response.status_code = 200
            return json.loads(data), response

        with patch("odoo.addons.shipstation_ept.models.shipstation_instance_ept.ShipstationInstanceEpt.get_connection",
                   new=_mock_get_response_label):
            picking.button_validate()

        self.assertEqual(picking.carrier_tracking_ref, "99999999999999999999", "Tracking number is not set in picking.")
        self.assertEqual(picking.ept_shipstation_shipment_id, -1, "Shipment ID is not set in picking.")
        self.assertEqual(picking.state, "done", "Picking is not marked done after label generation.")
