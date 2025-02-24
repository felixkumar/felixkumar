# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.sale_subscription.tests.common_sale_subscription import TestSubscriptionCommon
from odoo.tests.common import Form
from odoo.tests import tagged
from odoo import Command


@tagged('post_install', '-at_install')
class TestSubscriptionSaleOrder(TestSubscriptionCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.order_1 = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [Command.create({'product_id': cls.product.id})],
        })

    def test_change_recurrence_plan_with_option(self):
        """
        A recurring order with a line for a recurring produce and a sale order option for a recurring product yields an
            exception when changing the recurring plan via Form, preventing the plan from being changed
        """
        self.env['sale.order.option'].create({
            'order_id': self.order_1.id,
            'product_id': self.product.id,
        })

        with Form(self.order_1) as order_form:
            order_form.recurrence_id = self.recurrence_week

        self.assertEqual(self.order_1.recurrence_id, self.recurrence_week)
