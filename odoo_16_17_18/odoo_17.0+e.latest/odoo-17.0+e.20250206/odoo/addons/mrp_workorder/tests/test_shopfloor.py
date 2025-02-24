# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import Command

from odoo.tests import Form
from odoo.tests.common import HttpCase, tagged

@tagged('post_install', '-at_install')
class TestShopFloor(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['res.config.settings'].create({
            'group_mrp_routings': True
        }).execute()

    def test_shop_floor(self):
        self.env['hr.employee'].create({
            'name': 'Marc Demo'
        })
        giraffe = self.env['product.product'].create({
            'name': 'Giraffe',
            'type': 'product',
            'tracking': 'lot',
        })
        leg = self.env['product.product'].create({
            'name': 'Leg',
            'type': 'product',
        })
        neck = self.env['product.product'].create({
            'name': 'Neck',
            'type': 'product',
            'tracking': 'serial',
        })
        color = self.env['product.product'].create({
            'name': 'Color',
            'type': 'product',
        })
        neck_sn_1, neck_sn_2 = self.env['stock.lot'].create([{
            'name': 'NE1',
            'product_id': neck.id,
        }, {
            'name': 'NE2',
            'product_id': neck.id,
        }])
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        stock_location = warehouse.lot_stock_id
        self.env['stock.quant']._update_available_quantity(leg, stock_location, quantity=100)
        self.env['stock.quant']._update_available_quantity(color, stock_location, quantity=100)
        self.env['stock.quant']._update_available_quantity(neck, stock_location, quantity=1, lot_id=neck_sn_1)
        self.env['stock.quant']._update_available_quantity(neck, stock_location, quantity=1, lot_id=neck_sn_2)
        savannah = self.env['mrp.workcenter'].create({
            'name': 'Savannah',
            'time_start': 10,
            'time_stop': 5,
            'time_efficiency': 80,
        })
        jungle = self.env['mrp.workcenter'].create({'name': 'Jungle'})
        picking_type = warehouse.manu_type_id
        bom = self.env['mrp.bom'].create({
            'product_id': giraffe.id,
            'product_tmpl_id': giraffe.product_tmpl_id.id,
            'product_uom_id': giraffe.uom_id.id,
            'product_qty': 1.0,
            'consumption': 'flexible',
            'operation_ids': [
                (0, 0, {
                'name': 'Creation',
                'workcenter_id': savannah.id,
            }), (0, 0, {
                'name': 'Release',
                'workcenter_id': jungle.id,
            })],
            'bom_line_ids': [
                (0, 0, {'product_id': leg.id, 'product_qty': 4}),
                (0, 0, {'product_id': neck.id, 'product_qty': 1})
            ]
        })
        steps_common_values = {
            'picking_type_ids': [(4, picking_type.id)],
            'product_ids': [(4, giraffe.id)],
            'operation_id': bom.operation_ids[0].id,
        }
        self.env['quality.point'].create([
            {
                **steps_common_values,
                'title': 'Register Production',
                'test_type_id': self.env.ref('mrp_workorder.test_type_register_production').id,
                'sequence': 0,
            },
            {
                **steps_common_values,
                'title': 'Instructions',
                'test_type_id': self.env.ref('quality.test_type_instructions').id,
                'sequence': 1,
            },
            {
                **steps_common_values,
                'title': 'Register legs',
                'component_id': leg.id,
                'test_type_id': self.env.ref('mrp_workorder.test_type_register_consumed_materials').id,
                'sequence': 2,
            },
            {
                **steps_common_values,
                'title': 'Register necks',
                'component_id': neck.id,
                'test_type_id': self.env.ref('mrp_workorder.test_type_register_consumed_materials').id,
                'sequence': 3,
            },
            {
                **steps_common_values,
                'title': 'Release',
                'test_type_id': self.env.ref('quality.test_type_instructions').id,
                'sequence': 4,
            },
        ])
        mo = self.env['mrp.production'].create({
            'product_id': giraffe.id,
            'product_qty': 2,
            'bom_id': bom.id,
        })
        mo.action_confirm()
        mo.action_assign()
        mo.button_plan()

        # Tour
        action = self.env["ir.actions.actions"]._for_xml_id("mrp_workorder.action_mrp_display")
        url = '/web?#action=%s' % (action['id'])
        self.start_tour(url, "test_shop_floor", login='admin')

        self.assertEqual(mo.move_finished_ids.quantity, 2)
        self.assertRecordValues(mo.move_raw_ids, [
            {'product_id': leg.id, 'quantity': 10, 'state': 'done'},
            {'product_id': neck.id, 'quantity': 2, 'state': 'done'},
            {'product_id': color.id, 'quantity': 1, 'state': 'done'},
        ])
        self.assertRecordValues(mo.workorder_ids, [
            {'state': 'done', 'workcenter_id': savannah.id},
            {'state': 'done', 'workcenter_id': jungle.id},
        ])
        self.assertRecordValues(mo.workorder_ids[0].check_ids, [
            {'quality_state': 'pass', 'component_id': False, 'qty_done': 2, 'lot_id': mo.move_finished_ids.move_line_ids.lot_id.id},
            {'quality_state': 'pass', 'component_id': False, 'qty_done': 0, 'lot_id': 0},
            {'quality_state': 'pass', 'component_id': leg.id, 'qty_done': 8, 'lot_id': 0},
            {'quality_state': 'pass', 'component_id': leg.id, 'qty_done': 2, 'lot_id': 0},
            {'quality_state': 'pass', 'component_id': neck.id, 'qty_done': 1, 'lot_id': neck_sn_2.id},
            {'quality_state': 'pass', 'component_id': neck.id, 'qty_done': 1, 'lot_id': neck_sn_1.id},
            {'quality_state': 'pass', 'component_id': False, 'qty_done': 0, 'lot_id': 0},
        ])

    def test_shop_floor_my_wo_filter_with_pin_user(self):
        """Checks the shown Work Orders (in "My WO" section) are correctly
        refreshed when selected user uses a PIN code."""
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        stock_location = warehouse.lot_stock_id
        # Create two employees (one with no PIN code and one with a PIN code.)
        self.env['hr.employee'].create([
            {'name': 'John Snow'},
            {'name': 'Queen Elsa', 'pin': '41213'},
        ])
        # Create some products and add enough quantity in stock for the components.
        final_product, comp_1, comp_2 = self.env['product.product'].create([{
            'name': name,
            'type': 'product',
        } for name in ['Snowman', 'Snowball', 'Carrot']])
        self.env['stock.quant']._update_available_quantity(comp_1, stock_location, quantity=100)
        self.env['stock.quant']._update_available_quantity(comp_2, stock_location, quantity=100)
        # Configure all the needs to create a MO with at least one WO.
        workcenter = self.env['mrp.workcenter'].create({
            'name': 'Winter\'s Workshop',
            'time_start': 10,
            'time_stop': 5,
            'time_efficiency': 80,
        })
        bom = self.env['mrp.bom'].create({
            'product_id': final_product.id,
            'product_tmpl_id': final_product.product_tmpl_id.id,
            'product_uom_id': final_product.uom_id.id,
            'product_qty': 1.0,
            'consumption': 'flexible',
            'operation_ids': [
                Command.create({
                    'name': 'Build the Snowman',
                    'workcenter_id': workcenter.id,
                }),
            ],
            'bom_line_ids': [
                Command.create({'product_id': comp_1.id, 'product_qty': 3}),
                Command.create({'product_id': comp_2.id, 'product_qty': 1}),
            ]
        })
        # Create, confirm and plan two MO.
        mo_1 = self.env['mrp.production'].create({
            'product_id': final_product.id,
            'product_qty': 3,
            'bom_id': bom.id,
        })
        mo_2 = self.env['mrp.production'].create({
            'product_id': final_product.id,
            'product_qty': 5,
            'bom_id': bom.id,
        })
        all_mo = mo_1 + mo_2
        all_mo.action_confirm()
        all_mo.action_assign()
        all_mo.button_plan()
        # Change MO name for easier tracking in the tour.
        mo_1.name = 'TEST/00001'
        mo_2.name = 'TEST/00002'

        action = self.env["ir.actions.actions"]._for_xml_id("mrp_workorder.action_mrp_display")
        url = '/web?#action=%s' % (action['id'])
        self.start_tour(url, 'test_shop_floor_my_wo_filter_with_pin_user', login='admin')

    def test_generate_serials_in_shopfloor(self):
        component1 = self.env['product.product'].create({
            'name': 'comp1',
            'type': 'product',
        })
        component2 = self.env['product.product'].create({
            'name': 'comp2',
            'type': 'product',
        })
        finished = self.env['product.product'].create({
            'name': 'finish',
            'type': 'product',
        })
        byproduct = self.env['product.product'].create({
            'name': 'byprod',
            'type': 'product',
            'tracking': 'serial',
        })
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        stock_location = warehouse.lot_stock_id
        self.env['stock.quant']._update_available_quantity(component1, stock_location, quantity=100)
        self.env['stock.quant']._update_available_quantity(component2, stock_location, quantity=100)
        workcenter = self.env['mrp.workcenter'].create({
            'name': 'Assembly Line',
        })
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': finished.product_tmpl_id.id,
            'product_qty': 1.0,
            'operation_ids': [
                (0, 0, {'name': 'Assemble', 'workcenter_id': workcenter.id}),
            ],
            'bom_line_ids': [
                (0, 0, {'product_id': component1.id, 'product_qty': 1}),
                (0, 0, {'product_id': component2.id, 'product_qty': 1}),
            ],
            'byproduct_ids': [
                (0, 0, {'product_id': byproduct.id, 'product_qty': 1}),
            ]
        })
        bom.byproduct_ids[0].operation_id = bom.operation_ids[0].id
        mo = self.env['mrp.production'].create({
            'product_id': finished.id,
            'product_qty': 1,
            'bom_id': bom.id,
        })
        mo.action_confirm()
        mo.action_assign()
        mo.button_plan()

        action = self.env["ir.actions.actions"]._for_xml_id("mrp_workorder.action_mrp_display")
        url = '/web?#action=%s' % (action['id'])
        self.start_tour(url, "test_generate_serials_in_shopfloor", login='admin')

    def test_canceled_wo(self):
        finished = self.env['product.product'].create({
            'name': 'finish',
            'type': 'product',
        })
        workcenter = self.env['mrp.workcenter'].create({
            'name': 'Assembly Line',
        })
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': finished.product_tmpl_id.id,
            'product_qty': 1.0,
            'operation_ids': [
                (0, 0, {'name': 'op1', 'workcenter_id': workcenter.id}),
                (0, 0, {'name': 'op2', 'workcenter_id': workcenter.id}),
            ],
        })

        # Cancel previous MOs and create a new one
        self.env['mrp.production'].search([]).action_cancel()
        mo = self.env['mrp.production'].create({
            'product_id': finished.id,
            'product_qty': 2,
            'bom_id': bom.id,
        })
        mo.action_confirm()
        mo.action_assign()
        mo.button_plan()

        # wo_1 completely finished
        mo_form = Form(mo)
        mo_form.qty_producing = 2
        mo = mo_form.save()
        mo.workorder_ids[0].button_start()
        mo.workorder_ids[0].button_finish()

        # wo_2 partially finished
        mo_form.qty_producing = 1
        mo = mo_form.save()
        mo.workorder_ids[1].button_start()
        mo.workorder_ids[1].button_finish()

        # Create a backorder
        action = mo.button_mark_done()
        backorder = Form(self.env['mrp.production.backorder'].with_context(**action['context']))
        backorder.save().action_backorder()
        mo_backorder = mo.procurement_group_id.mrp_production_ids[-1]
        mo_backorder.button_plan()

        # Sanity check
        self.assertEqual(mo_backorder.workorder_ids[0].state, 'cancel')
        self.assertEqual(mo_backorder.workorder_ids[1].state, 'ready')

        action = self.env["ir.actions.actions"]._for_xml_id("mrp_workorder.action_mrp_display")
        url = '/web?#action=%s' % (action['id'])
        self.start_tour(url, "test_canceled_wo", login='admin')

    def test_quality_checks_updated_in_shop_floor(self):
        component1 = self.env['product.product'].create({
            'name': 'comp1',
            'type': 'product',
            'tracking': 'lot',
        })
        finished = self.env['product.product'].create({
            'name': 'finish',
            'type': 'product',
            'tracking': 'serial',
        })
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        stock_location = warehouse.lot_stock_id
        lot = self.env['stock.lot'].create([{'name': 'LOT', 'product_id': component1.id}])
        self.env['stock.quant']._update_available_quantity(component1, stock_location, quantity=100, lot_id=lot)
        workcenter = self.env['mrp.workcenter'].create({
            'name': 'Assembly Line',
        })
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': finished.product_tmpl_id.id,
            'product_qty': 1.0,
            'operation_ids': [
                (0, 0, {'name': 'Assemble', 'workcenter_id': workcenter.id}),
            ],
            'bom_line_ids': [
                (0, 0, {'product_id': component1.id, 'product_qty': 1}),
            ],
        })
        self.env['quality.point'].create([
            {
                'picking_type_ids': [(4, warehouse.manu_type_id.id)],
                'product_ids': [(4, finished.id)],
                'operation_id': bom.operation_ids[0].id,
                'title': 'Register Production',
                'test_type_id': self.env.ref('mrp_workorder.test_type_register_production').id,
                'sequence': 0,
            },
            {
                'picking_type_ids': [(4, warehouse.manu_type_id.id)],
                'product_ids': [(4, finished.id)],
                'operation_id': bom.operation_ids[0].id,
                'title': 'Register comp1',
                'component_id': component1.id,
                'test_type_id': self.env.ref('mrp_workorder.test_type_register_consumed_materials').id,
                'sequence': 1,
            },
        ])
        mo = self.env['mrp.production'].create({
            'product_id': finished.id,
            'product_qty': 3,
            'bom_id': bom.id,
        })
        mo.action_confirm()
        mo.action_assign()
        mo.button_plan()

        action = self.env["ir.actions.actions"]._for_xml_id("mrp_workorder.action_mrp_display")
        url = '/web?#action=%s' % (action['id'])
        self.start_tour(url, "test_updated_quality_checks", login='admin')

    def test_update_tracked_consumed_materials_in_shopfloor(self):
        """
        Test that changing the consumed lot in a quality check updates the
        related moves accordingly and pops up a warning if unavailable.

        Detailed steps:
        - Create a bom with using a tracked component.
        - Create a quality check to register the consumed materials.
        - Put 4 SN in stock: 3 in the warehouse of the MO and 1 elsewhere to be unavailable.
        - Create and confirm an MO to consume 2 units.
        - Register: 1 of the reserved unit, 1 of the unreserved one and 1 unavaible one on the QC.

        Check that every update was correctly applied.
        """
        warehouse_1 = self.env.ref("stock.warehouse0")
        locations = self.env['stock.location'].create([
            {
            'name': f"Lovely shelf {i + 1}",
            'location_id': warehouse_1.lot_stock_id.id,
            'usage': 'internal',
            'company_id': self.env.company.id
            } for i in range(3)
        ]) | self.env['stock.warehouse'].create({'name': 'WH2', 'code': 'WH2', 'company_id': self.env.company.id}).lot_stock_id
        final_product, component = self.env['product.product'].create([
            {
            'name': 'Lovely Product',
            'type': 'product',
            'tracking': 'none',
            },
            {
            'name': 'Lovely Component',
            'type': 'product',
            'tracking': 'serial',
            },
        ])
        lots = self.env['stock.lot'].create([
            {'name': f'SN00{i + 1}', 'product_id': component.id}
            for i in range(4)
        ])
        for i in range(4):
            self.env['stock.quant']._update_available_quantity(component, locations[i], quantity=1, lot_id=lots[i])
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
                Command.create({'product_id': component.id, 'product_qty': 2}),
            ]
        })
        self.env['quality.point'].create([
            {
                'picking_type_ids': [Command.link(warehouse_1.manu_type_id.id)],
                'product_ids': [Command.link(final_product.id)],
                'operation_id': bom.operation_ids.id,
                'title': 'Register component',
                'component_id': component.id,
                'test_type_id': self.env.ref('mrp_workorder.test_type_register_consumed_materials').id,
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
        mo.button_plan()
        self.assertEqual(mo.move_raw_ids.lot_ids, lots[:2])
        action = mo.workorder_ids.action_open_mes()
        url = '/web?#action=%s' % (action['id'])
        self.start_tour(url, "test_update_tracked_consumed_materials_in_shopfloor", login='admin')
        self.assertEqual(mo.move_raw_ids.quantity, 3.0)
        self.assertEqual(mo.move_raw_ids.lot_ids, lots[1:])
        self.assertEqual(mo.move_raw_ids.move_line_ids.filtered(lambda m: m.lot_id == lots[1]).location_id, locations[1])
        self.assertEqual(mo.move_raw_ids.move_line_ids.filtered(lambda m: m.lot_id == lots[2]).location_id, locations[2])
        # since the production happens in WH1, the update of SN004 should have fall back on that location
        self.assertEqual(mo.move_raw_ids.move_line_ids.filtered(lambda m: m.lot_id == lots[3]).location_id, warehouse_1.lot_stock_id)

    def test_under_consume_materials_in_shopfloor(self):
        """
        Test that underconsuming in a "register consumed materials" step updates
        the consumed quantity of the component accordingly and that the reservation
        state is not altered.
        """
        warehouse = self.env.ref("stock.warehouse0")
        final_product, component = self.env['product.product'].create([
            {
            'name': 'Lovely Product',
            'type': 'product',
            'tracking': 'none',
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
                Command.create({'product_id': component.id, 'product_qty': 10}),
            ]
        })
        self.env['quality.point'].create([
            {
                'picking_type_ids': [Command.link(warehouse.manu_type_id.id)],
                'product_ids': [Command.link(final_product.id)],
                'operation_id': bom.operation_ids.id,
                'title': 'Register component',
                'component_id': component.id,
                'test_type_id': self.env.ref('mrp_workorder.test_type_register_consumed_materials').id,
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
        self.assertEqual(mo.move_raw_ids.quantity, 10.0)
        action = mo.workorder_ids.action_open_mes()
        url = '/web?#action=%s' % (action['id'])
        self.start_tour(url, "test_under_consume_materials_in_shopfloor", login='admin')
        self.assertEqual(mo.move_raw_ids.quantity, 5.0)
        self.assertEqual(mo.move_raw_ids.move_line_ids.mapped('quantity'), [3.0, 2.0])
        self.assertEqual(len(mo.move_raw_ids.move_line_ids.quality_check_ids), 2.0)
        self.assertEqual(mo.reservation_state, 'assigned')
