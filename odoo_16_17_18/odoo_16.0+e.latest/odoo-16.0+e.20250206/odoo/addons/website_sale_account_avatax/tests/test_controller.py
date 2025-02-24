# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.account_avatax.tests.common import TestAvataxCommon
from odoo.addons.website_sale_account_avatax.controllers.main import WebsiteSaleAvatax
from odoo.addons.website.tools import MockRequest
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

@tagged('post_install', '-at_install')
class TestWebsiteSaleAvataxController(TestAvataxCommon):
    def setUp(self):
        super().setUp()
        self.website = self.env.ref('website.default_website')
        self.Controller = WebsiteSaleAvatax()

    @mute_logger('odoo.addons.account_avatax.models.account_avatax')
    def test_validate_payment_with_error_from_avatax(self):
        """
        Payment should be blocked if Avatax raises an error
        (invalid address, connection issue, etc ...)
        """
        main_company = self.env.ref('base.main_company')

        # fill an american address
        self.env.user.partner_id.with_company(main_company).write({
            'country_id': self.env.ref('base.us').id,
            'state_id': self.env.ref('base.state_us_5').id,
            'zip': '12345',
            'property_account_position_id': self.fp_avatax.id,
        })
        mock_error_response = {
            'error': {'details' : [{'message': 'bim bam boom'}]},
        }

        with MockRequest(self.env, website=self.website):
            self.website.sale_get_order(force_create=True)
            with self.assertRaisesRegex(ValidationError, 'bim bam boom'):
                with self._capture_request(return_value=mock_error_response):
                    self.Controller.shop_payment_validate()
