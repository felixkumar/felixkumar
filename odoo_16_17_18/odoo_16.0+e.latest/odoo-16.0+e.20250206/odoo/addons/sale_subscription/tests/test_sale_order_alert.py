from odoo.addons.sale_subscription.tests.common_sale_subscription import TestSubscriptionCommon
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestSaleOrderAlert(TestSubscriptionCommon):
    def test_sale_order_alert_stages(self):
        """
        Check that a sale order alert generates exactly one activity when the stage of a subscription changes
        from the `from` stage to the `to` stage defined in the alert.
        """
        stage_in_progress = self.env['sale.order.stage'].search([('name', '=', 'In Progress')])

        subscription = self.subscription
        alerts = self.env['sale.order.alert'].create([{
            'name': 'Activity when a subscription reaches Progress stage',
            'trigger_condition': 'on_create_or_write',
            'action': 'next_activity',
            'activity_user': 'contract',
            'stage_to_id': stage_in_progress.id,
        },
        {
            'name': 'Activity when a subscription leaves Progress stage',
            'trigger_condition': 'on_create_or_write',
            'action': 'next_activity',
            'activity_user': 'contract',
            'stage_from_id': stage_in_progress.id,
        },
        ])
        alerts.activity_type_id = self.env['mail.activity.type'].search([('name', '=', 'Email')])

        activity_count = len(subscription.activity_ids)
        subscription.internal_note = "trigger a write on the subscription"
        self.assertEqual(len(subscription.activity_ids), activity_count)

        subscription.action_confirm()
        self.assertEqual(len(subscription.activity_ids), activity_count + 1)

        subscription.set_close()
        subscription.action_cancel()
        subscription.action_draft()
        self.assertEqual(len(subscription.activity_ids), activity_count + 2)
