# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# pylint: disable=C0326
from base64 import b64decode
from datetime import datetime
from freezegun import freeze_time

from odoo.addons.account_reports.tests.common import TestAccountReportsCommon
from odoo.tests import tagged
from odoo import fields


@tagged('post_install_l10n', 'post_install', '-at_install')
class LuxembourgElectronicReportTest(TestAccountReportsCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref='l10n_lu.lu_2011_chart_1'):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.company_data['company'].write({
            'ecdf_prefix': '1234AB',
            'vat': 'LU12345613',
            'matr_number': '12345678900',
        })

        cls.out_invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner_a.id,
            'invoice_date': '2019-01-01',
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'line_1',
                    'price_unit': 1000.0,
                    'quantity': 1.0,
                    'account_id': cls.company_data['default_account_revenue'].id,
                    'tax_ids': [(6, 0, cls.company_data['default_tax_sale'].ids)],
                }),
            ],
        })

        cls.in_invoice = cls.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': cls.partner_a.id,
            'invoice_date': '2019-01-01',
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'line_1',
                    'price_unit': 800.0,
                    'quantity': 1.0,
                    'account_id': cls.company_data['default_account_expense'].id,
                    'tax_ids': [(6, 0, cls.company_data['default_tax_purchase'].ids)],
                }),
            ],
        })

        (cls.out_invoice + cls.in_invoice).action_post()
    #
    def _filter_zero_lines(self, lines):
        filtered_lines = []
        for line in lines:
            bal_col = line['columns'][0]
            if not bal_col.get('is_zero'):
                filtered_lines.append(line)
        return filtered_lines

    def test_balance_sheet(self):
        report = self.env.ref('l10n_lu_reports.account_financial_report_l10n_lu_bs')
        options = self._generate_options(report, fields.Date.from_string('2019-01-01'), fields.Date.from_string('2019-12-31'))

        self.assertLinesValues(
            self._filter_zero_lines(report._get_lines(options)),
            #   Name                                            Balance
            [   0,                                              1],
            [
                ('D. Current assets',                           1306.0),
                ('II. Debtors',                                 1306.0),
                ('1. Trade debtors',                            1170.0),
                ('a) becoming due and payable within one year', 1170.0),
                ('4. Other debtors',                            136.0),
                ('a) becoming due and payable within one year', 136.0),
                ('TOTAL (ASSETS)',                              1306.0),
                ('A. Capital and reserves',                      200.0),
                ('VI. Profit or loss for the financial year',    200.0),
                ('C. Creditors',                                 1106.0),
                ('4. Trade creditors',                           936.0),
                ('a) becoming due and payable within one year',  936.0),
                ('8. Other creditors',                           170.0),
                ('a) Tax authorities',                           170.0),
                ('TOTAL (CAPITAL, RESERVES AND LIABILITIES)',    1306.0),
            ],
        )

    def test_profit_and_loss(self):
        report = self.env.ref('l10n_lu_reports.account_financial_report_l10n_lu_pl')
        options = self._generate_options(report, fields.Date.from_string('2019-01-01'), fields.Date.from_string('2019-12-31'))

        self.assertLinesValues(
            self._filter_zero_lines(report._get_lines(options)),
            #   Name                                                                    Balance
            [   0,                                                                      1],
            [
                ('1. Net turnover',                                                     1000.0),
                ('5. Raw materials and consumables and other external expenses',        -800.0),
                ('a) Raw materials and consumables',                                    -800.0),
                ('16. Profit or loss after taxation',                                    200.0),
                ('18. Profit or loss for the financial year',                            200.0),
            ],
        )

    @freeze_time('2019-12-31')
    def test_generate_xml(self):
        first_tax = self.env['account.tax'].search([('name', '=', '17-P-G'), ('company_id', '=', self.company_data['company'].id)], limit=1)
        second_tax = self.env['account.tax'].search([('name', '=', '14-P-S'), ('company_id', '=', self.company_data['company'].id)], limit=1)

        # Create and post a move with two move lines to get some data in the report
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'journal_id': self.company_data['default_journal_purchase'].id,
            'partner_id': self.partner_a.id,
            'invoice_date': '2019-11-12',
            'date': '2019-11-12',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_a.id,
                'quantity': 1.0,
                'name': 'product test 1',
                'price_unit': 150,
                'tax_ids': first_tax.ids,
            }), (0, 0, {
                'product_id': self.product_b.id,
                'quantity': 1.0,
                'name': 'product test 2',
                'price_unit': 100,
                'tax_ids': second_tax.ids,
            })]
        })
        move.action_post()

        report = self.env.ref('l10n_lu.tax_report')
        options = report._get_options()

        # Add the filename in the options, which is initially done by the get_report_filename() method
        now_datetime = datetime.now()
        file_ref_data = {
            'ecdf_prefix': self.env.company.ecdf_prefix,
            'datetime': now_datetime.strftime('%Y%m%dT%H%M%S%f')[:-4]
        }
        options['filename'] = '{ecdf_prefix}X{datetime}'.format(**file_ref_data)

        expected_xml = """
        <eCDFDeclarations xmlns="http://www.ctie.etat.lu/2011/ecdf">
            <FileReference>%s</FileReference>
            <eCDFFileVersion>2.0</eCDFFileVersion>
            <Interface>MODL5</Interface>
            <Agent>
                <MatrNbr>12345678900</MatrNbr>
                <RCSNbr>NE</RCSNbr>
                <VATNbr>12345613</VATNbr>
            </Agent>
            <Declarations>
                <Declarer>
                    <MatrNbr>12345678900</MatrNbr>
                    <RCSNbr>NE</RCSNbr>
                    <VATNbr>12345613</VATNbr>
                    <Declaration model="1" type="TVA_DECM" language="EN">
                        <Year>2019</Year>
                        <Period>11</Period>
                        <FormData>
                                <NumericField id="012">0,00</NumericField>
                                <NumericField id="021">0,00</NumericField>
                                <NumericField id="457">0,00</NumericField>
                                <NumericField id="014">0,00</NumericField>
                                <NumericField id="018">0,00</NumericField>
                                <NumericField id="423">0,00</NumericField>
                                <NumericField id="419">0,00</NumericField>
                                <NumericField id="022">0,00</NumericField>
                                <NumericField id="037">0,00</NumericField>
                                <NumericField id="033">0,00</NumericField>
                                <NumericField id="046">0,00</NumericField>
                                <NumericField id="051">0,00</NumericField>
                                <NumericField id="056">0,00</NumericField>
                                <NumericField id="152">0,00</NumericField>
                                <NumericField id="065">0,00</NumericField>
                                <NumericField id="407">0,00</NumericField>
                                <NumericField id="409">0,00</NumericField>
                                <NumericField id="436">0,00</NumericField>
                                <NumericField id="463">0,00</NumericField>
                                <NumericField id="765">0,00</NumericField>
                                <NumericField id="410">0,00</NumericField>
                                <NumericField id="462">0,00</NumericField>
                                <NumericField id="464">0,00</NumericField>
                                <NumericField id="766">0,00</NumericField>
                                <NumericField id="767">0,00</NumericField>
                                <NumericField id="768">0,00</NumericField>
                                <NumericField id="076">0,00</NumericField>
                                <NumericField id="093">39,50</NumericField>
                                <NumericField id="458">39,50</NumericField>
                                <NumericField id="097">0,00</NumericField>
                                <NumericField id="102">39,50</NumericField>
                                <NumericField id="103">0,00</NumericField>
                                <NumericField id="104">39,50</NumericField>
                                <NumericField id="105">-39,50</NumericField>
                                <Choice id="204">0</Choice>
                                <Choice id="205">1</Choice>
                                <NumericField id="403">0</NumericField>
                                <NumericField id="418">0</NumericField>
                                <NumericField id="453">0</NumericField>
                                <NumericField id="042">0,00</NumericField>
                                <NumericField id="416">0,00</NumericField>
                                <NumericField id="417">0,00</NumericField>
                                <NumericField id="451">0,00</NumericField>
                                <NumericField id="452">0,00</NumericField>
                        </FormData>
                    </Declaration>
                </Declarer>
            </Declarations>
        </eCDFDeclarations>
        """ % options['filename']

        wizard = self.env['l10n_lu.generate.tax.report'].create({})
        new_context = self.env.context.copy()
        new_context['report_generation_options'] = options
        wizard.with_context(new_context).get_xml()
        declaration_to_compare = b64decode(wizard.report_data.decode("utf-8"))[38:]

        self.assertXmlTreeEqual(
            self.get_xml_tree_from_string(declaration_to_compare),
            self.get_xml_tree_from_string(expected_xml)
        )

    @freeze_time('2019-12-31')
    def test_generate_bs_pnl_xml(self):
        report = self.env.ref('l10n_lu_reports.account_financial_report_l10n_lu_bs')
        options = report._get_options()
        # Add the filename in the options, which is initially done by the get_report_filename() method
        now_datetime = datetime.now()
        file_ref_data = {
            'ecdf_prefix': self.env.company.ecdf_prefix,
            'datetime': now_datetime.strftime('%Y%m%dT%H%M%S%f')[:-4]
        }
        options['unposted_in_period'] = False
        options['filename'] = '{ecdf_prefix}X{datetime}'.format(**file_ref_data)

        expected_xml = """
            <eCDFDeclarations xmlns="http://www.ctie.etat.lu/2011/ecdf">
                <FileReference>%s</FileReference>
                <eCDFFileVersion>2.0</eCDFFileVersion>
                <Interface>MODL5</Interface>
                <Agent>
                    <MatrNbr>12345678900</MatrNbr>
                    <RCSNbr>NE</RCSNbr>
                    <VATNbr>12345613</VATNbr>
                </Agent>
                <Declarations>
                    <Declarer>
                        <MatrNbr>12345678900</MatrNbr>
                        <RCSNbr>NE</RCSNbr>
                        <VATNbr>12345613</VATNbr>
                            <Declaration type="CA_COMPP" model="1" language="EN">
                                <Year>2019</Year>
                                <Period>1</Period>
                                <FormData>
                                    <TextField id="01">01/01/2019</TextField>
                                    <TextField id="02">31/12/2019</TextField>
                                    <TextField id="03">EUR</TextField>
                                    <NumericField id="701">1000,00</NumericField>
                                    <NumericField id="671">-800,00</NumericField>
                                    <NumericField id="601">-800,00</NumericField>
                                    <NumericField id="667">200,00</NumericField>
                                    <NumericField id="669">200,00</NumericField>
                                </FormData>
                            </Declaration>
                            <Declaration type="CA_BILAN" model="1" language="EN">
                                <Year>2019</Year>
                                <Period>1</Period>
                                <FormData>
                                    <TextField id="01">01/01/2019</TextField>
                                    <TextField id="02">31/12/2019</TextField>
                                    <TextField id="03">EUR</TextField>
                                    <NumericField id="151">1306,00</NumericField>
                                    <NumericField id="163">1306,00</NumericField>
                                    <NumericField id="165">1170,00</NumericField>
                                    <NumericField id="167">1170,00</NumericField>
                                    <NumericField id="183">136,00</NumericField>
                                    <NumericField id="185">136,00</NumericField>
                                    <NumericField id="201">1306,00</NumericField>
                                    <NumericField id="202">0,00</NumericField>
                                    <NumericField id="301">200,00</NumericField>
                                    <NumericField id="321">200,00</NumericField>
                                    <NumericField id="435">1106,00</NumericField>
                                    <NumericField id="367">936,00</NumericField>
                                    <NumericField id="369">936,00</NumericField>
                                    <NumericField id="451">170,00</NumericField>
                                    <NumericField id="393">170,00</NumericField>
                                    <NumericField id="405">1306,00</NumericField>
                                    <NumericField id="406">0,00</NumericField>
                                </FormData>
                            </Declaration>
                            <Declaration type="CA_PLANCOMPTA" model="1" language="EN">
                                <Year>2019</Year>
                                <Period>1</Period>
                                <FormData>
                                    <TextField id="01">01/01/2019</TextField>
                                    <TextField id="02">31/12/2019</TextField>
                                    <TextField id="03">EUR</TextField>
                                    <NumericField id="0565">1170,00</NumericField>
                                    <NumericField id="0567">1170,00</NumericField>
                                    <NumericField id="0569">1170,00</NumericField>
                                    <NumericField id="0657">136,00</NumericField>
                                    <NumericField id="0659">136,00</NumericField>
                                    <NumericField id="0687">136,00</NumericField>
                                    <NumericField id="0689">136,00</NumericField>
                                    <NumericField id="0691">136,00</NumericField>
                                    <NumericField id="0812">936,00</NumericField>
                                    <NumericField id="0814">936,00</NumericField>
                                    <NumericField id="0816">936,00</NumericField>
                                    <NumericField id="0818">936,00</NumericField>
                                    <NumericField id="0908">170,00</NumericField>
                                    <NumericField id="0910">170,00</NumericField>
                                    <NumericField id="0954">170,00</NumericField>
                                    <NumericField id="0956">170,00</NumericField>
                                    <NumericField id="0958">170,00</NumericField>
                                    <NumericField id="1113">800,00</NumericField>
                                    <NumericField id="1115">800,00</NumericField>
                                    <NumericField id="1852">1000,00</NumericField>
                                    <NumericField id="1862">1000,00</NumericField>
                                    <NumericField id="1112">-0,00</NumericField>
                                    <NumericField id="2258">200,00</NumericField>
                                    <NumericField id="0162">200,00</NumericField>
                                    <NumericField id="0158">200,00</NumericField>
                                    <NumericField id="2939">1,00</NumericField>
                                </FormData>
                            </Declaration>
                    </Declarer>
                </Declarations>
            </eCDFDeclarations>
        """ % options['filename']

        wizard = self.env['l10n_lu.generate.accounts.report'].create({})
        new_context = self.env.context.copy()
        new_context['report_generation_options'] = options
        wizard.with_context(new_context).get_xml()
        declaration_to_compare = b64decode(wizard.report_data.decode("utf-8"))[38:]

        self.assertXmlTreeEqual(
            self.get_xml_tree_from_string(declaration_to_compare),
            self.get_xml_tree_from_string(expected_xml)
        )
