"""
Emipro Technologies Private Limited
Author :Ravi Kotadiya | ravik@emiprotechnologies.com
Date : Oct-26-2021
"""

import json
from unittest.mock import patch

import requests
from odoo.modules.module import get_module_resource

from .common import TestShipStationCommon


class TestExportOrder(TestShipStationCommon):
    """

    """

    def setUp(self):
        super(TestExportOrder, self).setUp()
        self.shipstation_product = self.env['shipstation.product.ept'].create({
            'name': "ShipStation Product",
            'product_id': self.product.id,
            'shipstation_identification': 1234,
            'shipstation_sku': "PRD",
            'shipstation_instance_id': self.instance.id
        })

    def test_export_order(self):
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

        def _mock_get_response_export_order(*_args, **_kwargs):
            data = open(get_module_resource("shipstation_ept", "tests",
                                            "responses/export_order.json"), mode="rt").read()
            response = requests.Response()
            response.status_code = 200
            return json.loads(data), response

        with patch("odoo.addons.shipstation_ept.models.shipstation_instance_ept.ShipstationInstanceEpt.get_connection",
                   new=_mock_get_response_export_order):
            picking.export_order_to_shipstation()
        self.assertEqual(picking.ept_shipstation_order_id, 32487896, "Picking has no order id after "
                                                                 "export_order_to_shipstation.")
        self.assertTrue(picking.is_exported_to_shipstation, "Picking is not marked Exported after "
                                                            "export_order_to_shipstation.")

    def test_validate_unexported_order(self):
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
        picking.export_order = True
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty

        picking.button_validate()

        self.assertEqual(picking.state, "assigned", "Picking State is not assigned after validate if not "
                                                    "exported to ShipStation.")
