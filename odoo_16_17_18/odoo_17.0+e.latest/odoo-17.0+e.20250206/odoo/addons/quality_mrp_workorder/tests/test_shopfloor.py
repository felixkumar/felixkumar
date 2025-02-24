# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import Command

from odoo.tests import Form
from odoo.tests.common import tagged
from odoo.addons.quality_control.tests.test_common import TestQualityCommon
from odoo.addons.mrp_workorder.tests.test_shopfloor import TestShopFloor

@tagged('post_install', '-at_install')
class TestShopFloorQuality(TestShopFloor, TestQualityCommon):
    def test_register_sn_production_quality_check(self):
        warehouse = self.env.ref("stock.warehouse0")
        final_product, component = self.env['product.product'].create([
            {
                'name': 'Lovely Product',
                'type': 'product',
                'tracking': 'serial',
            },
            {
                'name': 'Lovely Component',
                'type': 'product',
                'tracking': 'none',
            },
        ])
        self.env['stock.quant']._update_available_quantity(component, warehouse.lot_stock_id, quantity=10)
        workcenter = self.env['mrp.workcenter'].create({
            'name': 'Lovely Workcenter',
        })
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': final_product.product_tmpl_id.id,
            'product_qty': 1.0,
            'operation_ids': [
                Command.create({'name': 'Lovely Operation', 'workcenter_id': workcenter.id}),
            ],
            'bom_line_ids': [
                Command.create({'product_id': component.id, 'product_qty': 1.0}),
            ]
        })
        self.env['quality.point'].create([
            {
                'picking_type_ids': [Command.link(warehouse.manu_type_id.id)],
                'operation_id': bom.operation_ids.id,
                'title': 'Lovely Production Registering',
                'test_type_id': self.ref('mrp_workorder.test_type_register_production'),
                'sequence': 1,
            },
        ])
        mo = self.env['mrp.production'].create({
            'product_id': final_product.id,
            'product_qty': 1,
            'bom_id': bom.id,
        })
        mo.action_confirm()
        mo.action_assign()
        self.assertEqual(mo.reservation_state, 'assigned')
        mo.button_plan()
        action = mo.workorder_ids.action_open_mes()
        url = '/web?#action=%s' % (action['id'])
        self.start_tour(url, "test_register_sn_production_quality_check", login='admin')
        self.assertRecordValues(mo.lot_producing_id, [{'name': 'SN0012'}])
