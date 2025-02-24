# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.account_accountant.tests.test_bank_rec_widget import WizardForm
from odoo.exceptions import RedirectWarning
from odoo.tests import tagged
from odoo import fields, Command
from unittest.mock import MagicMock, patch


@tagged('post_install', '-at_install')
class TestSynchStatementCreation(AccountTestInvoicingCommon):
    def setUp(self):
        super(TestSynchStatementCreation, self).setUp()
        self.bnk_stmt_line = self.env['account.bank.statement.line']
        self.env.ref('base.EUR').active = True
        # Create an account.online.link and account.online.account and associate to journal bank
        self.bank_journal = self.env['account.journal'].create({
            'name': 'Bank_Online',
            'type': 'bank',
            'code': 'BNKon',
            'currency_id': self.env.ref('base.EUR').id,
        })
        self.link_account = self.env['account.online.link'].create({'name': 'Test Bank'})
        self.online_account = self.env['account.online.account'].create({
            'name': 'MyBankAccount',
            'account_online_link_id': self.link_account.id,
            'journal_ids': [(6, 0, self.bank_journal.id)]
        })
        self.transaction_id = 1
        self.account = self.env['account.account'].create({
            'name': 'toto',
            'code': 'bidule',
            'account_type': 'asset_fixed'
        })

    # This method return a list of transactions with the given dates
    # amount for each transaction is 10
    def create_transactions(self, dates):
        transactions = []
        for date in dates:
            transactions.append({
                'online_transaction_identifier': self.transaction_id,
                'date': fields.Date.from_string(date),
                'payment_ref': 'transaction_' + str(self.transaction_id),
                'amount': 10,
            })
            self.transaction_id += 1
        return transactions

    def create_transaction_partner(self, date=False, partner_id=False, partner_info=False):
        tr = {
            'online_transaction_identifier': self.transaction_id,
            'date': fields.Date.from_string(date),
            'payment_ref': 'transaction_p',
            'amount': 50,
        }
        if partner_id:
            tr['partner_id'] = partner_id
        if partner_info:
            tr['online_partner_information'] = partner_info
        self.transaction_id += 1
        return [tr]

    def assertDate(self, date1, date2):
        if isinstance(date1, str):
            date1 = fields.Date.from_string(date1)
        if isinstance(date2, str):
            date2 = fields.Date.from_string(date2)
        self.assertEqual(date1, date2)

    def reconncile_st_lines(self, st_lines):
        for line in st_lines:
            wizard = self.env['bank.rec.widget'].with_context(default_st_line_id=line.id).new({})
            auto_balance_line = wizard.line_ids.filtered(lambda x: x.flag == 'auto_balance')
            form = WizardForm(wizard)
            form._view['modifiers']['todo_command']['invisible'] = False
            form.todo_command = f'mount_line_in_edit,{auto_balance_line.index}'
            form.form_name = "toto"
            form.form_account_id = self.account
            wizard = form.save()
            wizard.button_validate(async_action=False)

    # Tests
    def test_creation_initial_sync_statement(self):
        transactions = self.create_transactions(['2016-01-01', '2016-01-03'])
        self.online_account.balance = 1000
        self.bnk_stmt_line._online_sync_bank_statement(transactions, self.online_account)
        # Since ending balance is 1000$ and we only have 20$ of transactions and that it is the first statement
        # it should create a statement before this one with the initial statement line
        created_st_lines = self.bnk_stmt_line.search([('journal_id', '=', self.bank_journal.id)], order='date asc')
        self.assertEqual(len(created_st_lines), 3, 'Should have created an initial bank statement line and two for the synchronization')
        transactions = self.create_transactions(['2016-01-05'])
        self.online_account.balance = 2000
        self.bnk_stmt_line._online_sync_bank_statement(transactions, self.online_account)
        created_st_lines = self.bnk_stmt_line.search([('journal_id', '=', self.bank_journal.id)], order='date asc')
        self.assertRecordValues(
            created_st_lines,
            [
                {'date': fields.Date.from_string('2015-12-31'), 'amount': 980.0},
                {'date': fields.Date.from_string('2016-01-01'), 'amount': 10.0},
                {'date': fields.Date.from_string('2016-01-03'), 'amount': 10.0},
                {'date': fields.Date.from_string('2016-01-05'), 'amount': 10.0},
            ]
        )

    def test_creation_initial_sync_statement_bis(self):
        transactions = self.create_transactions(['2016-01-01', '2016-01-03'])
        self.online_account.balance = 20
        self.bnk_stmt_line._online_sync_bank_statement(transactions, self.online_account)
        # Since ending balance is 20$ and we only have 20$ of transactions and that it is the first statement
        # it should NOT create a initial statement before this one
        created_st_lines = self.bnk_stmt_line.search([('journal_id', '=', self.bank_journal.id)], order='date asc')
        self.assertRecordValues(
            created_st_lines,
            [
                {'date': fields.Date.from_string('2016-01-01'), 'amount': 10.0},
                {'date': fields.Date.from_string('2016-01-03'), 'amount': 10.0},
            ]
        )
        self.assertEqual(len(created_st_lines), 2, 'Should have two lines')

    def test_creation_initial_sync_statement_invert_sign(self):
        transactions = self.create_transactions(['2016-01-01', '2016-01-03'])
        self.online_account.balance = -20
        self.online_account.inverse_transaction_sign = True
        self.online_account.inverse_balance_sign = True
        self.bnk_stmt_line._online_sync_bank_statement(transactions, self.online_account)
        # Since ending balance is 1000$ and we only have 20$ of transactions and that it is the first statement
        # it should create a statement before this one with the initial statement line
        created_st_lines = self.bnk_stmt_line.search([('journal_id', '=', self.bank_journal.id)], order='date asc')
        self.assertEqual(len(created_st_lines), 2, 'Should have created two bank statement lines for the synchronization')
        transactions = self.create_transactions(['2016-01-05'])
        self.online_account.balance = -30
        self.bnk_stmt_line._online_sync_bank_statement(transactions, self.online_account)
        created_st_lines = self.bnk_stmt_line.search([('journal_id', '=', self.bank_journal.id)], order='date asc')
        self.assertRecordValues(
            created_st_lines,
            [
                {'date': fields.Date.from_string('2016-01-01'), 'amount': -10.0},
                {'date': fields.Date.from_string('2016-01-03'), 'amount': -10.0},
                {'date': fields.Date.from_string('2016-01-05'), 'amount': -10.0},
            ]
        )

    def test_assign_partner_auto_bank_stmt(self):
        self.assertEqual(self.partner_a.online_partner_information, False)
        transactions = self.create_transaction_partner(date='2016-01-01', partner_info='test_vendor_name')
        self.online_account.balance = 50
        self.bnk_stmt_line._online_sync_bank_statement(transactions, self.online_account)
        created_st_line = self.bnk_stmt_line.search([('journal_id', '=', self.bank_journal.id)], order='date desc', limit=1)
        # Ensure that bank statement has no partner set
        self.assertFalse(created_st_line.partner_id)
        # Assign partner
        created_st_line.partner_id = self.partner_a
        # process the bank statement line
        self.reconncile_st_lines(created_st_line)
        # Check that partner has correct vendor_name associated to it
        self.assertEqual(self.partner_a.online_partner_information, 'test_vendor_name')

        # Create another statement with a partner
        transactions = self.create_transaction_partner(date='2016-01-02', partner_id=self.partner_a.id, partner_info='test_other_vendor_name')
        self.online_account.balance = 100
        self.bnk_stmt_line._online_sync_bank_statement(transactions, self.online_account)
        created_st_line = self.bnk_stmt_line.search([('journal_id', '=', self.bank_journal.id)], order='date desc', limit=1)
        # Ensure that statement has a partner set
        self.assertEqual(created_st_line.partner_id, self.partner_a)
        # Validate and check that partner has no vendor_information set
        self.reconncile_st_lines(created_st_line)
        self.assertEqual(self.partner_a.online_partner_information, False)

        # Create another statement with same information
        transactions = self.create_transaction_partner(date='2016-01-03', partner_id=self.partner_a.id)
        self.online_account.balance = 150
        self.bnk_stmt_line._online_sync_bank_statement(transactions, self.online_account)
        created_st_line = self.bnk_stmt_line.search([('journal_id', '=', self.bank_journal.id)], order='date desc', limit=1)
        # Ensure that statement has a partner set
        self.assertEqual(created_st_line.partner_id, self.partner_a)
        # Validate and check that partner has no vendor_name set
        self.reconncile_st_lines(created_st_line)
        self.assertEqual(self.partner_a.online_partner_information, False)

    def test_automatic_journal_assignment(self):
        def create_online_account(name, link_id, iban, currency_id):
            return self.env['account.online.account'].create({
                'name': name,
                'account_online_link_id': link_id,
                'account_number': iban,
                'currency_id' : currency_id,
            })

        def create_bank_account(account_number, partner_id):
            return self.env['res.partner.bank'].create({
                'acc_number': account_number,
                'partner_id': partner_id,
            })

        def create_journal(name, journal_type, code, currency_id=False, bank_account_id=False):
            return self.env['account.journal'].create({
                'name': name,
                'type': journal_type,
                'code': code,
                'currency_id': currency_id,
                'bank_account_id': bank_account_id,
            })

        eur_currency = self.env.ref('base.EUR')
        bank_account_1 = create_bank_account('BE48485444456727', self.company_data['company'].partner_id.id)
        bank_account_2 = create_bank_account('Coucou--.BE619-.--5-----4856342317yocestmoi-', self.company_data['company'].partner_id.id)
        bank_account_3 = create_bank_account('BE23798242487491', self.company_data['company'].partner_id.id)

        bank_journal_with_account_eur = create_journal('Bank with account', 'bank', 'BJWA1', eur_currency.id, bank_account_1.id)
        bank_journal_with_badly_written_account_eur = create_journal('Bank with errors in account name', 'bank', 'BJWA2', eur_currency.id, bank_account_2.id)
        bank_journal_with_account_usd = create_journal('Bank with account USD', 'bank', 'BJWA3', self.env.ref('base.USD').id, bank_account_3.id)
        bank_journal_simple = create_journal('Bank without account and currency', 'bank', 'BJWOA2')

        online_account_1 = create_online_account('OnlineAccount1', self.link_account.id, 'BE48485444456727', eur_currency.id)
        online_account_2 = create_online_account('OnlineAccount2', self.link_account.id, 'BE61954856342317', eur_currency.id)
        online_account_3 = create_online_account('OnlineAccount3', self.link_account.id, 'BE23798242487491', eur_currency.id)
        online_account_4 = create_online_account('OnlineAccount4', self.link_account.id, 'BE31812561129155', eur_currency.id)
        online_accounts = [online_account_1, online_account_2, online_account_3, online_account_4]

        account_link_journal_wizard = self.env['account.link.journal'].create({
            'number_added': len(online_accounts),
            'account_ids': [Command.create({
                'online_account_id': online_account.id,
                'journal_id': online_account.journal_ids[0].id if online_account.journal_ids else None
            }) for online_account in online_accounts]
        })
        with patch('odoo.addons.account_online_synchronization.models.account_online.AccountOnlineLink.action_fetch_transactions', return_value=True):
            account_link_journal_wizard.sync_now()

        self.assertEqual(online_account_1.id, bank_journal_with_account_eur.account_online_account_id.id, "The wizard should have linked the first online account to the journal with the same account.")
        self.assertEqual(online_account_2.id, bank_journal_with_badly_written_account_eur.account_online_account_id.id, "The wizard should have linked the second online account to the journal with the same account, after sanitization.")
        self.assertNotEqual(online_account_3.id, bank_journal_with_account_usd.account_online_account_id.id, "As the currency in the journal is different than the one specified in the online account, they should not be linked to each other.")
        self.assertEqual(online_account_3.id, bank_journal_simple.account_online_account_id.id, "The next empty journal should be linked to the online account, when no journal exists with the corresponding currency and account number.")
        previously_created_journals = [bank_journal_with_account_eur, bank_journal_with_badly_written_account_eur, bank_journal_with_account_usd, bank_journal_simple, self.bank_journal]
        self.assertTrue(online_account_4.journal_ids and online_account_4.journal_ids[0] not in previously_created_journals, "A new journal should be created for the remaining online account.")

    def test_multiple_transaction_identifier_fetched(self):
        # Ensure that if we receive twice the same transaction within the same call, it won't be created twice
        transactions = self.create_transactions(['2016-01-01', '2016-01-03'])
        # Add first transactions to the list again
        transactions.append(transactions[0])
        self.bnk_stmt_line._online_sync_bank_statement(transactions, self.online_account)
        bnk_stmt_lines = self.bnk_stmt_line.search([('online_transaction_identifier', '!=', False), ('journal_id', '=', self.bank_journal.id)])
        self.assertEqual(len(bnk_stmt_lines), 2, 'Should only have created two lines')

    @patch('odoo.addons.account_online_synchronization.models.account_online.requests')
    def test_fetch_transactions_reauth(self, patched_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'error': {
                'code': 300,
                'data': {'mode': 'updateCredentials'},
            },
        }
        patched_request.post.return_value = mock_response
        self.online_account.account_online_link_id.state = 'connected'
        res = self.online_account.account_online_link_id._fetch_transactions()
        self.assertTrue('account_online_identifier' in res.get('params', {}).get('includeParam', {}))

    @patch('odoo.addons.account_online_synchronization.models.account_online.requests')
    def test_fetch_receive_error_message(self, patched_request):
        # We want to test that when we receive an error, a redirectWarning with the correct parameter is thrown
        # However the method _log_information that we need to test for that is performing a rollback as it needs
        # to save the message error on the record as well (so it rollback, save message, commit, raise error).
        # So in order to test the method, we need to use a "test cursor".
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'error': {
                'code': 400,
                'message': 'Shit Happened',
                'data': {
                    'exception_type': 'random',
                    'message': 'This kind of things can happen.',
                    'error_reference': 'abc123',
                    'provider_type': 'theonlyone',
                    'redirect_warning_url': 'odoo_support',
                },

            },
        }
        patched_request.post.return_value = mock_response

        generated_url = 'https://www.odoo.com/help?stage=bank_sync&summary=Bank+sync+error+ref%3A+abc123+-+Provider%3A+theonlyone+-+Client+ID%3A+False&description=ClientID%3A+False%0AInstitution%3A+Test+Bank%0AError+Reference%3A+abc123%0AError+Message%3A+This+kind+of+things+can+happen.%0A'
        return_act_url = {
            'type': 'ir.actions.act_url',
            'url': generated_url
        }
        body_generated_url = generated_url.replace('&', '&amp;') #in post_message, & has been escaped to &amp;
        message_body = f"""<p>This kind of things can happen.

If you've already opened a ticket for this issue, don't report it again: a support agent will contact you shortly.<br>You can contact Odoo support <a href=\"{body_generated_url}\">Here</a></p>"""

        # flush and clear everything for the new "transaction"
        self.env.invalidate_all()
        try:
            self.env.registry.enter_test_mode(self.cr)
            with self.env.registry.cursor() as test_cr:
                test_env = self.env(cr=test_cr)
                test_link_account = self.link_account.with_env(test_env)
                test_link_account.state = 'connected'

                # this hand-written self.assertRaises() does not roll back self.cr,
                # which is necessary below to inspect the message being posted
                try:
                    test_link_account._fetch_odoo_fin('/testthisurl')
                except Exception as exception:
                    self.assertIsInstance(exception, RedirectWarning)
                    self.assertEqual(exception.args[0], "This kind of things can happen.\n\nIf you've already opened a ticket for this issue, don't report it again: a support agent will contact you shortly.")
                    self.assertEqual(exception.args[1], return_act_url)
                    self.assertEqual(exception.args[2], 'Report issue')
                else:
                    self.fail("Expected RedirectWarning not raised")
                self.assertEqual(test_link_account.message_ids[0].body, message_body)
        finally:
            self.env.registry.leave_test_mode()
