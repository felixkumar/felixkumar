# -*- coding: utf-8 -*-
# pylint: disable=bad-whitespace
from odoo import fields, Command
from odoo.tests import tagged

from odoo.addons.account_reports.tests.common import TestAccountReportsCommon


@tagged('post_install', 'post_install_l10n', '-at_install')
class TestDiot(TestAccountReportsCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref='l10n_mx.mx_coa'):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.purchase_taxes = cls._get_purchase_taxes()

        cls.partner_a.write({'country_id': cls.env.ref('base.mx').id, 'l10n_mx_type_of_operation': '85', 'vat': 'XAXX010101000'})
        cls.partner_b.write({'country_id': cls.env.ref('base.us').id, 'l10n_mx_type_of_operation': '85'})

    @classmethod
    def _get_purchase_taxes(cls):
        taxes = cls.env['account.tax']
        for i in [1, 2, 7, 8, 13, 14, 16]:
            taxes += cls.env.ref(f'l10n_mx.{cls.env.company.id}_tax{i}')
        return taxes

    def test_diot_report(self):
        date_invoice = '2022-07-01'
        moves_vals = []
        for i, tax in enumerate(self.purchase_taxes):
            for partner in (self.partner_a, self.partner_b):
                moves_vals += [
                    {
                        'move_type': 'in_invoice',
                        'partner_id': partner.id,
                        'invoice_payment_term_id': False,
                        'invoice_date': date_invoice,
                        'date': date_invoice,
                        'invoice_line_ids': [Command.create({
                            'name': f'test {tax.amount}',
                            'quantity': 1,
                            'price_unit': 10 + 1 * i,
                            'tax_ids': [Command.set(tax.ids)],
                        })],
                    },
                    {
                        'move_type': 'in_refund',
                        'partner_id': partner.id,
                        'invoice_payment_term_id': False,
                        'invoice_date': date_invoice,
                        'date': date_invoice,
                        'invoice_line_ids': [Command.create({
                            'name': f'test {tax.amount}',
                            'quantity': 1,
                            'price_unit': 10 + 2 * i,
                            'tax_ids': [Command.set(tax.ids)],
                        })],
                    },
                ]

        moves = self.env['account.move'].create(moves_vals)
        moves.action_post()

        for move in moves:
            self.env['account.payment.register'].with_context(active_model='account.move', active_ids=move.ids).create({
                'payment_date': date_invoice,
                'journal_id': self.company_data['default_journal_bank'].id,
                'amount': move.amount_total,
            })._create_payments()

        self.assertTrue(all(m.payment_state in ('paid', 'in_payment') for m in moves))

        diot_report = self.env.ref('l10n_mx_reports.diot_report')

        options = self._generate_options(diot_report, fields.Date.from_string('2022-01-01'), fields.Date.from_string('2022-12-31'))
        options['unfold_all'] = True

        self.assertLinesValues(
            diot_report._get_lines(options),
            # 3rd p code, op type code,      vat number,   country,nationality,  16%, 16% non-cred,   8%, 8% non-cred, 16% imp, 0% paid, exempt, withheld, refund
            [       1,               2,               3,         4,          5,    6,            7,    8,           9,      10,      11,     12,       13,     14],
            [
                (  "",              "",              "",        "",         "", 30.0,           "", 32.0,          "",      "",    28.0,     "",    -1.26,   9.92),

                ("04",            "85", "XAXX010101000",      "MX",  "Mexican", 15.0,           "", 16.0,          "",      "",    14.0,     "",    -0.63,   4.96),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",       "",   1.76),
                (  "",              "",              "",        "",         "",   "",           "", 16.0,          "",      "",      "",     "",       "",     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",       "",    3.2),
                (  "",              "",              "",        "",         "", 15.0,           "",   "",          "",      "",      "",     "",       "",     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",    14.0,     "",       "",     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",    -1.71,     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",     1.39,     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",    -1.49,     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",     1.28,     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",    -1.20,     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",     1.10,     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",    -0.40,     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",     0.40,     ""),
                ("04",            "85", "XAXX010101000",      "MX",  "Mexican", 15.0,           "", 16.0,          "",      "",    14.0,     "",    -0.63,   4.96),

                ("05",            "85",              "",      "US", "American", 15.0,           "", 16.0,          "",      "",    14.0,     "",    -0.63,   4.96),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",       "",   1.76),
                (  "",              "",              "",        "",         "",   "",           "", 16.0,          "",      "",      "",     "",       "",     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",       "",    3.2),
                (  "",              "",              "",        "",         "", 15.0,           "",   "",          "",      "",      "",     "",       "",     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",    14.0,     "",       "",     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",    -1.71,     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",     1.39,     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",    -1.49,     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",     1.28,     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",    -1.20,     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",     1.10,     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",    -0.40,     ""),
                (  "",              "",              "",        "",         "",   "",           "",   "",          "",      "",      "",     "",     0.40,     ""),
                ("05",            "85",              "",      "US", "American", 15.0,           "", 16.0,          "",      "",    14.0,     "",    -0.63,   4.96),

                (  "",              "",              "",        "",         "", 30.0,           "", 32.0,          "",      "",    28.0,     "",    -1.26,  9.92),
            ]
        )

        self.assertEqual(
            self.env[diot_report.custom_handler_model_name].action_get_diot_txt(options)['file_content'].decode(),
            "04|85|XAXX010101000|||||15|||||16||||||||14||-1|5|\n"
            "05|85|||partnerb|US|American|15|||||16||||||||14||-1|5|"
        )

        self.assertEqual(
            self.env[diot_report.custom_handler_model_name].action_get_dpiva_txt(options)['file_content'].decode(),
            "|1.0|2022|MES|Enero|1|1|||13|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|04|85|XAXX010101000|||||15|||16||||||||14||-1|5|\n"
            "|1.0|2022|MES|Enero|1|1|||13|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|05|85|||partnerb|US|American|15|||16||||||||14||-1|5|"
        )

        # Testing a Bill with 2+ taxes on the same line
        multi_taxes = self.env['account.tax']
        multi_taxes += self.env.ref(f'l10n_mx.{self.env.company.id}_tax14') # IVA(16%) COMPRAS
        multi_taxes += self.env.ref(f'l10n_mx.{self.env.company.id}_tax1') # RET IVA FLETES 4%
        multi_taxes += self.env.ref(f'l10n_mx.{self.env.company.id}_tax2') # RET IVA ARRENDAMIENTO 10%

        multi_tax_line_move = self.env['account.move'].create({
             'move_type': 'in_invoice',
             'partner_id': self.partner_a.id,
             'invoice_payment_term_id': False,
             'invoice_date': date_invoice,
             'date': date_invoice,
             'invoice_line_ids': [Command.create({
                 'name': 'test multi tax',
                 'quantity': 1,
                 'price_unit': 100,
                 'tax_ids': [Command.set(multi_taxes.ids)],
             })]
        })
        multi_tax_line_move.action_post()

        self.env['account.payment.register'].with_context(active_model='account.move', active_ids=multi_tax_line_move.ids).create({
            'payment_date': date_invoice,
            'journal_id': self.company_data['default_journal_bank'].id,
            'amount': multi_tax_line_move.amount_total,
        })._create_payments()

        options = self._generate_options(diot_report, fields.Date.from_string('2022-01-01'), fields.Date.from_string('2022-12-31'))

        self.assertLinesValues(
            diot_report._get_lines(options),
            # 3rd p code, op type code,      vat number,   country, nationality,    16%, 16% non-cred,   8%, 8% non-cred, 16% imp, 0% paid, exempt, withheld,   refund
            [       1,               2,               3,         4,           5,      6,            7,    8,           9,      10,      11,     12,       13,      14],
            [
                (  "",              "",              "",        "",          "",  130.0,           "", 32.0,          "",      "",    28.0,     "",    12.74,    9.92),
                ("04",            "85", "XAXX010101000",      "MX",   "Mexican",  115.0,           "", 16.0,          "",      "",    14.0,     "",    13.37,    4.96),
                ("05",            "85",              "",      "US",  "American",   15.0,           "", 16.0,          "",      "",    14.0,     "",    -0.63,    4.96),
                (  "",              "",              "",        "",          "",  130.0,           "", 32.0,          "",      "",    28.0,     "",    12.74,    9.92),
            ]
        )

    def test_diot_report_with_refund(self):
        date_invoice = '2022-07-01'
        tax = self.purchase_taxes.filtered(lambda tax: tax.amount == 16)

        move = self.env['account.move'].create({
            'move_type': 'in_refund',
            'partner_id': self.partner_a.id,
            'invoice_date': date_invoice,
            'date': date_invoice,
            'invoice_line_ids': [Command.create({
                'name': f'test {tax.amount}',
                'quantity': 1,
                'price_unit': 100,
                'tax_ids': [Command.set(tax.ids)],
            })]
        })
        move.action_post()

        self.env['account.payment.register'].with_context(active_model='account.move', active_ids=move.ids).create({
                'payment_date': date_invoice,
                'journal_id': self.company_data['default_journal_bank'].id,
                'amount': move.amount_total,
            })._create_payments()

        self.assertTrue(move.payment_state in ('paid', 'in_payment'))

        diot_report = self.env.ref('l10n_mx_reports.diot_report')

        options = self._generate_options(diot_report, fields.Date.from_string('2022-01-01'), fields.Date.from_string('2022-12-31'))

        self.assertLinesValues(
            diot_report._get_lines(options),
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
            [
                # pylint: disable=C0326
                (  "",   "",              "",   "",         "", "","", "","","", "","", "", 16.0),
                ("04", "85", "XAXX010101000", "MX",  "Mexican", "","", "","","", "","", "", 16.0),
                (  "",   "",              "",   "",         "", "","", "","","", "","", "", 16.0),
            ]
        )

        self.assertEqual(
            self.env[diot_report.custom_handler_model_name].action_get_diot_txt(options)['file_content'].decode(),
            "04|85|XAXX010101000|||||||||||||||||||||16|")

        self.assertEqual(
            self.env[diot_report.custom_handler_model_name].action_get_dpiva_txt(options)['file_content'].decode(),
            "|1.0|2022|MES|Enero|1|1|||1|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|04|85|XAXX010101000|||||||||||||||||||16|")
