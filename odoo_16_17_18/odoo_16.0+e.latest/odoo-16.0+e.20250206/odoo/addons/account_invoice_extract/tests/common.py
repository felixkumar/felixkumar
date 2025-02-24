# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from contextlib import contextmanager
from freezegun import freeze_time
from unittest.mock import patch

from odoo.addons.account_invoice_extract.models.account_invoice import AccountMove
from odoo.addons.base.models.ir_cron import ir_cron
from odoo.addons.iap.models.iap_account import IapAccount
from odoo.addons.partner_autocomplete.models.iap_autocomplete_api import IapAutocompleteEnrichAPI
from odoo.sql_db import Cursor
from odoo.tests import common


# Freeze time to avoid nondeterminism in the tests.
# The value of the due date and the creation date are checked to know whether we should fill the due date or not.
# When tests run at around midnight, it can happen that the creation date and the default due date don't
# match, e.g. when one is set at 23:59:59 and the other one at 00:00:00.
# This issue can of course also occur under normal utilization, but it should be very rare and with negligible consequences.
@freeze_time('2019-04-15')
class MockIAP(common.BaseCase):
    @contextmanager
    def mock_iap_extract(self, extract_response, partner_autocomplete_response):
        def _trigger(self, *args, **kwargs):
            # A call to _trigger will directly run the cron
            self.method_direct_trigger()

        # The module iap is committing the transaction when creating an IAP account, we mock it to avoid that
        with patch.object(AccountMove, '_contact_iap_extract', side_effect=lambda *args, **kwargs: extract_response), \
                patch.object(IapAutocompleteEnrichAPI, '_contact_iap', side_effect=lambda *args, **kwargs: partner_autocomplete_response), \
                patch.object(IapAccount, 'get_credits', side_effect=lambda *args, **kwargs: 1), \
                patch.object(Cursor, 'commit', side_effect=lambda *args, **kwargs: None), \
                patch.object(ir_cron, '_trigger', side_effect=_trigger, autospec=True):
            yield
