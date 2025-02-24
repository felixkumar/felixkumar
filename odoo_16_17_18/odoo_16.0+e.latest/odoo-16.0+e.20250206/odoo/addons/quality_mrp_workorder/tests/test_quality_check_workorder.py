# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import Command
from odoo.tests import Form, HttpCase, tagged
from odoo.addons.mrp.tests.common import TestMrpCommon
from odoo.addons.mrp_workorder.tests import test_tablet_client_action

_logger = logging.getLogger(__name__)


class TestQualityCheckWorkorder(TestMrpCommon):

    def test_01_quality_check_with_component_consumed_in_operation(self):
        """ Test quality check on a production with a component consumed in one operation
        """

        picking_type_id = self.env.ref('stock.warehouse0').manu_type_id.id
        component = self.env['product.product'].create({
            'name': 'consumable component',
            'type': 'consu',
        })
        bom = self.bom_2.copy()
        bom.bom_line_ids[0].product_id = component

        # Registering the first component in the operation of the BoM
        bom.bom_line_ids[0].operation_id = bom.operation_ids[0]

        # Create Quality Point for the product consumed in the operation of the BoM
        self.env['quality.point'].create({
            'product_ids': [bom.bom_line_ids[0].product_id.id],
            'picking_type_ids': [picking_type_id],
            'measure_on': 'move_line',
        })
        # Create Quality Point for all products (that should not apply on components)
        self.env['quality.point'].create({
            'product_ids': [],
            'picking_type_ids': [picking_type_id],
            'measure_on': 'move_line',
        })

        # Create Production of Painted Boat to produce 5.0 Unit.
        production_form = Form(self.env['mrp.production'])
        production_form.product_id = bom.product_id
        production_form.bom_id = bom
        production_form.product_qty = 5.0
        production = production_form.save()
        production.action_confirm()
        production.qty_producing = 3.0

        # Check that the Quality Check were created and has correct values
        self.assertEqual(len(production.move_raw_ids[0].move_line_ids.check_ids), 2)
        self.assertEqual(len(production.move_raw_ids[1].move_line_ids.check_ids), 0)
        self.assertEqual(len(production.check_ids.filtered(lambda qc: qc.product_id == production.product_id)), 1)
        self.assertEqual(len(production.check_ids), 2)

        # Registering consumption in tablet view
        wo = production.workorder_ids[0]
        wo.open_tablet_view()
        wo.qty_done = 10.0
        wo.current_quality_check_id.action_next()
        self.assertEqual(len(production.move_raw_ids[0].move_line_ids.check_ids), 2)

    def test_register_consumed_materials(self):
        """
        Process a MO based on a BoM with one operation. That operation has one
        step: register the used component. Both finished product and component
        are tracked by serial. The auto-completion of the serial numbers should
        be correct
        """
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)

        finished = self.bom_4.product_id
        component = self.bom_4.bom_line_ids.product_id
        (finished | component).write({
            'type': 'product',
            'tracking': 'serial',
        })

        finished_sn, component_sn = self.env['stock.lot'].create([{
            'name': p.name,
            'product_id': p.id,
            'company_id': self.env.company.id,
        } for p in (finished, component)])
        self.env['stock.quant']._update_available_quantity(component, warehouse.lot_stock_id, 1, lot_id=component_sn)

        type_register_materials = self.env.ref('mrp_workorder.test_type_register_consumed_materials')
        operation = self.env['mrp.routing.workcenter'].create({
            'name': 'Super Operation',
            'bom_id': self.bom_4.id,
            'workcenter_id': self.workcenter_2.id,
            'quality_point_ids': [(0, 0, {
                'product_ids': [(4, finished.id)],
                'picking_type_ids': [(4, warehouse.manu_type_id.id)],
                'test_type_id': type_register_materials.id,
                'component_id': component.id,
                'bom_id': self.bom_4.id,
                'measure_on': 'operation',
            })]
        })
        self.bom_4.operation_ids = [(6, 0, operation.ids)]

        mo_form = Form(self.env['mrp.production'])
        mo_form.bom_id = self.bom_4
        mo = mo_form.save()
        mo.action_confirm()

        mo_form = Form(mo)
        mo_form.lot_producing_id = finished_sn
        mo = mo_form.save()

        self.assertEqual(mo.workorder_ids.finished_lot_id, finished_sn)
        self.assertEqual(mo.workorder_ids.lot_id, component_sn)

        mo.workorder_ids.current_quality_check_id.action_next()
        mo.workorder_ids.do_finish()
        mo.button_mark_done()

        self.assertRecordValues(mo.move_raw_ids.move_line_ids + mo.move_finished_ids.move_line_ids, [
            {'qty_done': 1, 'lot_id': component_sn.id},
            {'qty_done': 1, 'lot_id': finished_sn.id},
        ])

    def test_backorder_cancelled_workorder_quality_check(self):
        """ Create an MO based on a bom with 2 operations, when processing workorders,
            process one workorder fully and the other partially, then confirm and create backorder
            the fully finished workorder copy should be cancelled without any checks to do, and the other
            should ready, we should be able to pass the checks and produce the backorder
        """
        bom = self.env['mrp.bom'].create({
            'product_id': self.product_6.id,
            'product_tmpl_id': self.product_6.product_tmpl_id.id,
            'product_qty': 1,
            'type': 'normal',
            'operation_ids': [
                (0, 0, {'name': 'Cut', 'workcenter_id': self.workcenter_1.id, 'time_cycle': 12, 'sequence': 1}),
                (0, 0, {'name': 'Weld', 'workcenter_id': self.workcenter_1.id, 'time_cycle': 18, 'sequence': 2}),
            ],
            'bom_line_ids': [
                (0, 0, {'product_id': self.product_3.id, 'product_qty': 2}),
                (0, 0, {'product_id': self.product_2.id, 'product_qty': 3}),
            ]
        })
        operation_ids = bom.operation_ids
        self.env['stock.quant'].create([
            {
                'product_id': self.product_3.id,
                'product_uom_id': self.uom_unit.id,
                'location_id': self.location_1.id,
                'quantity': 4,
            },
            {
                'product_id': self.product_2.id,
                'product_uom_id': self.uom_unit.id,
                'location_id': self.location_1.id,
                'quantity': 6,
            },
        ])
        self.env['quality.point'].create([
            {
                'title': 'test QP1',
                'product_ids': [(4, self.product_6.id, 0)],
                'operation_id': operation_ids[0].id,
                'note': 'Cut',
            },
            {
                'title': 'test QP2',
                'product_ids': [(4, self.product_6.id, 0)],
                'operation_id': operation_ids[1].id,
                'note': 'Weld',
            }
        ])
        mo = self.env['mrp.production'].create({
            'product_id': self.product_6.id,
            'product_qty': 2,
            'bom_id': bom.id,
        })
        mo.action_confirm()
        self.assertEqual(len(mo.move_raw_ids), 2)
        self.assertEqual(len(mo.workorder_ids), 2)
        self.assertEqual(len(mo.workorder_ids.check_ids), 2)
        # 1 work order will produce the full 2 qty, the other will only produce 1
        full_workorder = mo.workorder_ids[0]
        full_workorder.qty_producing = 2
        full_workorder.check_ids.action_pass_and_next()
        full_workorder.button_finish()
        self.assertEqual(full_workorder.state, 'done')
        partial_workorder = mo.workorder_ids[1]
        partial_workorder.qty_producing = 1
        partial_workorder.check_ids.action_pass_and_next()
        partial_workorder.button_finish()
        self.assertEqual(partial_workorder.state, 'done')
        # MO qty_producing should become 1 since only 1 qty was fully produced
        self.assertEqual(mo.qty_producing, 1)
        action = mo.button_mark_done()
        backorder_form = Form(self.env[action['res_model']].with_context(**action['context']))
        backorder_form.save().action_backorder()
        backorder = mo.procurement_group_id.mrp_production_ids[1]
        # the backorder has 1 qty to produce and the full workorder done from before should be cancelled (its a copy)
        # and should not have any quality check to perform
        self.assertEqual(backorder.product_qty, 1)
        self.assertEqual(len(backorder.workorder_ids), 2)
        self.assertEqual(backorder.workorder_ids[0].state, 'cancel')
        self.assertEqual(len(backorder.workorder_ids[0].check_ids), 0)
        backorder.workorder_ids[1].qty_producing = 1
        backorder.workorder_ids[1].check_ids.action_pass_and_next()
        backorder.workorder_ids[1].button_finish()
        backorder.button_mark_done()
        self.assertEqual(backorder.state, 'done')


