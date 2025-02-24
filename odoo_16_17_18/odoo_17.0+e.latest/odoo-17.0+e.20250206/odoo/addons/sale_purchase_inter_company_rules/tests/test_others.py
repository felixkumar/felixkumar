from .common import TestInterCompanyRulesCommonSOPO
from odoo.tests import tagged
from odoo.tests.common import Form


@tagged('-at_install', 'post_install')
class TestInterCompanyOthers(TestInterCompanyRulesCommonSOPO):

    def test_00_auto_purchase_on_normal_sales_order(self):
        partner1 = self.env['res.partner'].create({'name': 'customer', 'email': 'from.customer@example.com'})
        my_service = self.env['product.product'].create({
            'name': 'my service',
            'type': 'service',
            'service_to_purchase': True,
            'seller_ids': [(0, 0, {
                'partner_id': self.company_a.partner_id.id,
                'min_qty': 1,
                'price': 10,
                'product_code': 'C01',
                'product_name': 'Name01',
                'sequence': 1,
            })]
        })
        so = self.env['sale.order'].create({
            'partner_id': partner1.id,
            'order_line': [
                (0, 0, {
                    'name': my_service.name,
                    'product_id': my_service.id,
                    'product_uom_qty': 1,
                })
            ],
        })
        # confirming the action from the test will use Odoobot which results in the same flow as
        # confirming the SO from an email link
        so.action_confirm()

        po = self.env['purchase.order'].search([('partner_id', '=', self.company_a.partner_id.id)], order='id desc',
                                               limit=1)
        self.assertEqual(po.order_line.name, "[C01] Name01")

    def test_return_purchase_on_inter_company(self):
        """
        Check that returning the reciept of an inter-company transit
        updates the received quantity correctly.
        """
        inter_company_transit_location = self.env.ref('stock.stock_location_inter_wh')
        inter_company_transit_location.write({
            'active': True,
            'return_location': True,
        })
        super_product = self.env['product.product'].create({
            'name': 'Super Product',
            'type': 'product',
            'company_id': False,
        })
        purchase_order = Form(self.env['purchase.order'].with_company(self.company_a))
        purchase_order.partner_id = self.company_b.partner_id
        purchase_order.company_id = self.company_a
        purchase_order = purchase_order.save()

        with Form(purchase_order.with_company(self.company_b)) as po:
            with po.order_line.new() as line:
                line.product_id = super_product
                line.product_qty = 10.0

        # Confirm Purchase order
        purchase_order.with_company(self.company_a).button_confirm()
        receipt = purchase_order.picking_ids
        self.assertRecordValues(receipt.move_ids, [{
            'product_id': super_product.id,
            'product_uom_qty': 10.0,
        }])
        # validate the receipt
        receipt.move_ids.quantity = 10.0
        receipt.move_ids.picked = True
        receipt.with_company(self.company_a).button_validate()
        self.assertEqual(receipt.state, 'done')
        self.assertEqual(purchase_order.order_line.qty_received, 10.0)
        # return the units to the inter company transit location
        self.env.user.groups_id |= self.env.ref('stock.group_stock_multi_locations')
        stock_return_picking_form = Form(self.env['stock.return.picking'].with_company(self.company_a).with_context(active_ids=receipt.ids, active_id=receipt.sorted().ids[0], active_model='stock.picking'))
        stock_return_picking_form.location_id = inter_company_transit_location
        return_wiz = stock_return_picking_form.save()
        res = return_wiz.create_returns()
        pick_return = self.env['stock.picking'].browse(res['res_id'])
        pick_return.move_ids.quantity = 10.0
        pick_return.move_ids.picked = True
        pick_return.with_company(self.company_a).button_validate()
        self.assertEqual(pick_return.state, 'done')
        self.assertEqual(purchase_order.order_line.qty_received, 0.0)
