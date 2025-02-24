# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged
from odoo.addons.website.tools import MockRequest
from odoo.exceptions import UserError
from .common import TestWebsiteSaleSubscriptionCommon

@tagged('post_install', '-at_install')
class TestWebsiteSaleSubscription(TestWebsiteSaleSubscriptionCommon):

    def test_cart_update_so_reccurence(self):
        # Product not recurring
        product = self.env['product.template'].with_context(website_id=self.current_website.id).create({
            'name': 'Streaming SUB Weekly',
            'list_price': 15,
            'type': 'service',
        })
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })

        # Mocking to check if error raised on Website when adding
        # 2 subscription product with different recurrence
        with MockRequest(self.env, website=self.current_website, sale_order_id=so.id):
            so = self.current_website.sale_get_order()
            self.assertFalse(so.recurrence_id)
            so._cart_update(product_id=product.product_variant_ids.id, add_qty=1)
            self.assertFalse(so.recurrence_id)
            so._cart_update(product_id=self.sub_product.product_variant_ids.id, add_qty=1)
            self.assertEqual(so.recurrence_id, self.recurrence_week)
            with self.assertRaises(UserError, msg="You can't add a subscription product to a sale order with another recurrence."):
                so._cart_update(product_id=self.sub_product_2.product_variant_ids.id, add_qty=1)
            so._cart_update(product_id=self.sub_product.product_variant_ids.id, add_qty=None, set_qty=0)
            self.assertFalse(so.recurrence_id)
            so._cart_update(product_id=self.sub_product_2.product_variant_ids.id, add_qty=1)
            self.assertEqual(so.recurrence_id, self.recurrence_month)
            so._cart_update(product_id=self.sub_product_2.product_variant_ids.id, add_qty=None, set_qty=0)
            self.assertFalse(so.recurrence_id)

    def test_combination_info_product(self):
        self.sub_product = self.sub_product.with_context(website_id=self.current_website.id)

        with MockRequest(self.env, website=self.current_website):
            combination_info = self.sub_product._get_combination_info()
            self.assertEqual(combination_info['price'], 5)
            self.assertTrue(combination_info['is_subscription'])
            self.assertEqual(combination_info['subscription_duration'], 1)
            self.assertEqual(combination_info['subscription_unit'], 'week')

    def test_combination_info_variant_products(self):
        self.sub_with_variants.with_context(website_id=self.current_website.id)

        with MockRequest(self.env, website=self.current_website):
            combination_info = self.sub_with_variants._get_combination_info(product_id=self.sub_with_variants.product_variant_ids[0].id)
            self.assertEqual(combination_info['price'], 10)
            self.assertTrue(combination_info['is_subscription'])
            self.assertEqual(combination_info['subscription_duration'], 1)
            self.assertEqual(combination_info['subscription_unit'], 'week')

            combination_info_variant_2 = self.sub_with_variants._get_combination_info(product_id=self.sub_with_variants.product_variant_ids[-1].id)
            self.assertEqual(combination_info_variant_2['price'], 25)
            self.assertTrue(combination_info_variant_2['is_subscription'])
            self.assertEqual(combination_info_variant_2['subscription_duration'], 1)
            self.assertEqual(combination_info_variant_2['subscription_unit'], 'month')

    def test_combination_info_multi_pricelist(self):
        product = self.sub_product_3.with_context(website_id=self.current_website.id)

        with MockRequest(self.env, website=self.current_website, website_sale_current_pl=self.pricelist_111.id):
            combination_info = product._get_combination_info()
            self.assertEqual(combination_info['price'], 111)

        with MockRequest(self.env, website=self.current_website, website_sale_current_pl=self.pricelist_222.id):
            combination_info = product._get_combination_info()
            self.assertEqual(combination_info['price'], 222)