@tagged('post_install', '-at_install')
class TestPickingWorkorderClientActionQuality(test_tablet_client_action.TestWorkorderClientActionCommon, HttpCase):

    def test_control_per_op_quantity_quality_check(self):
        """ Test quality point control per product on workorder operation
        """
        self.env['quality.point'].create({
            'title': 'test QP1',
            'picking_type_ids': [(4, self.env['stock.picking.type'].search([('code', '=', 'mrp_operation')], limit=1).id)],
            'measure_on': 'move_line',
            'product_ids': [(4, self.bom_2.product_id.id, 0)],
            'operation_id': self.bom_2.operation_ids.id,
            'note': 'Cut',
        })

        mo_form = Form(self.env['mrp.production'])
        mo_form.bom_id = self.bom_2
        mo = mo_form.save()
        mo.action_confirm()

        # Check created on the workorder not the MO
        self.assertEqual(len(mo.check_ids), 0)
        self.assertEqual(len(mo.workorder_ids), 1)
        self.assertEqual(len(mo.workorder_ids.check_ids), 1)

    def test_register_consumed_materials_01(self):
        """
        Process a MO based on a BoM with one operation. That operation has one
        step: register the used component. Both finished product and component
        are tracked by serial. Changing both the finished product and the
        component serial at the same time should record both values.

        Also ensure if there is an overlapping quality.point for MOs (i.e. not
        a WO step), the SNs are as expected between:
        WO step <-> MO QC <-> move_line.lot_id
        regardless of which one is changed. All 3 use case occurring at the same
        time is unlikely, but helps tests expected behavior for the possible
        combinations of these use cases within 1 test
        """
        # The test requires the tablet timer group
        self.env.ref('base.group_user').implied_ids += (
            self.env.ref('mrp_workorder.group_mrp_wo_tablet_timer')
        )
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)

        finished = self.potion
        component = self.ingredient_1
        (finished | component).write({
            'type': 'product',
            'tracking': 'serial',
        })

        finished_sn, component_sn = self.env['stock.lot'].create([{
            'name': p.name + "_1",
            'product_id': p.id,
            'company_id': self.env.company.id,
        } for p in (finished, component)])
        finished_sn2, component_sn2 = self.env['stock.lot'].create([{
            'name': p.name + "_2",
            'product_id': p.id,
            'company_id': self.env.company.id,
        } for p in (finished, component)])
        component_sn3 = self.env['stock.lot'].create({
            'name': component.name + "_3",
            'product_id': component.id,
            'company_id': self.env.company.id,
        })
        self.env['stock.quant']._update_available_quantity(component, warehouse.lot_stock_id, 1, lot_id=component_sn)
        self.env['stock.quant']._update_available_quantity(component, warehouse.lot_stock_id, 1, lot_id=component_sn2)
        self.env['stock.quant']._update_available_quantity(component, warehouse.lot_stock_id, 1, lot_id=component_sn3)

        type_register_materials = self.env.ref('mrp_workorder.test_type_register_consumed_materials')
        self.wizarding_step_1.test_type_id = type_register_materials
        self.wizarding_step_2.unlink()

        self.env['quality.point'].create({
            'product_ids': [component.id],
            'picking_type_ids': [(4, warehouse.manu_type_id.id)],
            'measure_on': 'move_line',
        })

        mo_form = Form(self.env['mrp.production'])
        mo_form.bom_id = self.bom_potion
        mo = mo_form.save()
        mo.action_confirm()

        self.assertEqual(mo.move_raw_ids.move_line_ids.lot_id, component_sn, "Unexpected reserved SN for MO component")
        self.assertEqual(mo.check_ids.lot_line_id, component_sn, "MO level QC should have been created with reserved SN")
        self.assertEqual(len(mo.workorder_ids.check_ids), 1, "WO and its step should have been created")
        self.assertEqual(mo.workorder_ids.check_ids.lot_id, component_sn, "WO's component lot should match reserved SN")

        mo.move_raw_ids.move_line_ids.lot_id = component_sn2
        mo.lot_producing_id = finished_sn

        self.assertEqual(mo.move_raw_ids.move_line_ids.lot_id, component_sn2, "Changing final product sn shouldn't affect component sn")
        self.assertEqual(mo.check_ids.lot_line_id, component_sn2, "MO level QC should update to match ml.lot_id")
        self.assertEqual(mo.workorder_ids.check_ids.lot_id, component_sn2, "WO's component lot should update to match ml.lot_id")
        wo = mo.workorder_ids[0]
        url = self._get_client_action_url(wo.id)

        self.start_tour(url, 'test_serial_tracked_and_register', login='admin', timeout=120)

        self.assertEqual(mo.workorder_ids.finished_lot_id, finished_sn2)
        self.assertEqual(mo.workorder_ids.check_ids.lot_id, component_sn, "WO level QC should be using newly selected SN")
        self.assertEqual(mo.check_ids.lot_line_id, component_sn, "MO level QC should update to match completed WO sn")
        self.assertEqual(mo.move_raw_ids.move_line_ids.lot_id, component_sn, "MO component SN should update to match completed WO sn")
        mo.check_ids.do_pass()
        mo.button_mark_done()

        self.assertRecordValues(mo.move_raw_ids.move_line_ids + mo.move_finished_ids.move_line_ids, [
            {'qty_done': 1, 'lot_id': component_sn.id},
            {'qty_done': 1, 'lot_id': finished_sn2.id},
        ])

    def test_measure_quality_check(self):
        self.env['quality.point'].create({
            'title': 'Measure Wand Step',
            'product_ids': [(4, self.potion.id)],
            'picking_type_ids': [(4, self.picking_type_manufacturing.id)],
            'operation_id': self.wizard_op_1.id,
            'test_type_id': self.env.ref('quality_control.test_type_measure').id,
            'norm': 15,
            'tolerance_min': 14,
            'tolerance_max': 16,
            'sequence': 0,
            'note': '<p>Make sure your wand is the correct size for the "magic" to happen</p>',
        })
        mo_form = Form(self.env['mrp.production'])
        mo_form.bom_id = self.bom_potion
        mo = mo_form.save()
        mo.action_confirm()
        mo.qty_producing = mo.product_qty

        self.assertEqual(mo.workorder_ids.check_ids.filtered(lambda x: x.test_type == 'measure').quality_state, 'none')

        res_action = mo.workorder_ids.check_ids.filtered(lambda x: x.test_type == 'measure').do_measure()

        self.assertEqual(mo.workorder_ids.check_ids.filtered(lambda x: x.test_type == 'measure').quality_state, 'fail', 'The measure quality check should have failed')
        self.assertEqual(res_action.get('res_model'), 'quality.check.wizard', 'The action should return a wizard when failing')

    def test_delete_workorder_linked_to_quality_check(self):
        """
        Test that a quality check is deleted when its linked workorder is deleted.
        * When components is tracked by lot, a quality check is created and linked to the last workorder.
        and when the last workorder is deleted, the quality check should be deleted too
        because a new quality check will be created.
        """
        self.bom_2.bom_line_ids.product_id.tracking = 'lot'
        self.bom_2.operation_ids.copy({'name': 'OP1'})
        mo_form = Form(self.env['mrp.production'])
        mo_form.bom_id = self.bom_2
        mo = mo_form.save()
        mo.action_confirm()
        self.assertEqual(len(mo.workorder_ids), 2)
        qc = self.env['quality.check'].search([('product_id', '=', self.bom_2.product_id.id)], limit=1)
        self.assertEqual(len(qc), 1)
        self.assertEqual(qc.mapped('workorder_id'), mo.workorder_ids[-1])
        mo.workorder_ids[-1].unlink()
        self.assertFalse(qc.exists())
        qc = self.env['quality.check'].search([('product_id', '=', self.bom_2.product_id.id)])[0]
        self.assertEqual(len(qc), 1)
        self.assertEqual(qc.mapped('workorder_id'), mo.workorder_ids[-1])

    def test_skipping_when_measure_fail_then_correct_it_tablet_wizard(self):
        product_1 = self.env['product.product'].create({'name': 'Table'})
        workcenter_1 = self.env['mrp.workcenter'].create({
            'name': 'Test Workcenter',
        })
        bom = self.env['mrp.bom'].create({
            'product_id': product_1.id,
            'product_tmpl_id': product_1.product_tmpl_id.id,
            'product_uom_id': product_1.uom_id.id,
            'product_qty': 1.0,
            'consumption': 'flexible',
            'operation_ids': [
                (0, 0, {'name': 'Assembly', 'workcenter_id': workcenter_1.id, 'time_cycle': 15, 'sequence': 1}),
            ],
            'type': 'normal',
        })
        qp1 = self.env['quality.point'].create({
            'title': 'Step1',
            'product_ids': [product_1.id],
            'operation_id': bom.operation_ids.id,
            'company_id': self.env.ref('base.main_company').id,
            'test_type_id': self.env.ref('quality_control.test_type_measure').id,
            'norm': 70,
            'tolerance_min': 60,
            'tolerance_max': 75
        })
        qp2 = self.env['quality.point'].create({
            'title': 'Step2',
            'product_ids': [product_1.id],
            'operation_id': bom.operation_ids.id,
            'company_id': self.env.ref('base.main_company').id,
            'test_type_id': self.env.ref('quality_control.test_type_passfail').id
        })
        qp3 = self.env['quality.point'].create({
            'title': 'Step3',
            'product_ids': [product_1.id],
            'operation_id': bom.operation_ids.id,
            'company_id': self.env.ref('base.main_company').id,
            'test_type_id': self.env.ref('quality_control.test_type_passfail').id
        })
        qc1 = self.env['quality.check'].create({'point_id': qp1.id,
                                                'team_id': 1})
        qc2 = self.env['quality.check'].create({'point_id': qp2.id,
                                                'team_id': 1})
        qc3 = self.env['quality.check'].create({'point_id': qp3.id,
                                                'team_id': 1})

        qc1.write({'next_check_id': qc2.id})
        qc2.write({'next_check_id': qc3.id, 'previous_check_id': qc1.id})
        qc3.write({'previous_check_id': qc2.id})

        production = self.env['mrp.production'].create({
            'bom_id': bom.id,
            'product_id': product_1.id,
            'product_tmpl_id': product_1.product_tmpl_id.id,
        })

        mo = self.env['mrp.workorder'].create({
            'name': 'Test order',
            'workcenter_id': self.workcenter_1.id,
            'product_uom_id': self.env.ref('uom.product_uom_gram').id,
            'production_id': production.id,
            'qty_producing': 2,
            'check_ids': [qc1.id, qc2.id, qc3.id],
            'current_quality_check_id': qc1.id
        })

        qc1.write({'measure': 50})
        qc1.do_measure()
        qc1.write({'measure': 70})
        qc1.do_measure()
        self.assertEqual(mo.current_quality_check_id.id, qc2.id)

    def test_getting_to_next_step(self):
        product_1 = self.env['product.product'].create({'name': 'Table'})
        workcenter_1 = self.env['mrp.workcenter'].create({
            'name': 'Test Workcenter',
        })
        bom = self.env['mrp.bom'].create({
            'product_id': product_1.id,
            'product_tmpl_id': product_1.product_tmpl_id.id,
            'product_uom_id': product_1.uom_id.id,
            'product_qty': 1.0,
            'consumption': 'flexible',
            'operation_ids': [
                (0, 0, {'name': 'Assembly', 'workcenter_id': workcenter_1.id, 'time_cycle': 15, 'sequence': 1}),
            ],
            'type': 'normal',
        })
        qp1 = self.env['quality.point'].create({
            'title': 'Step1',
            'product_ids': [Command.link(product_1.id)],
            'operation_id': bom.operation_ids.id,
            'company_id': self.env.ref('base.main_company').id,
            'test_type_id': self.env.ref('quality_control.test_type_passfail').id,
        })
        qp2 = self.env['quality.point'].create({
            'title': 'Step2',
            'product_ids': [Command.link(product_1.id)],
            'operation_id': bom.operation_ids.id,
            'company_id': self.env.ref('base.main_company').id,
            'test_type_id': self.env.ref('quality_control.test_type_passfail').id
        })
        qc1 = self.env['quality.check'].create({'point_id': qp1.id,
                                                'team_id': 1})
        qc2 = self.env['quality.check'].create({'point_id': qp2.id,
                                                'team_id': 1})

        qc1.write({'next_check_id': qc2.id})
        qc2.write({'previous_check_id': qc1.id})

        production = self.env['mrp.production'].create({
            'bom_id': bom.id,
            'product_id': product_1.id,
            'product_tmpl_id': product_1.product_tmpl_id.id,
        })

        mo = self.env['mrp.workorder'].create({
            'name': 'Test order',
            'workcenter_id': self.workcenter_1.id,
            'product_uom_id': self.env.ref('uom.product_uom_gram').id,
            'production_id': production.id,
            'qty_producing': 2,
            'check_ids': [Command.link(qc1.id), Command.link(qc2.id)],
            'current_quality_check_id': qc1.id
        })

        qc1.action_fail_and_next()

        self.assertEqual(mo.current_quality_check_id.id, qc2.id)
