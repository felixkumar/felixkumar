# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import Command
from odoo.addons.account_reports.tests.common import TestAccountReportsCommon
from odoo.tests import tagged
from .gstr_test_json import gstr2b_test_json, gstr2b_late_reconciliation_data, gstr2b_reconciliation_different_partner
import logging
import json
from datetime import date
from dateutil.relativedelta import relativedelta

TEST_DATE = date(2023, 5, 20)
_logger = logging.getLogger(__name__)

@tagged('post_install_l10n', 'post_install', '-at_install')
class TestReports(TestAccountReportsCommon):

    @classmethod
    def l10n_in_reports_gstr2b_inv_init(cls, ref, partner=None, product_price_unit=None, inv=None, invoice_date=TEST_DATE, gst_treatment=None):

        if not inv:
            inv = cls.init_invoice(
                "in_invoice",
                products=cls.product_a,
                invoice_date=invoice_date,
                taxes=cls.igst_18,
                company=cls.company_data['company'],
                partner=partner,
            )
        else:
            inv = inv._reverse_moves()
            inv.write({'invoice_date': invoice_date})
        inv.write({'ref': ref})
        if product_price_unit:
            inv.write({'invoice_line_ids': [Command.update(l.id, {'price_unit': product_price_unit}) for l in inv.invoice_line_ids]})
        if gst_treatment:
            inv.write({'l10n_in_gst_treatment': gst_treatment})
        inv.action_post()
        return inv

    @classmethod
    def _get_tax_from_xml_id(cls, trailing_xmlid):
        return cls.env.ref('account.%s_%s' % (cls.company_data['company'].id, trailing_xmlid))

    @classmethod
    def setUpClass(cls, chart_template_ref="in"):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.company_data["company"].write({
            "vat": "24AAGCC7144L6ZE",
            "state_id": cls.env.ref("base.state_in_gj").id,
            "street": "street1",
            "city": "city1",
            "zip": "123456",
            "country_id": cls.env.ref("base.in").id,
        })
        cls.partner_b.write({
            "vat": "27BBBFF5679L8ZR",
            "state_id": cls.env.ref("base.state_in_mh").id,
            "street": "street1",
            "city": "city1",
            "zip": "123456",
            "country_id": cls.env.ref("base.in").id,
            "l10n_in_gst_treatment": "regular",
        })
        overseas_partner = cls.partner_b.copy({
            'l10n_in_gst_treatment': 'overseas',
            'vat': None,
            'state_id': cls.env.ref("base.state_us_5").id,
            'country_id': cls.env.ref("base.us").id
        })
        cls.product_a.write({"l10n_in_hsn_code": "01111"})
        cls.igst_18 = cls._get_tax_from_xml_id("igst_sale_18")

        cls.fully_matched_bill = cls.l10n_in_reports_gstr2b_inv_init('INV/001', cls.partner_b)
        cls.fully_matched_bill_refund = cls.l10n_in_reports_gstr2b_inv_init('CR/001', inv=cls.fully_matched_bill)

        cls.bill_with_conflict_date = cls.l10n_in_reports_gstr2b_inv_init('INV/002', cls.partner_b)

        cls.bill_with_conflict_amount = cls.l10n_in_reports_gstr2b_inv_init('INV/003', cls.partner_b)

        cls.bill_with_conflict_date_amount = cls.l10n_in_reports_gstr2b_inv_init('INV/004', cls.partner_b)

        cls.bill_with_conflict_type = cls.l10n_in_reports_gstr2b_inv_init('INV/005', cls.partner_b)

        cls.bill_with_conflict_type_date = cls.l10n_in_reports_gstr2b_inv_init('CR/002', inv=cls.bill_with_conflict_type)

        cls.bill_with_conflict_type_amount = cls.l10n_in_reports_gstr2b_inv_init('INV/006', cls.partner_b)

        cls.bill_with_conflict_type_date_amount = cls.l10n_in_reports_gstr2b_inv_init('CR/003', inv=cls.bill_with_conflict_type)

        partner_conflict_vat = cls.partner_b.copy({'vat': '24ABCDM1234E1ZE'})
        cls.bill_with_conflict_vat = cls.l10n_in_reports_gstr2b_inv_init('INV/007', partner_conflict_vat)

        cls.bill_with_conflict_vat_date = cls.l10n_in_reports_gstr2b_inv_init('INV/008', partner_conflict_vat)

        cls.bill_with_conflict_vat_amount = cls.l10n_in_reports_gstr2b_inv_init('INV/009', partner_conflict_vat)

        cls.bill_with_conflict_vat_date_amount = cls.l10n_in_reports_gstr2b_inv_init('INV/010', partner_conflict_vat)

        cls.bill_with_conflict_vat_type = cls.l10n_in_reports_gstr2b_inv_init('INV/011', partner_conflict_vat)

        cls.bill_with_conflict_vat_type_date = cls.l10n_in_reports_gstr2b_inv_init('CR/004', inv=cls.bill_with_conflict_type)

        cls.bill_with_conflict_vat_type_amount = cls.l10n_in_reports_gstr2b_inv_init('INV/012', partner_conflict_vat)

        cls.bill_with_conflict_vat_type_date_amount = cls.l10n_in_reports_gstr2b_inv_init('CR/005', inv=cls.bill_with_conflict_type)

        cls.bill_with_conflict_ref = cls.l10n_in_reports_gstr2b_inv_init(None, cls.partner_b, 2000)

        cls.bill_not_in_gstr2b = cls.bill_with_conflict_ref = cls.l10n_in_reports_gstr2b_inv_init('INV/404', cls.partner_b)

        cls.overseas_bill = cls.bill_with_conflict_ref = cls.l10n_in_reports_gstr2b_inv_init('BOE/123', overseas_partner, 100000)

        cls.report = cls.gstr_report = cls.env['l10n_in.gst.return.period'].create({
            'company_id': cls.company_data["company"].id,
            'periodicity': 'monthly',
            'year': TEST_DATE.strftime('%Y'),
            'month': TEST_DATE.strftime('%m'),
        })

    def test_gstr2b(self):

        self.report.gstr2b_json_from_portal_ids = self.env['ir.attachment'].create({
            'name': 'gstr2b.json',
            'mimetype': 'application/json',
            'raw': json.dumps(gstr2b_test_json),
        })
        self.report.gstr2b_match_data()

        self.assertEqual(self.report.gstr2b_status, "partially_matched")
        self.assertEqual(self.fully_matched_bill.l10n_in_gstr2b_reconciliation_status, "matched")
        self.assertEqual(bool(self.fully_matched_bill.l10n_in_exception), False)
        self.assertEqual(self.fully_matched_bill_refund.l10n_in_gstr2b_reconciliation_status, "matched")
        self.assertEqual(self.bill_with_conflict_date.l10n_in_gstr2b_reconciliation_status, "partially_matched")
        self.assertEqual(self.bill_with_conflict_amount.l10n_in_gstr2b_reconciliation_status, "partially_matched")
        self.assertEqual(self.bill_with_conflict_date_amount.l10n_in_gstr2b_reconciliation_status, "partially_matched")

        self.assertEqual(self.bill_with_conflict_type.l10n_in_gstr2b_reconciliation_status, "partially_matched")
        self.assertEqual(self.bill_with_conflict_type_date.l10n_in_gstr2b_reconciliation_status, "partially_matched")
        self.assertEqual(self.bill_with_conflict_type_amount.l10n_in_gstr2b_reconciliation_status, "partially_matched")
        self.assertEqual(self.bill_with_conflict_type_date_amount.l10n_in_gstr2b_reconciliation_status, "partially_matched")

        self.assertEqual(self.bill_with_conflict_vat.l10n_in_gstr2b_reconciliation_status, "partially_matched")
        self.assertEqual(self.bill_with_conflict_vat_date.l10n_in_gstr2b_reconciliation_status, "partially_matched")
        self.assertEqual(self.bill_with_conflict_vat_amount.l10n_in_gstr2b_reconciliation_status, "partially_matched")
        self.assertEqual(self.bill_with_conflict_vat_date_amount.l10n_in_gstr2b_reconciliation_status, "partially_matched")

        self.assertEqual(self.bill_with_conflict_vat_type.l10n_in_gstr2b_reconciliation_status, "partially_matched")
        self.assertEqual(self.bill_with_conflict_vat_type_date.l10n_in_gstr2b_reconciliation_status, "partially_matched")
        self.assertEqual(self.bill_with_conflict_vat_type_amount.l10n_in_gstr2b_reconciliation_status, "partially_matched")
        self.assertEqual(self.bill_with_conflict_vat_type_date_amount.l10n_in_gstr2b_reconciliation_status, "partially_matched")

        self.assertEqual(self.bill_not_in_gstr2b.l10n_in_gstr2b_reconciliation_status, "bills_not_in_gstr2")
        self.assertEqual(self.overseas_bill.l10n_in_gstr2b_reconciliation_status, "matched")
        bill_not_in_odoo = self.env['account.move'].search([('ref', '=', '533515'), ('company_id', '=', self.company_data['company'].id)])
        self.assertEqual(len(bill_not_in_odoo), 1)
        self.assertEqual(bill_not_in_odoo.l10n_in_gstr2b_reconciliation_status, 'gstr2_bills_not_in_odoo')
        self.assertEqual(bill_not_in_odoo.l10n_in_gst_treatment, 'regular')
        sez_bill = self.env['account.move'].search([('ref', '=', 'SEZ/123'), ('company_id', '=', self.company_data['company'].id)])
        self.assertEqual(len(sez_bill), 1)
        self.assertEqual(sez_bill.l10n_in_gstr2b_reconciliation_status, "gstr2_bills_not_in_odoo")
        self.assertEqual(bool(sez_bill.l10n_in_exception), False)
        self.assertEqual(sez_bill.l10n_in_gst_treatment, "special_economic_zone")

    def test_gstr2b_late_reconciliation(self):
        """
        Test the GSTR-2B reconciliation process for late received invoices.

        This test verifies that when an invoice arrives with a previous month's date
        but differs from an existing invoice date, the original invoice remains unchanged.
        """
        previous_invoice = self.l10n_in_reports_gstr2b_inv_init('BILL/001', self.partner_b, invoice_date=TEST_DATE - relativedelta(months=1), product_price_unit=100)
        self.report.gstr2b_json_from_portal_ids = self.env['ir.attachment'].create({
            'name': 'gstr2b.json',
            'mimetype': 'application/json',
            'raw': json.dumps(gstr2b_late_reconciliation_data),
        })
        self.report.gstr2b_match_data()

        self.assertEqual(previous_invoice.l10n_in_gstr2b_reconciliation_status, "matched")
        self.assertFalse(previous_invoice.l10n_in_exception)
        self.assertEqual(previous_invoice.l10n_in_gst_return_period_id, self.report)

    def test_gstr2b_reconciliation_different_partner(self):
        """
        Test the GSTR-2B reconciliation process for invoices with different partners.

        This test verifies that when multiple invoices with the same reference
        but different partners are processed, they are correctly matched, and
        a new bill is created for any additional invoice found in the GSTR-2B data.

        The test checks that:
        - Three invoices are matched (two existing, one new).
        - Both bills with different partners are marked as 'matched'.
        - A new bill is created and labeled as 'gstr2_bills_not_in_odoo' for
        invoices found in the GSTR-2B data but not present in Odoo.
        """
        bill_with_partner_b = self.l10n_in_reports_gstr2b_inv_init('BILL/001', self.partner_b)
        partner_c = self.partner_b.copy({'name': 'Partner_c', 'vat': '24WXYZM1234E1ZE'})
        bill_with_partner_c = self.l10n_in_reports_gstr2b_inv_init('BILL/001', partner_c)

        self.report.gstr2b_json_from_portal_ids = self.env['ir.attachment'].create({
            'name': 'gstr2b.json',
            'mimetype': 'application/json',
            'raw': json.dumps(gstr2b_reconciliation_different_partner),
        })

        self.report.gstr2b_match_data()
        matched_invoices = self.env['account.move'].search([('ref', '=', 'BILL/001'), ('company_id', '=', self.company_data['company'].id)])
        self.assertEqual(len(matched_invoices), 3)
        self.assertEqual(bill_with_partner_b.l10n_in_gstr2b_reconciliation_status, "matched")
        self.assertEqual(bill_with_partner_c.l10n_in_gstr2b_reconciliation_status, "matched")

        new_bill = matched_invoices - bill_with_partner_b - bill_with_partner_c
        self.assertEqual(new_bill.l10n_in_gstr2b_reconciliation_status, "gstr2_bills_not_in_odoo")
