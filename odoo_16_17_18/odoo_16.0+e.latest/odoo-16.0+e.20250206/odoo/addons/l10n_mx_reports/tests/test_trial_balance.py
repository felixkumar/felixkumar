# -*- coding: utf-8 -*-
# pylint: disable=C0326
from odoo.addons.account_reports.tests.common import TestAccountReportsCommon

from odoo import fields, Command
from odoo.tests import tagged
from odoo.tools import misc
from odoo.exceptions import RedirectWarning

import base64
import datetime

from freezegun import freeze_time
from pytz import timezone

@tagged('post_install_l10n', 'post_install', '-at_install')
class TestL10nMXTrialBalanceReport(TestAccountReportsCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref='l10n_mx.mx_coa'):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.frozen_today = datetime.datetime(year=2021, month=1, day=1, hour=0, minute=0, second=0, tzinfo=timezone('utc'))

        cls.company_data['company'].country_id = cls.env.ref('base.mx')
        cls.company_data['company'].vat = 'EKU9003173C9'

        # The test certificate may be expired. However, since the tests are only testing the xml
        # values without sending anything, we don't really care about the certificate validity.
        with freeze_time(cls.frozen_today):
            cls.certificate = cls.env['l10n_mx_edi.certificate'].create({
                'content': base64.encodebytes(misc.file_open('l10n_mx_edi/demo/pac_credentials/certificate.cer', 'rb').read()),
                'key': base64.encodebytes(misc.file_open('l10n_mx_edi/demo/pac_credentials/certificate.key', 'rb').read()),
                'password': '12345678a',
            })
        cls.certificate.write({
            'date_start': '2016-01-01 01:00:00',
            'date_end': '2022-01-01 01:00:00',
        })
        cls.company_data['company'].l10n_mx_edi_certificate_ids = cls.certificate

        # Entries in 2020 to test initial balance
        cls.move_2020_01 = cls.env['account.move'].create({
            'move_type': 'entry',
            'date': fields.Date.to_date('2020-01-01'),
            'journal_id': cls.company_data['default_journal_misc'].id,
            'line_ids': [
                Command.create({'debit': 1000.0, 'credit': 0.0, 'account_id': cls.company_data['default_account_payable'].id}),
                Command.create({'debit': 0.0, 'credit': 1000.0, 'account_id': cls.company_data['default_account_revenue'].id}),
            ]
        })

        cls.move_2020_02 = cls.env['account.move'].create({
            'move_type': 'entry',
            'date': fields.Date.to_date('2020-02-01'),
            'journal_id': cls.company_data['default_journal_misc'].id,
            'line_ids': [
                Command.create(
                    {'debit': 500.0, 'credit': 0.0, 'account_id': cls.company_data['default_account_expense'].id}),
                Command.create(
                    {'debit': 0.0, 'credit': 500.0, 'account_id': cls.company_data['default_account_revenue'].id}),
            ]
        })
        (cls.move_2020_01 + cls.move_2020_02).action_post()

        # Entries in 2021 to test report for a specific financial year
        cls.move_2021_01 = cls.env['account.move'].create({
            'move_type': 'entry',
            'date': fields.Date.to_date('2021-06-01'),
            'journal_id': cls.company_data['default_journal_misc'].id,
            'line_ids': [
                Command.create(
                    {'debit': 250.0, 'credit': 0.0, 'account_id': cls.company_data['default_account_expense'].id}),
                Command.create(
                    {'debit': 0.0, 'credit': 250.0, 'account_id': cls.company_data['default_account_revenue'].id}),
            ]
        })

        cls.move_2021_02 = cls.env['account.move'].create({
            'move_type': 'entry',
            'date': fields.Date.to_date('2021-08-01'),
            'journal_id': cls.company_data['default_journal_misc'].id,
            'line_ids': [
                Command.create(
                    {'debit': 75.0, 'credit': 0.0, 'account_id': cls.company_data['default_account_payable'].id}),
                Command.create(
                    {'debit': 0.0, 'credit': 75.0, 'account_id': cls.company_data['default_account_revenue'].id}),
            ]
        })
        (cls.move_2021_01 + cls.move_2021_02).action_post()

        # Special cases: codes with extra levels from the default COA and dotted account names
        cls.extra_deep_code = cls.env["account.account"].create(
            {
                "name": "Extra deep code",
                "account_type": "liability_current",
                "code": "205.06.01.001",
                "reconcile": True,
            }
        )

        cls.dotted_name = cls.env["account.account"].create(
            {
                "name": "Dotted name C.V.",
                "account_type": "liability_current",
                "code": "205.06.02",
                "reconcile": True,
            }
        )

        cls.extra_deep_code_move = cls.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.to_date("2021-06-01"),
                "journal_id": cls.company_data["default_journal_misc"].id,
                "line_ids": [
                    Command.create(
                        {
                            "debit": 400.0,
                            "credit": 0.0,
                            "account_id": cls.dotted_name.id,
                        }
                    ),
                    Command.create(
                        {
                            "debit": 0.0,
                            "credit": 400.0,
                            "account_id": cls.extra_deep_code.id,
                        }
                    ),
                ],
            }
        )

        cls.dotted_name_move = cls.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.to_date("2021-06-01"),
                "journal_id": cls.company_data["default_journal_misc"].id,
                "line_ids": [
                    Command.create(
                        {
                            "debit": 50.0,
                            "credit": 0.0,
                            "account_id": cls.extra_deep_code.id,
                        }
                    ),
                    Command.create(
                        {
                            "debit": 0.0,
                            "credit": 50.0,
                            "account_id": cls.dotted_name.id,
                        }
                    ),
                ],
            }
        )
        (cls.extra_deep_code_move + cls.dotted_name_move).action_post()

        cls.report = cls.env.ref('account_reports.trial_balance_report')

    @classmethod
    def setup_company_data(cls, company_name, chart_template=None, **kwargs):
        # OVERRIDE account
        mx_country_id = cls.env.ref('base.mx').id
        return super().setup_company_data(company_name, chart_template=chart_template, country_id=mx_country_id, **kwargs)

    def test_generate_coa_xml(self):
        """ This test will generate a COA report and verify that every
            account with an entry in the selected period has been there.

            CodAgrup corresponds to Account Group code
            NumCta corresponds to Account Group code
            Desc corresponds to Account Group Name
            Nivel corresponds to Hierarchy Level
            Natur corresponds to type of account (Debit or Credit)

            Available values for "Natur":
            D = Debit Account
            A = Credit Account

            Unaffected Earnings account is not include in this report because
            it's custom Odoo account.
        """
        expected_coa_xml = b"""<?xml version='1.0' encoding='utf-8'?>
        <catalogocuentas:Catalogo xmlns:catalogocuentas="http://www.sat.gob.mx/esquemas/ContabilidadE/1_3/CatalogoCuentas" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.sat.gob.mx/esquemas/ContabilidadE/1_3/CatalogoCuentas http://www.sat.gob.mx/esquemas/ContabilidadE/1_3/CatalogoCuentas/CatalogoCuentas_1_3.xsd" Version="1.3" RFC="EKU9003173C9" Mes="01" Anio="2021" Sello="___ignore___" Certificado="___ignore___" noCertificado="___ignore___">
            <catalogocuentas:Ctas CodAgrup="101" NumCta="101" Desc="Caja" Nivel="1" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="101.01" NumCta="101.01" Desc="Caja y efectivo" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="102" NumCta="102" Desc="Bancos" Nivel="1" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="102.01" NumCta="102.01" Desc="Bancos nacionales" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="102.02" NumCta="102.02" Desc="Bancos extranjeros" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="105" NumCta="105" Desc="Clientes" Nivel="1" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="105.01" NumCta="105.01" Desc="Clientes nacionales" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="107" NumCta="107" Desc="Deudores diversos" Nivel="1" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="107.05" NumCta="107.05" Desc="Otros deudores diversos" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="108" NumCta="108" Desc="Estimaci&#243;n de cuentas incobrables" Nivel="1" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="108.01" NumCta="108.01" Desc="Estimaci&#243;n de cuentas incobrables nacional" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="108.02" NumCta="108.02" Desc="Estimaci&#243;n de cuentas incobrables extranjero" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="115" NumCta="115" Desc="Inventario" Nivel="1" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="115.01" NumCta="115.01" Desc="Inventario" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="115.02" NumCta="115.02" Desc="Materia prima y materiales" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="115.03" NumCta="115.03" Desc="Producci&#243;n en proceso" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="115.04" NumCta="115.04" Desc="Productos terminados" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="115.05" NumCta="115.05" Desc="Mercanc&#237;as en tr&#225;nsito" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="115.06" NumCta="115.06" Desc="Mercanc&#237;as en poder de terceros" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="118" NumCta="118" Desc="Impuestos acreditables pagados" Nivel="1" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="118.01" NumCta="118.01" Desc="IVA acreditable pagado" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="118.03" NumCta="118.03" Desc="IEPS acreditable pagado" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="119" NumCta="119" Desc="Impuestos acreditables por pagar" Nivel="1" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="119.01" NumCta="119.01" Desc="IVA pendiente de pago" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="119.03" NumCta="119.03" Desc="IEPS pendiente de pago" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="120" NumCta="120" Desc="Anticipo a proveedores" Nivel="1" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="120.01" NumCta="120.01" Desc="Anticipo a proveedores nacional" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="120.02" NumCta="120.02" Desc="Anticipo a proveedores extranjero" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="201" NumCta="201" Desc="Proveedores" Nivel="1" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="201.01" NumCta="201.01" Desc="Proveedores nacionales" Nivel="2" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="205" NumCta="205" Desc="Acreedores diversos a corto plazo" Nivel="1" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="205.06" NumCta="205.06" Desc="Otros acreedores diversos a corto plazo" Nivel="2" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="206" NumCta="206" Desc="Anticipo de cliente" Nivel="1" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="206.01" NumCta="206.01" Desc="Anticipo de cliente nacional" Nivel="2" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="206.02" NumCta="206.02" Desc="Anticipo de cliente extranjero" Nivel="2" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="206.05" NumCta="206.05" Desc="Otros anticipos de clientes" Nivel="2" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="208" NumCta="208" Desc="Impuestos trasladados cobrados" Nivel="1" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="208.01" NumCta="208.01" Desc="IVA trasladado cobrado" Nivel="2" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="208.02" NumCta="208.02" Desc="IEPS trasladado cobrado" Nivel="2" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="209" NumCta="209" Desc="Impuestos trasladados no cobrados" Nivel="1" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="209.01" NumCta="209.01" Desc="IVA trasladado no cobrado" Nivel="2" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="209.02" NumCta="209.02" Desc="IEPS trasladado no cobrado" Nivel="2" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="216" NumCta="216" Desc="Impuestos retenidos" Nivel="1" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="216.03" NumCta="216.03" Desc="Impuestos retenidos de ISR por arrendamiento" Nivel="2" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="216.04" NumCta="216.04" Desc="Impuestos retenidos de ISR por servicios profesionales" Nivel="2" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="216.10" NumCta="216.10" Desc="Impuestos retenidos de IVA" Nivel="2" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="302" NumCta="302" Desc="Patrimonio" Nivel="1" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="302.01" NumCta="302.01" Desc="Patrimonio" Nivel="2" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="304" NumCta="304" Desc="Resultado de ejercicios anteriores" Nivel="1" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="304.01" NumCta="304.01" Desc="Utilidad de ejercicios anteriores" Nivel="2" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="305" NumCta="305" Desc="Resultado del ejercicio" Nivel="1" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="305.01" NumCta="305.01" Desc="Utilidad del ejercicio" Nivel="2" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="401" NumCta="401" Desc="Ingresos" Nivel="1" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="401.01" NumCta="401.01" Desc="Ventas y/o servicios gravados a la tasa general" Nivel="2" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="501" NumCta="501" Desc="Costo de venta y/o servicio" Nivel="1" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="501.01" NumCta="501.01" Desc="Costo de venta" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="601" NumCta="601" Desc="Gastos generales" Nivel="1" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="601.84" NumCta="601.84" Desc="Otros gastos generales" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="701" NumCta="701" Desc="Gastos financieros" Nivel="1" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="701.01" NumCta="701.01" Desc="P&#233;rdida cambiaria" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="702" NumCta="702" Desc="Productos financieros" Nivel="1" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="702.01" NumCta="702.01" Desc="Utilidad cambiaria" Nivel="2" Natur="A"/>
            <catalogocuentas:Ctas CodAgrup="811" NumCta="811" Desc="Utilidad o p&#233;rdida fiscal en venta y/o baja de activo fijo" Nivel="1" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="811.01" NumCta="811.01" Desc="Utilidad o p&#233;rdida fiscal en venta y/o baja de activo fijo" Nivel="2" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="899" NumCta="899" Desc="Otras cuentas de orden" Nivel="1" Natur="D"/>
            <catalogocuentas:Ctas CodAgrup="899.01" NumCta="899.01" Desc="Otras cuentas de orden" Nivel="2" Natur="D"/>
        </catalogocuentas:Catalogo>
        """

        options = self._generate_options(self.report, '2021-01-01', '2021-12-31')
        with freeze_time(self.frozen_today):
            coa_report = self.env[self.report.custom_handler_model_name].with_context(skip_xsd=True).action_l10n_mx_generate_coa_sat_xml(options)['file_content']
        self.assertXmlTreeEqual(
            self.get_xml_tree_from_string(coa_report),
            self.get_xml_tree_from_string(expected_coa_xml),
        )

    def test_generate_sat_xml(self):
        """ This test will generate a SAT report and verify that
        every account present in the trial balance (except unaffected
        earnings account) is present in the xml.

        SaldoIni corresponds to Initial Balance
        SaldoFin corresponds to End Balance
        Debe corresponds to Debit in the current period
        Haber corresponds to Credit in the current period
        NumCta corresponds to Account Group code
        """
        expected_sat_xml = b"""<?xml version='1.0' encoding='utf-8'?>
        <BCE:Balanza xmlns:BCE="http://www.sat.gob.mx/esquemas/ContabilidadE/1_3/BalanzaComprobacion" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.sat.gob.mx/esquemas/ContabilidadE/1_3/BalanzaComprobacion http://www.sat.gob.mx/esquemas/ContabilidadE/1_3/BalanzaComprobacion/BalanzaComprobacion_1_3.xsd" Version="1.3" RFC="EKU9003173C9" Mes="01" Anio="2021" TipoEnvio="N" Sello="___ignore___" Certificado="___ignore___" noCertificado="___ignore___">
            <BCE:Ctas Debe="75.00" NumCta="201" Haber="0.00" SaldoFin="-1075.00" SaldoIni="-1000.00"/>
            <BCE:Ctas Debe="75.00" NumCta="201.01" Haber="0.00" SaldoFin="-1075.00" SaldoIni="-1000.00"/>
            <BCE:Ctas Debe="450.00" NumCta="205" Haber="450.00" SaldoFin="0.00" SaldoIni="0.00"/>
            <BCE:Ctas Debe="450.00" NumCta="205.06" Haber="450.00" SaldoFin="0.00" SaldoIni="0.00"/>
            <BCE:Ctas Debe="0.00" NumCta="401" Haber="325.00" SaldoFin="325.00" SaldoIni="0.00"/>
            <BCE:Ctas Debe="0.00" NumCta="401.01" Haber="325.00" SaldoFin="325.00" SaldoIni="0.00"/>
            <BCE:Ctas Debe="250.00" NumCta="601" Haber="0.00" SaldoFin="250.00" SaldoIni="0.00"/>
            <BCE:Ctas Debe="250.00" NumCta="601.84" Haber="0.00" SaldoFin="250.00" SaldoIni="0.00"/>
        </BCE:Balanza>
        """

        options = self._generate_options(self.report, '2021-01-01', '2021-12-31')
        with freeze_time(self.frozen_today):
            sat_report = self.env[self.report.custom_handler_model_name].with_context(skip_xsd=True).action_l10n_mx_generate_sat_xml(options)['file_content']
        self.assertXmlTreeEqual(
            self.get_xml_tree_from_string(sat_report),
            self.get_xml_tree_from_string(expected_sat_xml),
        )

    def test_generate_coa_xml_without_tag(self):
        """This test verifies that all accounts present in the trial balance have a Debit or a Credit balance account tag"""
        self.company_data['default_account_payable'].tag_ids = [Command.clear()]
        options = self._generate_options(self.report, '2021-01-01', '2021-12-31')
        with self.assertRaises(RedirectWarning):
            self.env[self.report.custom_handler_model_name].action_l10n_mx_generate_coa_sat_xml(options)

    def test_generate_coa_xml_with_too_much_tag(self):
        """This test verifies that all accounts present in the trial balance have exactly one Debit or Credit balance account tag"""
        self.company_data['default_account_payable'].tag_ids = self.env.ref('l10n_mx.tag_debit_balance_account') + self.env.ref('l10n_mx.tag_credit_balance_account')
        options = self._generate_options(self.report, '2021-01-01', '2021-12-31')
        with self.assertRaises(RedirectWarning):
            self.env[self.report.custom_handler_model_name].action_l10n_mx_generate_coa_sat_xml(options)

    def test_generate_coa_xml_with_too_much_tag_in_group(self):
        """This test verifies that all accounts present in the same group have exactly one Debit or Credit balance account tag"""
        self.company_data['default_account_receivable'].tag_ids = self.env.ref('l10n_mx.tag_credit_balance_account')
        options = self._generate_options(self.report, '2021-01-01', '2021-12-31')
        with self.assertRaises(RedirectWarning):
            self.env[self.report.custom_handler_model_name].action_l10n_mx_generate_coa_sat_xml(options)

    def test_generate_coa_xml_with_too_much_tag_in_parent(self):
        """This test verifies that all account groups in the same parent have the same account tag"""
        self.company_data['default_account_tax_purchase'].tag_ids = self.env.ref('l10n_mx.tag_credit_balance_account')
        options = self._generate_options(self.report, '2021-01-01', '2021-12-31')
        with self.assertRaises(RedirectWarning):
            self.env[self.report.custom_handler_model_name].action_l10n_mx_generate_coa_sat_xml(options)

    def test_mx_trial_balance(self):
        """ This test will test the Mexican Trial Balance (with and without the hierarchy) """
        # Testing the report without hierarchy
        options = self._generate_options(self.report, '2021-01-01', '2021-12-31', {'hierarchy': False, 'unfold_all': True})
        self.assertLinesValues(
            self.report._get_lines(options),
            [   0,                                                            1,         2,         3,       4,        5,         6],
            [
                ('201.01.01 Proveedores nacionales',                          1000.0,    '',        75.0,    '',       1075.0,    ''),
                ('205.06.01.001 Extra deep code',                             '',        '',        50.0,    400.0,    '',        350.0),
                ('205.06.02 Dotted name C.V.',                                '',        '',        400.0,   50.0,     350.0,     ''),
                ('401.01.01 Ventas y/o servicios gravados a la tasa general', '',        '',        '',      325.0,    '',        325.0),
                ('601.84.01 Otros gastos generales',                          '',        '',        250.0,   '',       250.0,     ''),
                ('999999 Undistributed Profits/Losses',                       '',        1000.0,    '',      '',       '',        1000.0),
                ('Total',                                                     1000.0,    1000.0,    775.0,   775.0,    1675.0,    1675.0),
            ],
        )

        # Testing the report with hierarchy
        options['hierarchy'] = True
        self.assertLinesValues(
            self.report._get_lines(options),
            [   0,                                                            1,         2,         3,       4,        5,         6],
            [
                ('2 Pasivos',                                                 1000.0,    '',        525.0,   450.0,    1425.0,    350.0),
                ('201 Proveedores',                                           1000.0,    '',        75.0,    '',       1075.0,    ''),
                ('201.01 Proveedores nacionales',                             1000.0,    '',        75.0,    '',       1075.0,    ''),
                ('201.01.01 Proveedores nacionales',                          1000.0,    '',        75.0,    '',       1075.0,    ''),
                ('205 Acreedores diversos a corto plazo',                     '',        '',        450.0,   450.0,    350.0,     350.0),
                ('205.06 Otros acreedores diversos a corto plazo',            '',        '',        450.0,   450.0,    350.0,     350.0),
                ('205.06.01.001 Extra deep code',                             '',        '',        50.0,    400.0,    '',        350.0),
                ('205.06.02 Dotted name C.V.',                                '',        '',        400.0,   50.0,     350.0,     ''),
                ('4 Ingresos',                                                '',        '',        '',      325.0,    '',        325.0),
                ('401 Ingresos',                                              '',        '',        '',      325.0,    '',        325.0),
                ('401.01 Ventas y/o servicios gravados a la tasa general',    '',        '',        '',      325.0,    '',        325.0),
                ('401.01.01 Ventas y/o servicios gravados a la tasa general', '',        '',        '',      325.0,    '',        325.0),
                ('6 Gastos',                                                  '',        '',        250.0,   '',       250.0,     ''),
                ('601 Gastos generales',                                      '',        '',        250.0,   '',       250.0,     ''),
                ('601.84 Otros gastos generales',                             '',        '',        250.0,   '',       250.0,     ''),
                ('601.84.01 Otros gastos generales',                          '',        '',        250.0,   '',       250.0,     ''),
                ('(No Group)',                                                '',        1000.0,    '',      '',       '',        1000.0),
                ('999999 Undistributed Profits/Losses',                       '',        1000.0,    '',      '',       '',        1000.0),
                ('Total',                                                     1000.0,    1000.0,    775.0,   775.0,    1675.0,    1675.0),
            ],
        )
