from odoo import fields, Command
from odoo.tests import tagged

from odoo.addons.account_reports.tests.common import TestAccountReportsCommon


@tagged("post_install", "post_install_l10n", "-at_install")
class TestPeSales(TestAccountReportsCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref="l10n_pe.pe_chart_template"):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.company_data["company"].country_id = cls.env.ref("base.pe")
        cls.company_data["company"].vat = "20512528458"
        cls.partner_a.write({"country_id": cls.env.ref("base.pe").id, "vat": "20557912879"})
        cls.partner_b.write({"country_id": cls.env.ref("base.pe").id, "vat": "20557912879"})

        move_types = ["out_invoice", "out_refund", "in_invoice", "in_refund"]
        date_invoice = "2022-07-01"
        moves_vals = [
            {
                "move_type": "entry",
                "date": date_invoice,
                "invoice_date_due": date_invoice,
                "line_ids": [
                    Command.create(
                        {'debit': 500.0, 'credit': 0.0, 'account_id': cls.company_data['default_account_expense'].id}),
                    Command.create(
                        {'debit': 0.0, 'credit': 500.0, 'account_id': cls.company_data['default_account_revenue'].id}),
                ]
            }
        ]
        moves_vals += [
            {
                "move_type": "entry",
                "date": date_invoice,
                "invoice_date_due": date_invoice,
                "line_ids": [
                    Command.create(
                        {'debit': 500.0, 'credit': 0.0, 'account_id': cls.company_data['default_account_expense'].id}),
                    Command.create(
                        {'debit': 0.0, 'credit': 500.0, 'account_id': cls.company_data['default_account_revenue'].id}),
                ]
            }
        ]
        for move_type in move_types:
            for partner in (cls.partner_a, cls.partner_b):
                moves_vals += [
                    {
                        "move_type": move_type,
                        "partner_id": partner.id,
                        "invoice_date": date_invoice,
                        "invoice_date_due": date_invoice,
                        "date": date_invoice,
                        "invoice_payment_term_id": False,
                        "l10n_latam_document_type_id": cls.env.ref("l10n_pe.document_type01").id if move_type in (
                            "out_invoice", "in_invoice") else cls.env.ref("l10n_pe.document_type07").id,
                        "l10n_latam_document_number": "FFF0001" if move_type in ("in_invoice", "in_refund") else False,
                        "invoice_line_ids": [
                            (0, 0, {
                                "name": f"test {move_type}",
                                "quantity": 1,
                                "price_unit": 10,
                                "tax_ids": [(6, 0, (
                                    cls.env.ref(f"l10n_pe.{cls.env.company.id}_sale_tax_igv_18") if move_type in ["out_invoice", "out_refund"] else
                                    cls.env.ref(f"l10n_pe.{cls.env.company.id}_purchase_tax_igv_18")).ids)],
                            })
                        ],
                    },
                ]

        moves = cls.env["account.move"].create(moves_vals)
        moves.action_post()

        # Move in draft must be ignored
        moves[0].copy({"date": moves[0].date})

    def test_51_report(self):
        report = self.env.ref("account_reports.general_ledger_report")
        options = self._generate_options(
            report, fields.Date.from_string("2022-01-01"), fields.Date.from_string("2022-12-31")
        )

        self.maxDiff = None
        self.assertEqual(
            "\n".join(
                [
                    "|".join(line.split("|")[2:-3])
                    for line in self.env[report.custom_handler_model_name]
                    .l10n_pe_export_ple_51_to_txt(options)["file_content"]
                    .decode()
                    .split("\n")
                ]
            ),
            """
M1|6011000|||PEN|||00|MISC202207|0001|01/07/2022|01/07/2022|01/07/2022|MISC2022070001||500.00|0.00
M2|7011100|||PEN|||00|MISC202207|0001|01/07/2022|01/07/2022|01/07/2022|MISC2022070001||0.00|500.00
M1|6011000|||PEN|||00|MISC202207|0002|01/07/2022|01/07/2022|01/07/2022|MISC2022070002||500.00|0.00
M2|7011100|||PEN|||00|MISC202207|0002|01/07/2022|01/07/2022|01/07/2022|MISC2022070002||0.00|500.00
M1|7012100|||PEN|0|20557912879|01|FFFI|00000001|01/07/2022|01/07/2022|01/07/2022|FFFI-00000001||0.00|10.00
M2|4011100|||PEN|0|20557912879|01|FFFI|00000001|01/07/2022|01/07/2022|01/07/2022|FFFI-00000001||0.00|1.80
M3|1213000|||PEN|0|20557912879|01|FFFI|00000001|01/07/2022|01/07/2022|01/07/2022|FFFI-00000001||11.80|0.00
M1|7012100|||PEN|0|20557912879|01|FFFI|00000002|01/07/2022|01/07/2022|01/07/2022|FFFI-00000002||0.00|10.00
M2|4011100|||PEN|0|20557912879|01|FFFI|00000002|01/07/2022|01/07/2022|01/07/2022|FFFI-00000002||0.00|1.80
M3|1213010|||PEN|0|20557912879|01|FFFI|00000002|01/07/2022|01/07/2022|01/07/2022|FFFI-00000002||11.80|0.00
M1|7012100|||PEN|0|20557912879|07|FCNE|00000001|01/07/2022|01/07/2022|01/07/2022|FCNE-00000001||10.00|0.00
M2|4011100|||PEN|0|20557912879|07|FCNE|00000001|01/07/2022|01/07/2022|01/07/2022|FCNE-00000001||1.80|0.00
M3|1213000|||PEN|0|20557912879|07|FCNE|00000001|01/07/2022|01/07/2022|01/07/2022|FCNE-00000001||0.00|11.80
M1|7012100|||PEN|0|20557912879|07|FCNE|00000002|01/07/2022|01/07/2022|01/07/2022|FCNE-00000002||10.00|0.00
M2|4011100|||PEN|0|20557912879|07|FCNE|00000002|01/07/2022|01/07/2022|01/07/2022|FCNE-00000002||1.80|0.00
M3|1213010|||PEN|0|20557912879|07|FCNE|00000002|01/07/2022|01/07/2022|01/07/2022|FCNE-00000002||0.00|11.80
M1|6329000|||PEN|0|20557912879|01|FFFF|0001|01/07/2022|01/07/2022|01/07/2022|FFFF0001||10.00|0.00
M2|4011100|||PEN|0|20557912879|01|FFFF|0001|01/07/2022|01/07/2022|01/07/2022|FFFF0001||1.80|0.00
M3|4111000|||PEN|0|20557912879|01|FFFF|0001|01/07/2022|01/07/2022|01/07/2022|FFFF0001||0.00|11.80
M1|6329000|||PEN|0|20557912879|01|FFFF|0001|01/07/2022|01/07/2022|01/07/2022|FFFF0001||10.00|0.00
M2|4011100|||PEN|0|20557912879|01|FFFF|0001|01/07/2022|01/07/2022|01/07/2022|FFFF0001||1.80|0.00
M3|4111010|||PEN|0|20557912879|01|FFFF|0001|01/07/2022|01/07/2022|01/07/2022|FFFF0001||0.00|11.80
M1|6329000|||PEN|0|20557912879|07|FFFF|0001|01/07/2022|01/07/2022|01/07/2022|FFFF0001||0.00|10.00
M2|4011100|||PEN|0|20557912879|07|FFFF|0001|01/07/2022|01/07/2022|01/07/2022|FFFF0001||0.00|1.80
M3|4111000|||PEN|0|20557912879|07|FFFF|0001|01/07/2022|01/07/2022|01/07/2022|FFFF0001||11.80|0.00
M1|6329000|||PEN|0|20557912879|07|FFFF|0001|01/07/2022|01/07/2022|01/07/2022|FFFF0001||0.00|10.00
M2|4011100|||PEN|0|20557912879|07|FFFF|0001|01/07/2022|01/07/2022|01/07/2022|FFFF0001||0.00|1.80
M3|4111010|||PEN|0|20557912879|07|FFFF|0001|01/07/2022|01/07/2022|01/07/2022|FFFF0001||11.80|0.00
"""[1:],
        )

    def test_53_report(self):
        report = self.env.ref("account_reports.general_ledger_report")
        options = self._generate_options(
            report, fields.Date.from_string("2022-01-01"), fields.Date.from_string("2022-12-31")
        )

        self.assertEqual(
            self.env[report.custom_handler_model_name].l10n_pe_export_ple_53_to_txt(options)["file_content"]
            .decode().split("\n")[0],
            """20220101|1010000|Caja|01|Plan contable empresarial|||1|""",
        )
