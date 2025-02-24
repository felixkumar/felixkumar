# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2021 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""
    Test Product Multi Company
"""
from odoo.exceptions import AccessError
from odoo.tests import common

from .common import ProductMultiCompanyCommon


class TestProductMultiCompany(ProductMultiCompanyCommon, common.TransactionCase):
    """
        Test Product Multi Company
    """
    def test_create_product(self):
        """
            Create Product called 'Test'
        """
        product = self.env["product.product"].create({"name": "Test"})
        company = self.env.company
        self.assertTrue(company.id in product.company_ids.ids)

    def test_company_none(self):
        """
            Test Company None
        """
        self.assertFalse(self.product_company_none.company_id)
        # All of this should be allowed
        self.product_company_none.with_user(
            self.user_company_1.id
        ).description_sale = "Test 1"
        self.product_company_none.with_user(
            self.user_company_2.id
        ).description_sale = "Test 2"

    def test_company_1(self):
        """
            Test Company 1
        """
        self.assertEqual(
            self.product_company_1.with_user(self.user_company_1).company_id,
            self.company_1,
        )
        # All of this should be allowed
        self.product_company_1.with_user(
            self.user_company_1
        ).description_sale = "Test 1"
        self.product_company_both.with_user(
            self.user_company_1
        ).description_sale = "Test 2"
        # And this one not
        with self.assertRaises(AccessError):
            self.product_company_2.with_user(
                self.user_company_1
            ).description_sale = "Test 3"

    def test_company_2(self):
        """
            Test Company 2
        """
        self.assertEqual(
            self.product_company_2.with_user(self.user_company_2).company_id,
            self.company_2,
        )
        # All of this should be allowed
        self.product_company_2.with_user(
            self.user_company_2
        ).description_sale = "Test 1"
        self.product_company_both.with_user(
            self.user_company_2
        ).description_sale = "Test 2"
        # And this one not
        with self.assertRaises(AccessError):
            self.product_company_1.with_user(
                self.user_company_2
            ).description_sale = "Test 3"

    def test_uninstall(self):
        """
            Test Uninstall
        """
        from ..hooks import uninstall_hook

        uninstall_hook(self.env.cr, None)
        rule = self.env.ref("product.product_comp_rule")
        domain = (
            " ['|', ('company_id', '=', user.company_id.id), "
            "('company_id', '=', False)]"
        )
        self.assertEqual(rule.domain_force, domain)
