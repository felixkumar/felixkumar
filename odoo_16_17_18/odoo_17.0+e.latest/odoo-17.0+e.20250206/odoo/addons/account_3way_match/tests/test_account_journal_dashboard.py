from freezegun import freeze_time

from odoo import Command
from odoo.addons.account.tests.test_account_journal_dashboard_common import TestAccountJournalDashboardCommon
from odoo.tests import tagged
from odoo.tools.misc import format_amount


@tagged('post_install', '-at_install')
class TestAccountJournalDashboard(TestAccountJournalDashboardCommon):

    @freeze_time("2023-03-15")
    def test_purchase_journal_numbers_and_sums_to_validate(self):
        company_currency = self.company_data['currency']
        journal = self.company_data['default_journal_purchase']

        line_vals = [Command.create({
            'product_id': self.product_a.id,
            'quantity': 1,
            'name': 'product test 1',
            'price_unit': 4000,
            'tax_ids': [],
        })]

        move_vals = {
            'move_type': 'in_invoice',
            'journal_id': journal.id,
            'partner_id': self.partner_a.id,
            'invoice_date': '2023-03-01',
            'date': '2023-03-01',
            'invoice_line_ids': line_vals
        }

        datas = [
            {'invoice_date_due': '2023-04-30'},
            {'invoice_date_due': '2023-04-30', 'release_to_pay': 'yes'},
            {'invoice_date_due': '2023-04-30', 'release_to_pay': 'no'},
            {'invoice_date_due': '2023-03-01'},
            {'invoice_date_due': '2023-03-01', 'release_to_pay': 'yes'},
            {'invoice_date_due': '2023-03-01', 'release_to_pay': 'no'},
        ]

        moves = self.env['account.move'].create([move_vals] * len(datas))

        for move, data in zip(moves, datas):
            move.write(data)

        dashboard_data = journal._get_journal_dashboard_data_batched()[journal.id]
        # Expected behavior is to have six amls waiting for payment for a total amount of 4440$
        # three of which would be late for a total amount of 140$
        self.assertEqual(4, dashboard_data['number_draft'])
        self.assertEqual(format_amount(self.env, 16000, company_currency), dashboard_data['sum_draft'])
