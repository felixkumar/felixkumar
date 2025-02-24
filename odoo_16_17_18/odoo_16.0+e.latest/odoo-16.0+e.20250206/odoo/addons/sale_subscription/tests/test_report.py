# -*- coding: utf-8 -*-

from odoo.addons.sale_subscription.tests.common_sale_subscription import TestSubscriptionCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestSubscription(TestSubscriptionCommon):

    def test_mrr_on_pivot_report_with_renew(self):
        self.subscription.action_confirm()
        am = self.subscription._create_recurring_invoice()
        am._post()

        action = self.subscription.prepare_renewal_order()
        renewal_so = self.env['sale.order'].browse(action['res_id'])
        renewal_so.action_confirm()

        (self.subscription | renewal_so).invalidate_recordset()
        res = self.env['sale.subscription.report'].read_group(
            [('partner_id', '=', self.subscription.partner_id.id)],
            ['recurring_monthly:sum'],
            []
        )

        self.assertEqual(res[0]['recurring_monthly'], sum(renewal_so.order_line.mapped('price_unit')))
