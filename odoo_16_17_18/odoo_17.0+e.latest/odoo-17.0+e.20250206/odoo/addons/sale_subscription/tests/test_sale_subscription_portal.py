# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.fields import Command, Date
from odoo.tests import HttpCase, tagged
from odoo.addons.sale_subscription.tests.common_sale_subscription import TestSubscriptionCommon

@tagged('post_install', '-at_install')
class TestSubscription(TestSubscriptionCommon, HttpCase):
    def test_pay_button_enabled_in_portal(self):
        # Check that the pay button is enabled when having only one payment provider enabled
        self.env['payment.provider'].search([]).write({'is_published': False})
        self.dummy_provider = self.env['payment.provider'].create({
            'name': "Dummy Provider",
            'code': 'none',
            'state': 'test',
            'is_published': True,
            'payment_method_ids': [Command.set([self.env.ref('payment.payment_method_unknown').id])],
            'allow_tokenization': True,
            'redirect_form_view_id': self.env['ir.ui.view'].search([('type', '=', 'qweb')], limit=1).id,
        })
        self.env.ref('payment.payment_method_unknown').write({
            'active': True,
            'support_tokenization': True,
        })
        sub = self.subscription
        sub.action_confirm()
        self.start_tour(self.subscription.get_portal_url(), 'test_sale_subscription_portal')

    def test_optional_products_appearance_in_portal(self):
        self.subscription.write({
            'start_date': Date.to_date('2024-06-18'),
            'sale_order_option_ids': [
                (0, 0, {
                    'name': 'optional product',
                    'price_unit': 1,
                    'uom_id': self.env.ref('uom.product_uom_unit').id,
                    'product_id': self.env['product.product'].create({'name': 'optional product'}).id,
                }),
            ],
        })
        self.start_tour(self.subscription.get_portal_url(), 'test_optional_products_portal')
