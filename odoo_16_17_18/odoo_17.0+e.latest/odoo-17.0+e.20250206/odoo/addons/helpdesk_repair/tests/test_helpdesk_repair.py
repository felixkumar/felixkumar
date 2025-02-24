# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests.common import Form
from odoo.addons.helpdesk.tests.common import HelpdeskCommon


class TestRepair(HelpdeskCommon):
    def test_lot_id(self):
        """ This test purpose is to ensure that, if present, the context key default_lot_id is not
        propagated to the action_repair_done(). """
        self.env.ref('base.group_user').implied_ids = [(4, self.env.ref('stock.group_production_lot').id)]

        company = self.env.company
        product = self.env['product.product'].create({'name': 'Product'})
        product_lot = self.env['stock.lot'].create({
            'product_id': product.id,
            'company_id': company.id})
        component = self.env['product.product'].create({'name': 'Component'})

        ro_form = Form(self.env['repair.order'].with_context(default_lot_id=product_lot.id))
        ro_form.product_id = product
        ro_form.partner_id = company.partner_id
        with ro_form.move_ids.new() as ro_line:
            ro_line.product_id = component

        repair_order = ro_form.save()
        repair_order.action_validate()
        repair_order.action_repair_start()
        repair_order.action_repair_end()

    def test_helpdesk_repair(self):
        self.test_team.use_product_repairs = True

        product = self.env['product.product'].create({'name': 'Product'})

        ticket = self.env['helpdesk.ticket'].create({
            'name': 'test',
            'partner_id': self.partner.id,
            'team_id': self.test_team.id,
        })

        ro_form = Form(self.env['repair.order'].with_context(default_ticket_id=ticket.id))
        ro_form.product_id = product

        repair_order = ro_form.save()
        repair_order._action_repair_confirm()

        self.assertEqual(ticket.repairs_count, 1, 'The ticket should be linked to a return')
        self.assertEqual(repair_order.id, ticket.repair_ids[0].id, 'The correct return should be referenced in the ticket')

        repair_order.action_repair_start()
        repair_order.action_repair_end()

        last_message = str(ticket.message_ids[0].body)

        self.assertTrue(repair_order.display_name in last_message and 'Repair' in last_message,
            'Repair validation should be logged on the ticket')

    def test_helpdesk_return_and_repair(self):
        self.test_team.use_product_returns = True
        self.test_team.use_product_repairs = True

        self.env['account.account'].create({
            'code': 'X1012',
            'name': 'Debtors - (test)',
            'reconcile': True,
            'account_type': 'asset_receivable',
        })
        a_sale = self.env['account.account'].create({
            'code': 'X2020',
            'name': 'Product Sales - (test)',
            'account_type': 'income',
        })
        self.sales_journal = self.env['account.journal'].create({
            'name': 'Customer Invoices - Test',
            'code': 'TINV',
            'type': 'sale',
            'default_account_id': a_sale.id,
            'refund_sequence': True,
        })

        product, part = self.env['product.product'].create([
            {
                'name': 'final product',
                'type': 'product',
            },
            {
                'name': 'part',
                'type': 'product',
            }
        ])
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.env['sale.order.line'].create({
            'product_id': product.id,
            'price_unit': 10,
            'product_uom_qty': 1,
            'order_id': so.id,
        })
        so.action_confirm()
        so._create_invoices()
        invoice = so.invoice_ids
        invoice.action_post()
        so.picking_ids[0].move_ids[0].quantity = 1
        so.picking_ids[0].button_validate()

        ticket = self.env['helpdesk.ticket'].create({
            'name': 'test',
            'partner_id': self.partner.id,
            'team_id': self.test_team.id,
            'sale_order_id': so.id,
        })
        stock_picking_form = Form(self.env['stock.return.picking'].with_context({
            'active_model': 'helpdesk.ticket',
            'default_ticket_id': ticket.id
        }))
        stock_picking_form.picking_id = so.picking_ids[0]
        return_picking = stock_picking_form.save()
        return_picking.create_returns()
        return_picking = self.env['stock.picking'].search([
            ('partner_id', '=', self.partner.id),
            ('picking_type_code', '=', 'incoming'),
        ])
        return_picking.move_ids[0].quantity = 1
        return_picking.button_validate()

        res_dict = ticket.action_repair_order_form()
        ro_form = Form(self.env[(res_dict.get('res_model'))].with_context(res_dict['context']), view=res_dict['view_id'])
        with ro_form.move_ids.new() as move:
            move.product_id = part
            move.product_uom_qty = 1.0
            move.quantity = 1.0
            move.repair_line_type = 'add'
        repair_order = ro_form.save()
        repair_order.action_validate()
        repair_order.action_repair_start()
        repair_order.action_repair_end()
        delivery = so.picking_ids - return_picking
        self.assertRecordValues(delivery.move_ids, [{'product_id': product.id, 'quantity': 1.0}])
        return_picking = so.picking_ids.filtered(lambda p: p.picking_type_id == so.warehouse_id.in_type_id)
        self.assertRecordValues(return_picking.move_ids, [{'product_id': product.id, 'quantity': 1.0}])
