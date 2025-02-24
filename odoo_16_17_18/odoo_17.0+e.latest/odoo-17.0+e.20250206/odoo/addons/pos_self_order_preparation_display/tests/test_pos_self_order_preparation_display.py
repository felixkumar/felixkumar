# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo.tests
from odoo.addons.pos_self_order.tests.self_order_common_test import SelfOrderCommonTest

@odoo.tests.tagged("post_install", "-at_install")
class TestPosSelfOrderPreparationDisplay(SelfOrderCommonTest):

    def test_self_order_preparation_disabling_preparation_display(self):
        """
        This test ensures that the preparation display option can be disabled when the self_ordering_mode is set to 'nothing'.
        It also tests that the preparation display option is enabled automatically when the self_ordering_mode is set to 'kiosk'.
        """
        self.pos_config.self_ordering_pay_after = 'each'
        with odoo.tests.Form(self.env['res.config.settings']) as form:
            with self.assertLogs(level="WARNING"):
                form.module_pos_preparation_display = False

            self.pos_config.write({
                'self_ordering_mode': 'nothing',
            })
            form.pos_config_id = self.pos_config
            self.assertEqual(form.module_pos_preparation_display, False)

            self.pos_config.write({
                'self_ordering_mode': 'kiosk',
            })
            form.pos_config_id = self.pos_config
            self.assertEqual(form.module_pos_preparation_display, True)
