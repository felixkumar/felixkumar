"""
Emipro Technologies Private Limited
Author : Ravi Kotadiya | ravik@emiprotechnologies.com
Date :
"""

from .common import TestShipStationCommon


class TestSaleOrderCreation(TestShipStationCommon):
    """
        Tests for Sale order creation with sales team.
    """

    def setUp(self):
        """
        Setup method for tests.
        """
        super(TestSaleOrderCreation, self).setUp()

    def test_sale_order_creation(self):
        """
        Sale order creation with sales team having shipStation store and default carrier.
        """
        self.order = self.env['sale.order'].create({
            'partner_id': self.customer_1.id,
            'team_id': self.sales_team.id
        })
        self.assertEqual(self.order.ept_shipstation_store_id.id, self.store_id.id,
                         "ShipStation store is not set as per config in sale order")
        self.assertEqual(self.order.ept_shipstation_store_id.shipstation_instance_id.id, self.instance.id,
                         "ShipStation instance is not set as per config in sale order")
        self.assertEqual(self.order.carrier_id.id, self.test_carrier.id,
                         "Carrier is not set as per config in sale order")

    def test_sale_order_confirm(self):
        """
        Sale order confirmation with ShipStation details set in order.
        @return:
        """
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
        self.assertTrue(picking.shipstation_instance_id, "ShipStation Instance not set in Delivery Order.")
        self.assertTrue(picking.shipstation_service_id, "ShipStation Service not set in Delivery Order.")
        self.assertTrue(picking.shipstation_package_id, "ShipStation Package not set in Delivery Order.")
        self.assertTrue(picking.ept_shipstation_store_id, "ShipStation Store not set in Delivery Order.")
