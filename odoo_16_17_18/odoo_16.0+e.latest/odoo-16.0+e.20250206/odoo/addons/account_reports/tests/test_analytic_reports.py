from odoo import Command
from odoo.tests import tagged

from .common import TestAccountReportsCommon


@tagged('post_install', '-at_install')
class TestAnalyticReport(TestAccountReportsCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.env.user.groups_id += cls.env.ref(
            'analytic.group_analytic_accounting')
        cls.report = cls.env.ref('account_reports.profit_and_loss')
        cls.report.write({'filter_analytic': True})

        cls.analytic_plan_parent = cls.env['account.analytic.plan'].create({
            'name': 'Plan Parent',
            'company_id': False,
        })
        cls.analytic_plan_child = cls.env['account.analytic.plan'].create({
            'name': 'Plan Child',
            'parent_id': cls.analytic_plan_parent.id,
            'company_id': False,
        })

        cls.analytic_account_parent = cls.env['account.analytic.account'].create({
            'name': 'Account 1',
            'plan_id': cls.analytic_plan_parent.id
        })
        cls.analytic_account_parent_2 = cls.env['account.analytic.account'].create({
            'name': 'Account 2',
            'plan_id': cls.analytic_plan_parent.id
        })
        cls.analytic_account_parent_3 = cls.env['account.analytic.account'].create({
            'name': 'Account 4',
            'plan_id': cls.analytic_plan_parent.id
        })
        cls.analytic_account_child = cls.env['account.analytic.account'].create({
            'name': 'Account 3',
            'plan_id': cls.analytic_plan_child.id
        })

    def test_report_group_by_analytic_plan(self):

        out_invoice = self.env['account.move'].create([{
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'date': '2019-05-01',
            'invoice_date': '2019-05-01',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'price_unit': 200.0,
                    'analytic_distribution': {
                        self.analytic_account_parent.id: 100,
                    },
                }),
                Command.create({
                    'product_id': self.product_b.id,
                    'price_unit': 200.0,
                    'analytic_distribution': {
                        self.analytic_account_child.id: 100,
                    },
                }),
            ]
        }])
        out_invoice.action_post()

        options = self._generate_options(
            self.report,
            '2019-01-01',
            '2019-12-31',
            default_options={
                'analytic_plans_groupby': [self.analytic_plan_parent.id, self.analytic_plan_child.id],
            }
        )

        lines = self.report._get_lines(options)

        self.assertLinesValues(
            # pylint: disable=bad-whitespace
            lines,
            [   0,                       1,            2],
            [
                ['Net Profit',           400.00,       200.00],
                ['Income',               400.00,       200.00],
                ['Gross Profit',         400.00,       200.00],
                ['Operating Income',     400.00,       200.00],
                ['Cost of Revenue',      '',           ''],
                ['Total Gross Profit',   400.00,       200.00],
                ['Other Income',         '',           ''],
                ['Total Income',         400.00,       200.00],
                ['Expenses',             '',           ''],
                ['Expenses',             '',           ''],
                ['Depreciation',         '',           ''],
                ['Total Expenses',       '',           ''],
            ],
            currency_map={
                1: {'currency': self.env.company.currency_id},
                2: {'currency': self.env.company.currency_id},
            },
        )

    def test_report_analytic_filter(self):

        out_invoice = self.env['account.move'].create([{
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'date': '2023-02-01',
            'invoice_date': '2023-02-01',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'price_unit': 1000.0,
                    'analytic_distribution': {
                        self.analytic_account_parent.id: 100,
                    },
                })
            ]
        }])
        out_invoice.action_post()

        options = self._generate_options(
            self.report,
            '2023-01-01',
            '2023-12-31',
            default_options={
                'analytic_accounts': [self.analytic_account_parent.id],
            }
        )

        self.assertLinesValues(
            # pylint: disable=C0326
            self.report._get_lines(options),
            [   0,                                 1],
            [
                ['Net Profit',               1000.00],
                ['Income',                   1000.00],
                ['Gross Profit',             1000.00],
                ['Operating Income',         1000.00],
                ['Cost of Revenue',               ''],
                ['Total Gross Profit',       1000.00],
                ['Other Income',                  ''],
                ['Total Income',             1000.00],
                ['Expenses',                      ''],
                ['Expenses',                      ''],
                ['Depreciation',                  ''],
                ['Total Expenses',                ''],
            ],
            currency_map={
                1: {'currency': self.env.company.currency_id},
                2: {'currency': self.env.company.currency_id},
            },
        )

        # Set the unused analytic account in filter, as no move is
        # using this account, the column should be empty
        options['analytic_accounts'] = [self.analytic_account_child.id]

        self.assertLinesValues(
            # pylint: disable=C0326
            self.report._get_lines(options),
            [   0,                               1],
            [
                ['Net Profit',                  ''],
                ['Income',                      ''],
                ['Gross Profit',                ''],
                ['Operating Income',            ''],
                ['Cost of Revenue',             ''],
                ['Total Gross Profit',          ''],
                ['Other Income',                ''],
                ['Total Income',                ''],
                ['Expenses',                    ''],
                ['Expenses',                    ''],
                ['Depreciation',                ''],
                ['Total Expenses',              ''],
            ],
            currency_map={
                1: {'currency': self.env.company.currency_id},
                2: {'currency': self.env.company.currency_id},
            },
        )

    def test_report_audit_analytic_filter(self):
        out_invoice = self.env['account.move'].create([{
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'date': '2023-02-01',
            'invoice_date': '2023-02-01',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'price_unit': 1000.0,
                    'analytic_distribution': {
                        self.analytic_account_parent.id: 100,
                    },
                }),
                Command.create({
                    'product_id': self.product_a.id,
                    'price_unit': 500.0,
                    'analytic_distribution': {
                        self.analytic_account_child.id: 100,
                    },
                }),
            ],
        }])
        out_invoice.action_post()

        options = self._generate_options(
            self.report,
            '2023-01-01',
            '2023-12-31',
            default_options={
                'analytic_accounts': [self.analytic_account_parent.id],
            }
        )

        lines = self.report._get_lines(options)

        report_line = self.report.line_ids[0]
        report_line_dict = next(x for x in lines if x['name'] == report_line.name)

        action_dict = self.report.action_audit_cell(
            options,
            self._get_audit_params_from_report_line(options, report_line, report_line_dict),
        )

        audited_lines = self.env['account.move.line'].search(action_dict['domain'])
        self.assertEqual(audited_lines, out_invoice.invoice_line_ids[0], "Only the line with the parent account should be shown")

    def test_report_analytic_groupby_and_filter(self):
        """
        Test that the analytic filter is applied on the groupby columns
        """

        out_invoice = self.env['account.move'].create([{
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'date': '2023-02-01',
            'invoice_date': '2023-02-01',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'price_unit': 1000.0,
                    'analytic_distribution': {
                        self.analytic_account_parent.id: 40,
                        self.analytic_account_child.id: 60,
                    },
                })
            ]
        }])
        out_invoice.action_post()

        # Test with only groupby
        options = self._generate_options(
            self.report,
            '2023-01-01',
            '2023-12-31',
            default_options={
                'analytic_accounts_groupby': [self.analytic_account_parent.id, self.analytic_account_child.id],
            }
        )

        self.assertLinesValues(
            # pylint: disable=C0326
            self.report._get_lines(options),
            [   0,                               1,            2,               3],
            [
                ['Net Profit',              400.00,       600.00,         1000.00],
                ['Income',                  400.00,       600.00,         1000.00],
                ['Gross Profit',            400.00,       600.00,         1000.00],
                ['Operating Income',        400.00,       600.00,         1000.00],
                ['Cost of Revenue',             '',           '',              ''],
                ['Total Gross Profit',      400.00,       600.00,         1000.00],
                ['Other Income',                '',           '',              ''],
                ['Total Income',            400.00,       600.00,         1000.00],
                ['Expenses',                    '',           '',              ''],
                ['Expenses',                    '',           '',              ''],
                ['Depreciation',                '',           '',              ''],
                ['Total Expenses',              '',           '',              ''],
            ],
            currency_map={
                1: {'currency': self.env.company.currency_id},
                2: {'currency': self.env.company.currency_id},
            },
        )

        # Adding analytic filter for the two analytic accounts used on the invoice line
        # The two groupby columns should still be filled
        options['analytic_accounts'] = [self.analytic_account_parent.id, self.analytic_account_child.id]

        self.assertLinesValues(
            # pylint: disable=C0326
            self.report._get_lines(options),
            [   0,                               1,            2,           3],
            [
                ['Net Profit',              400.00,       600.00,     1000.00],
                ['Income',                  400.00,       600.00,     1000.00],
                ['Gross Profit',            400.00,       600.00,     1000.00],
                ['Operating Income',        400.00,       600.00,     1000.00],
                ['Cost of Revenue',             '',           '',          ''],
                ['Total Gross Profit',      400.00,       600.00,     1000.00],
                ['Other Income',                '',           '',          ''],
                ['Total Income',            400.00,       600.00,     1000.00],
                ['Expenses',                    '',           '',          ''],
                ['Expenses',                    '',           '',          ''],
                ['Depreciation',                '',           '',          ''],
                ['Total Expenses',              '',           '',          ''],
            ],
            currency_map={
                1: {'currency': self.env.company.currency_id},
                2: {'currency': self.env.company.currency_id},
            },
        )
        # Keep only first analytic account on filter, the groupby column
        # for this account should still be filled, unlike the other
        options['analytic_accounts'] = [self.analytic_account_parent.id]

        self.assertLinesValues(
            # pylint: disable=C0326
            self.report._get_lines(options),
            [   0,                          1,            2,              3],
            [
                ['Net Profit',              400.00,       '',         1000.00],
                ['Income',                  400.00,       '',         1000.00],
                ['Gross Profit',            400.00,       '',         1000.00],
                ['Operating Income',        400.00,       '',         1000.00],
                ['Cost of Revenue',             '',       '',              ''],
                ['Total Gross Profit',      400.00,       '',         1000.00],
                ['Other Income',                '',       '',              ''],
                ['Total Income',            400.00,       '',         1000.00],
                ['Expenses',                    '',       '',              ''],
                ['Expenses',                    '',       '',              ''],
                ['Depreciation',                '',       '',              ''],
                ['Total Expenses',              '',       '',              ''],
            ],
            currency_map={
                1: {'currency': self.env.company.currency_id},
                2: {'currency': self.env.company.currency_id},
            },
        )

        # Keep only first analytic account on filter, the groupby column
        # for this account should still be filled, unlike the other
        options['analytic_accounts'] = [self.analytic_account_child.id]

        self.assertLinesValues(
            # pylint: disable=C0326
            self.report._get_lines(options),
            [   0,                               1,        2,               3],
            [
                ['Net Profit',                  '',   600.00,         1000.00],
                ['Income',                      '',   600.00,         1000.00],
                ['Gross Profit',                '',   600.00,         1000.00],
                ['Operating Income',            '',   600.00,         1000.00],
                ['Cost of Revenue',             '',       '',              ''],
                ['Total Gross Profit',          '',   600.00,         1000.00],
                ['Other Income',                '',       '',              ''],
                ['Total Income',                '',   600.00,         1000.00],
                ['Expenses',                    '',       '',              ''],
                ['Expenses',                    '',       '',              ''],
                ['Depreciation',                '',       '',              ''],
                ['Total Expenses',              '',       '',              ''],
            ],
            currency_map={
                1: {'currency': self.env.company.currency_id},
                2: {'currency': self.env.company.currency_id},
            },
        )

        # Set an unused analytic account in filter, all the columns
        # should be empty, as no move is using this account
        options['analytic_accounts'] = [self.analytic_account_parent_2.id]

        self.assertLinesValues(
            # pylint: disable=C0326
            self.report._get_lines(options),
            [   0,                               1,        2,               3],
            [
                ['Net Profit',                  '',       '',              ''],
                ['Income',                      '',       '',              ''],
                ['Gross Profit',                '',       '',              ''],
                ['Operating Income',            '',       '',              ''],
                ['Cost of Revenue',             '',       '',              ''],
                ['Total Gross Profit',          '',       '',              ''],
                ['Other Income',                '',       '',              ''],
                ['Total Income',                '',       '',              ''],
                ['Expenses',                    '',       '',              ''],
                ['Expenses',                    '',       '',              ''],
                ['Depreciation',                '',       '',              ''],
                ['Total Expenses',              '',       '',              ''],
            ],
            currency_map={
                1: {'currency': self.env.company.currency_id},
                2: {'currency': self.env.company.currency_id},
            },
        )

    def test_analytic_groupby_with_horizontal_groupby(self):
        horizontal_group = self.env['account.report.horizontal.group'].create({
            'name': 'Horizontal Group Products',
            'report_ids': [self.report.id],
            'rule_ids': [
                Command.create({
                    'field_name': 'product_id',
                    'domain': f"[('id', 'in', {(self.product_a + self.product_b).ids})]",
                }),
            ],
        })

        out_invoice = self.env['account.move'].create([{
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'date': '2024-07-01',
            'invoice_date': '2024-07-01',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'price_unit': 100.0,
                    'analytic_distribution': {
                        self.analytic_account_parent.id: 100,
                    },
                }),
                Command.create({
                    'product_id': self.product_b.id,
                    'price_unit': 500.0,
                    'analytic_distribution': {
                        self.analytic_account_parent_2.id: 80,
                        self.analytic_account_parent_3.id: -10,
                    },
                }),
            ]
        }])
        out_invoice.action_post()

        options = self._generate_options(
            self.report,
            '2024-01-01',
            '2024-12-31',
            default_options={
                'analytic_accounts_groupby': [self.analytic_account_parent.id, self.analytic_account_parent_2.id, self.analytic_account_parent_3.id],
                'selected_horizontal_group_id': horizontal_group.id,
            }
        )

        self.assertLinesValues(
            self.report._get_lines(options),
            #   Horizontal groupby      [          Product A          ]     [            Product B            ]
            #   Analytic groupby        A1      A2      A3      Balance     A1      A2          A3      Balance
            [    0,                     1,      2,      3,      4,          5,      6,          7,      8],
            [
                ['Net Profit',          100.00, '',     '',     100.00,     '',     400.00,     -50.00, 500.00],
                ['Income',              100.00, '',     '',     100.00,     '',     400.00,     -50.00, 500.00],
                ['Gross Profit',        100.00, '',     '',     100.00,     '',     400.00,     -50.00, 500.00],
                ['Operating Income',    100.00, '',     '',     100.00,     '',     400.00,     -50.00, 500.00],
                ['Cost of Revenue',     '',     '',     '',     '',         '',     '',         '',     ''],
                ['Total Gross Profit',  100.00, '',     '',     100.00,     '',     400.00,     -50.00, 500.00],
                ['Other Income',        '',     '',     '',     '',         '',     '',         '',     ''],
                ['Total Income',        100.00, '',     '',     100.00,     '',     400.00,     -50.00, 500.00],
                ['Expenses',            '',     '',     '',     '',         '',     '',         '',     ''],
                ['Expenses',            '',     '',     '',     '',         '',     '',         '',     ''],
                ['Depreciation',        '',     '',     '',     '',         '',     '',         '',     ''],
                ['Total Expenses',      '',     '',     '',     '',         '',     '',         '',     ''],
            ],
        )
