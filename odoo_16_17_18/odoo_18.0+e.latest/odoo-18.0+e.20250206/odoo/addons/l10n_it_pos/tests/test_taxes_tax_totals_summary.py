from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.account.tests.test_taxes_tax_totals_summary import TestTaxesTaxTotalsSummary
from odoo.addons.point_of_sale.tests.test_frontend import TestPointOfSaleHttpCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'post_install_l10n')
class TestTaxesTaxTotalsSummaryL10nItPos(TestPointOfSaleHttpCommon, TestTaxesTaxTotalsSummary):

    @classmethod
    @AccountTestInvoicingCommon.setup_country('it')
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_a.name = "AAAAAA"  # The POS only load the first 100 partners
        cls.main_pos_config.it_fiscal_printer_ip = "0.0.0.0"

    def _jsonify_document_line(self, document, index, line):
        # EXTENDS 'account'
        values = super()._jsonify_document_line(document, index, line)
        values['l10n_it_epson_printer'] = line['l10n_it_epson_printer']
        return values

    def _test_taxes_l10n_it_epson_printer(self):
        tax = self.percent_tax(22.0, price_include_override='tax_excluded', tax_group_id=self.tax_groups[0].id)
        document_params = self.init_document(
            lines=[
                {'price_unit': 5.16, 'quantity': 3.0, 'tax_ids': tax, 'l10n_it_epson_printer': True},
            ],
        )
        expected_values = {
            'same_tax_base': True,
            'currency_id': self.currency.id,
            'base_amount_currency': 15.49,
            'tax_amount_currency': 3.41,
            'total_amount_currency': 18.9,
            'subtotals': [
                {
                    'name': "Untaxed Amount",
                    'base_amount_currency': 15.49,
                    'tax_amount_currency': 3.41,
                    'tax_groups': [
                        {
                            'id': self.tax_groups[0].id,
                            'base_amount_currency': 15.49,
                            'tax_amount_currency': 3.41,
                            'display_base_amount_currency': 15.49,
                        },
                    ],
                },
            ],
        }
        yield 1, self.populate_document(document_params), expected_values

        document_params = self.init_document(
            lines=[
                {'price_unit': 2.20, 'quantity': 3.0, 'tax_ids': tax, 'l10n_it_epson_printer': True},
            ],
        )
        expected_values = {
            'same_tax_base': True,
            'currency_id': self.currency.id,
            'base_amount_currency': 6.59,
            'tax_amount_currency': 1.45,
            'total_amount_currency': 8.04,
            'subtotals': [
                {
                    'name': "Untaxed Amount",
                    'base_amount_currency': 6.59,
                    'tax_amount_currency': 1.45,
                    'tax_groups': [
                        {
                            'id': self.tax_groups[0].id,
                            'base_amount_currency': 6.59,
                            'tax_amount_currency': 1.45,
                            'display_base_amount_currency': 6.59,
                        },
                    ],
                },
            ],
        }
        yield 2, self.populate_document(document_params), expected_values

        document_params = self.init_document(
            lines=[
                {'price_unit': 5.16, 'quantity': 3.0, 'tax_ids': tax, 'l10n_it_epson_printer': True},
                {'price_unit': 2.20, 'quantity': 3.0, 'tax_ids': tax, 'l10n_it_epson_printer': True},
            ],
        )
        expected_values = {
            'same_tax_base': True,
            'currency_id': self.currency.id,
            'base_amount_currency': 22.08,
            'tax_amount_currency': 4.86,
            'total_amount_currency': 26.94,
            'subtotals': [
                {
                    'name': "Untaxed Amount",
                    'base_amount_currency': 22.08,
                    'tax_amount_currency': 4.86,
                    'tax_groups': [
                        {
                            'id': self.tax_groups[0].id,
                            'base_amount_currency': 22.08,
                            'tax_amount_currency': 4.86,
                            'display_base_amount_currency': 22.08,
                        },
                    ],
                },
            ],
        }
        yield 3, self.populate_document(document_params), expected_values

    def test_taxes_l10n_it_epson_printer_generic_helpers(self):
        for test_index, document, expected_values in self._test_taxes_l10n_it_epson_printer():
            with self.subTest(test_index=test_index):
                self.assert_tax_totals_summary(document, expected_values)
        self._run_js_tests()

    def test_taxes_l10n_it_epson_printer_pos(self):
        # Create the missing products.
        products_map = {}
        for test_index, document, expected_values in self._test_taxes_l10n_it_epson_printer():
            for line in document['lines']:
                line['_product_key'] = (line['price_unit'], line['tax_ids'])
                if line['_product_key'] not in products_map:
                    products_map[line['_product_key']] = self.env['product.product'].create({
                        'name': f"product_{str(line['price_unit']).replace('.', '_')}_{line['tax_ids'].amount}",
                        'available_in_pos': True,
                        'list_price': line['price_unit'],
                        'taxes_id': [Command.set(line['tax_ids'].ids)],
                        'pos_categ_ids': [Command.set(self.pos_desk_misc_test.ids)],
                    })

        with self.with_new_session(user=self.pos_user) as session:
            self.start_pos_tour('test_taxes_l10n_it_epson_printer_pos')
            orders = self.env['pos.order'].search([('session_id', '=', session.id)])
            for order, (test_index, document, expected_values) in zip(orders, self._test_taxes_l10n_it_epson_printer()):
                self.assertRecordValues(order, [{
                    'amount_tax': expected_values['tax_amount_currency'],
                    'amount_total': expected_values['total_amount_currency'],
                    'amount_paid': expected_values['total_amount_currency'],
                }])
                self.assertRecordValues(order.account_move, [{
                    'amount_untaxed': expected_values['base_amount_currency'],
                    'amount_tax': expected_values['tax_amount_currency'],
                    'amount_total': expected_values['total_amount_currency'],
                }])
