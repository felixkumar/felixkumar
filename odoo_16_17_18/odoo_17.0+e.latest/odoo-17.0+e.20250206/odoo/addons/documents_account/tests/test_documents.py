# -*- coding: utf-8 -*-

import base64

from odoo.tests import Form

from odoo.exceptions import UserError
from odoo.tests.common import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon

GIF = b"R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs="
TEXT = base64.b64encode(bytes("workflow bridge account", 'utf-8'))
PDF = 'JVBERi0xLjYNJeLjz9MNCjI0IDAgb2JqDTw8L0ZpbHRlci9GbGF0ZURlY29kZS9GaXJzdCA0L0xlbmd0aCAyMTYvTiAxL1R5cGUvT2JqU3RtPj5zdHJlYW0NCmjePI9RS8MwFIX/yn1bi9jepCQ6GYNpFBTEMsW97CVLbjWYNpImmz/fVsXXcw/f/c4SEFarepPTe4iFok8dU09DgtDBQx6TMwT74vaLTE7uSPDUdXM0Xe/73r1FnVwYYEtHR6d9WdY3kX4ipRMV6oojSmxQMoGyac5RLBAXf63p38aGA7XPorLewyvFcYaJile8rB+D/YcwiRdMMGScszO8/IW0MdhsaKKYGA46gXKTr/cUQVY4We/cYMNpnLVeXPJUXHs9fECr7kAFk+eZ5Xr9LcAAfKpQrA0KZW5kc3RyZWFtDWVuZG9iag0yNSAwIG9iag08PC9GaWx0ZXIvRmxhdGVEZWNvZGUvRmlyc3QgNC9MZW5ndGggNDkvTiAxL1R5cGUvT2JqU3RtPj5zdHJlYW0NCmjeslAwULCx0XfOL80rUTDU985MKY42NAIKBsXqh1QWpOoHJKanFtvZAQQYAN/6C60NCmVuZHN0cmVhbQ1lbmRvYmoNMjYgMCBvYmoNPDwvRmlsdGVyL0ZsYXRlRGVjb2RlL0ZpcnN0IDkvTGVuZ3RoIDQyL04gMi9UeXBlL09ialN0bT4+c3RyZWFtDQpo3jJTMFAwVzC0ULCx0fcrzS2OBnENFIJi7eyAIsH6LnZ2AAEGAI2FCDcNCmVuZHN0cmVhbQ1lbmRvYmoNMjcgMCBvYmoNPDwvRmlsdGVyL0ZsYXRlRGVjb2RlL0ZpcnN0IDUvTGVuZ3RoIDEyMC9OIDEvVHlwZS9PYmpTdG0+PnN0cmVhbQ0KaN4yNFIwULCx0XfOzytJzSspVjAyBgoE6TsX5Rc45VdEGwB5ZoZGCuaWRrH6vqkpmYkYogGJRUCdChZgfUGpxfmlRcmpxUAzA4ryk4NTS6L1A1zc9ENSK0pi7ez0g/JLEktSFQz0QyoLUoF601Pt7AACDADYoCeWDQplbmRzdHJlYW0NZW5kb2JqDTIgMCBvYmoNPDwvTGVuZ3RoIDM1MjUvU3VidHlwZS9YTUwvVHlwZS9NZXRhZGF0YT4+c3RyZWFtDQo8P3hwYWNrZXQgYmVnaW49Iu+7vyIgaWQ9Ilc1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCI/Pgo8eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJBZG9iZSBYTVAgQ29yZSA1LjQtYzAwNSA3OC4xNDczMjYsIDIwMTIvMDgvMjMtMTM6MDM6MDMgICAgICAgICI+CiAgIDxyZGY6UkRGIHhtbG5zOnJkZj0iaHR0cDovL3d3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYtc3ludGF4LW5zIyI+CiAgICAgIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICAgICAgICAgIHhtbG5zOnBkZj0iaHR0cDovL25zLmFkb2JlLmNvbS9wZGYvMS4zLyIKICAgICAgICAgICAgeG1sbnM6eG1wPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvIgogICAgICAgICAgICB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIKICAgICAgICAgICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIj4KICAgICAgICAgPHBkZjpQcm9kdWNlcj5BY3JvYmF0IERpc3RpbGxlciA2LjAgKFdpbmRvd3MpPC9wZGY6UHJvZHVjZXI+CiAgICAgICAgIDx4bXA6Q3JlYXRlRGF0ZT4yMDA2LTAzLTA2VDE1OjA2OjMzLTA1OjAwPC94bXA6Q3JlYXRlRGF0ZT4KICAgICAgICAgPHhtcDpDcmVhdG9yVG9vbD5BZG9iZVBTNS5kbGwgVmVyc2lvbiA1LjIuMjwveG1wOkNyZWF0b3JUb29sPgogICAgICAgICA8eG1wOk1vZGlmeURhdGU+MjAxNi0wNy0xNVQxMDoxMjoyMSswODowMDwveG1wOk1vZGlmeURhdGU+CiAgICAgICAgIDx4bXA6TWV0YWRhdGFEYXRlPjIwMTYtMDctMTVUMTA6MTI6MjErMDg6MDA8L3htcDpNZXRhZGF0YURhdGU+CiAgICAgICAgIDx4bXBNTTpEb2N1bWVudElEPnV1aWQ6ZmYzZGNmZDEtMjNmYS00NzZmLTgzOWEtM2U1Y2FlMmRhMmViPC94bXBNTTpEb2N1bWVudElEPgogICAgICAgICA8eG1wTU06SW5zdGFuY2VJRD51dWlkOjM1OTM1MGIzLWFmNDAtNGQ4YS05ZDZjLTAzMTg2YjRmZmIzNjwveG1wTU06SW5zdGFuY2VJRD4KICAgICAgICAgPGRjOmZvcm1hdD5hcHBsaWNhdGlvbi9wZGY8L2RjOmZvcm1hdD4KICAgICAgICAgPGRjOnRpdGxlPgogICAgICAgICAgICA8cmRmOkFsdD4KICAgICAgICAgICAgICAgPHJkZjpsaSB4bWw6bGFuZz0ieC1kZWZhdWx0Ij5CbGFuayBQREYgRG9jdW1lbnQ8L3JkZjpsaT4KICAgICAgICAgICAgPC9yZGY6QWx0PgogICAgICAgICA8L2RjOnRpdGxlPgogICAgICAgICA8ZGM6Y3JlYXRvcj4KICAgICAgICAgICAgPHJkZjpTZXE+CiAgICAgICAgICAgICAgIDxyZGY6bGk+RGVwYXJ0bWVudCBvZiBKdXN0aWNlIChFeGVjdXRpdmUgT2ZmaWNlIG9mIEltbWlncmF0aW9uIFJldmlldyk8L3JkZjpsaT4KICAgICAgICAgICAgPC9yZGY6U2VxPgogICAgICAgICA8L2RjOmNyZWF0b3I+CiAgICAgIDwvcmRmOkRlc2NyaXB0aW9uPgogICA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgog' + 682 * 'ICAg' + 'Cjw/eHBhY2tldCBlbmQ9InciPz4NCmVuZHN0cmVhbQ1lbmRvYmoNMTEgMCBvYmoNPDwvTWV0YWRhdGEgMiAwIFIvUGFnZUxhYmVscyA2IDAgUi9QYWdlcyA4IDAgUi9UeXBlL0NhdGFsb2c+Pg1lbmRvYmoNMjMgMCBvYmoNPDwvRmlsdGVyL0ZsYXRlRGVjb2RlL0xlbmd0aCAxMD4+c3RyZWFtDQpIiQIIMAAAAAABDQplbmRzdHJlYW0NZW5kb2JqDTI4IDAgb2JqDTw8L0RlY29kZVBhcm1zPDwvQ29sdW1ucyA0L1ByZWRpY3RvciAxMj4+L0ZpbHRlci9GbGF0ZURlY29kZS9JRFs8REI3Nzc1Q0NFMjI3RjZCMzBDNDQwREY0MjIxREMzOTA+PEJGQ0NDRjNGNTdGNjEzNEFCRDNDMDRBOUU0Q0ExMDZFPl0vSW5mbyA5IDAgUi9MZW5ndGggODAvUm9vdCAxMSAwIFIvU2l6ZSAyOS9UeXBlL1hSZWYvV1sxIDIgMV0+PnN0cmVhbQ0KaN5iYgACJjDByGzIwPT/73koF0wwMUiBWYxA4v9/EMHA9I/hBVCxoDOQeH8DxH2KrIMIglFwIpD1vh5IMJqBxPpArHYgwd/KABBgAP8bEC0NCmVuZHN0cmVhbQ1lbmRvYmoNc3RhcnR4cmVmDQo0NTc2DQolJUVPRg0K'


@tagged('post_install', '-at_install', 'test_document_bridge')
class TestCaseDocumentsBridgeAccount(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.folder_a = cls.env['documents.folder'].create({
            'name': 'folder A',
        })
        cls.folder_a_a = cls.env['documents.folder'].create({
            'name': 'folder A - A',
            'parent_folder_id': cls.folder_a.id,
        })
        cls.document_txt = cls.env['documents.document'].create({
            'datas': TEXT,
            'name': 'file.txt',
            'mimetype': 'text/plain',
            'folder_id': cls.folder_a_a.id,
        })
        cls.document_gif = cls.env['documents.document'].create({
            'datas': GIF,
            'name': 'file.gif',
            'mimetype': 'image/gif',
            'folder_id': cls.folder_a.id,
        })
        cls.workflow_rule_vendor_bill = cls.env['documents.workflow.rule'].create({
            'domain_folder_id': cls.folder_a.id,
            'name': 'workflow rule create vendor bill on f_a',
            'create_model': 'account.move.in_invoice',
        })

    def test_bridge_folder_workflow(self):
        """
        tests the create new business model (vendor bill & credit note).

        """
        self.assertEqual(self.document_txt.res_model, 'documents.document', "failed at default res model")
        multi_return = self.workflow_rule_vendor_bill.apply_actions([self.document_txt.id, self.document_gif.id])
        self.assertEqual(multi_return.get('type'), 'ir.actions.act_window',
                         'failed at invoice workflow return value type')
        self.assertEqual(multi_return.get('res_model'), 'account.move',
                         'failed at invoice workflow return value res model')

        self.assertEqual(self.document_txt.res_model, 'account.move', "failed at workflow_bridge_dms_account"
                                                                           " new res_model")
        vendor_bill_txt = self.env['account.move'].search([('id', '=', self.document_txt.res_id)])
        self.assertTrue(vendor_bill_txt.exists(), 'failed at workflow_bridge_dms_account vendor_bill')
        self.assertEqual(self.document_txt.res_id, vendor_bill_txt.id, "failed at workflow_bridge_dms_account res_id")
        self.assertEqual(vendor_bill_txt.move_type, 'in_invoice', "failed at workflow_bridge_dms_account vendor_bill type")
        vendor_bill_gif = self.env['account.move'].search([('id', '=', self.document_gif.res_id)])
        self.assertEqual(self.document_gif.res_id, vendor_bill_gif.id, "failed at workflow_bridge_dms_account res_id")

        single_return = self.workflow_rule_vendor_bill.apply_actions([self.document_txt.id])
        self.assertEqual(single_return.get('res_model'), 'account.move',
                         'failed at invoice res_model action from workflow create model')
        invoice = self.env[single_return['res_model']].browse(single_return.get('res_id'))
        attachments = self.env['ir.attachment'].search([('res_model', '=', 'account.move'), ('res_id', '=', invoice.id)])
        self.assertEqual(len(attachments), 1, 'there should only be one ir attachment matching')

    def test_bridge_account_account_settings_on_write(self):
        """
        Makes sure the settings apply their values when an ir_attachment is set as message_main_attachment_id
        on invoices.
        """
        folder_test = self.env['documents.folder'].create({'name': 'folder_test'})
        self.env.user.company_id.documents_account_settings = True

        for invoice_type in ['in_invoice', 'out_invoice', 'in_refund', 'out_refund']:
            invoice_test = self.env['account.move'].with_context(default_move_type=invoice_type).create({
                'name': 'invoice_test',
                'move_type': invoice_type,
            })
            setting = self.env['documents.account.folder.setting'].create({
                'folder_id': folder_test.id,
                'journal_id': invoice_test.journal_id.id,
            })

            attachments = self.env["ir.attachment"]
            for i in range(3):
                attachment = self.env["ir.attachment"].create({
                    "datas": TEXT,
                    "name": f"fileText_test{i}.txt",
                    "mimetype": "text/plain",
                    "res_model": "account.move",
                    "res_id": invoice_test.id,
                })
                attachment.register_as_main_attachment(force=False)
                attachments |= attachment

            document = self.env["documents.document"].search(
                [("attachment_id", "=", attachments[0].id)]
            )
            self.assertEqual(
                document.folder_id, folder_test, "the text test document have a folder"
            )

            def check_main_attachment_and_document(
                main_attachment, doc_attachment, previous_attachment_ids
            ):
                self.assertRecordValues(
                    invoice_test,
                    [{"message_main_attachment_id": main_attachment.id}],
                )
                self.assertRecordValues(
                    document,
                    [
                        {
                            "attachment_id": doc_attachment.id,
                            "previous_attachment_ids": previous_attachment_ids,
                        }
                    ],
                )

            # Ensure the main attachment is the first one and ensure the document is correctly linked
            check_main_attachment_and_document(attachments[0], attachments[0], [])

            # Switch the main attachment to the second one and ensure the document is updated correctly
            invoice_test.write({"message_main_attachment_id": attachments[1].id})
            check_main_attachment_and_document(
                attachments[1], attachments[1], attachments[0].ids
            )

            # Switch the main attachment to the third one and ensure the document is updated correctly
            attachments[2].register_as_main_attachment(force=True)
            check_main_attachment_and_document(
                attachments[2], attachments[2], (attachments[0] + attachments[1]).ids
            )

            # Ensure all attachments are still linked to the invoice
            attachments = self.env["ir.attachment"].search(
                [("res_model", "=", "account.move"), ("res_id", "=", invoice_test.id)]
            )
            self.assertEqual(
                len(attachments),
                3,
                "there should be 3 attachments linked to the invoice",
            )

            # deleting the setting to prevent duplicate settings.
            setting.unlink()

    def test_bridge_account_account_settings_on_write_with_versioning(self):
        """
        With accounting-document centralization activated, make sure that the right attachment
        is set as main attachment on the invoice when versioning is involved and only one document
        is being created and updated.
        """
        folder_test = self.env["documents.folder"].create({"name": "folder_test"})
        self.env.user.company_id.documents_account_settings = True

        invoice_test = (
            self.env["account.move"]
            .with_context(default_move_type="in_invoice")
            .create({
                "name": "invoice_test",
                "move_type": "in_invoice",
            })
        )

        self.env["documents.account.folder.setting"].create({
            "folder_id": folder_test.id,
            "journal_id": invoice_test.journal_id.id,
        })

        attachments = self.env["ir.attachment"]
        for i in range(1, 3):
            attachment = self.env["ir.attachment"].create({
                "datas": TEXT,
                "name": f"attachment-{i}.txt",
                "mimetype": "text/plain",
                "res_model": "account.move",
                "res_id": invoice_test.id,
            })
            attachment.register_as_main_attachment(force=False)
            attachments |= attachment

        first_attachment, second_attachment = attachments[0], attachments[1]

        document = self.env["documents.document"].search(
            [("res_model", "=", "account.move"), ("res_id", "=", invoice_test.id)]
        )
        self.assertEqual(
            len(document), 1, "there should be 1 document linked to the invoice"
        )
        self.assertEqual(
            document.folder_id, folder_test, "the text test document have a folder"
        )

        def check_main_attachment_and_document(
            main_attachment, doc_attachment, previous_attachment_ids
        ):
            self.assertRecordValues(
                invoice_test,
                [{"message_main_attachment_id": main_attachment.id}],
            )
            self.assertRecordValues(
                document,
                [
                    {
                        "attachment_id": doc_attachment.id,
                        "previous_attachment_ids": previous_attachment_ids,
                    }
                ],
            )

        # Ensure the main attachment is attachment-1
        check_main_attachment_and_document(first_attachment, first_attachment, [])

        # Version the main attachment:
        # attachment-1 become attachment-3
        # version attachement become attachment-1
        document.write({
            "datas": TEXT,
            "name": "attachment-3.txt",
            "mimetype": "text/plain",
        })
        third_attachment = document.attachment_id
        first_attachment = document.previous_attachment_ids[0]
        check_main_attachment_and_document(
            third_attachment, third_attachment, first_attachment.ids
        )

        # Switch main attachment to attachment-2
        second_attachment.register_as_main_attachment(force=True)
        check_main_attachment_and_document(
            second_attachment,
            second_attachment,
            (first_attachment + third_attachment).ids,
        )

        # restore versioned attachment (attachment-1)
        document.write({"attachment_id": document.previous_attachment_ids[0].id})
        check_main_attachment_and_document(
            second_attachment,
            first_attachment,
            (third_attachment + second_attachment).ids,
        )

        # Switch main attachment to attachment-3
        third_attachment.register_as_main_attachment(force=True)
        check_main_attachment_and_document(
            third_attachment,
            third_attachment,
            (second_attachment + first_attachment).ids,
        )

        # Ensure there is still only one document linked to the invoice
        document = self.env["documents.document"].search(
            [("res_model", "=", "account.move"), ("res_id", "=", invoice_test.id)]
        )
        self.assertEqual(
            len(document), 1, "there should be 1 document linked to the invoice"
        )

    def test_journal_entry(self):
        """
        Makes sure the settings apply their values when an ir_attachment is set as message_main_attachment_id
        on invoices.
        """
        folder_test = self.env['documents.folder'].create({'name': 'Bills'})
        self.env.user.company_id.documents_account_settings = True

        invoice_test = self.env['account.move'].with_context(default_move_type='entry').create({
            'name': 'Journal Entry',
            'move_type': 'entry',
        })
        setting = self.env['documents.account.folder.setting'].create({
            'folder_id': folder_test.id,
            'journal_id': invoice_test.journal_id.id,
        })
        attachments = self.env['ir.attachment'].create([{
            'datas': TEXT,
            'name': 'fileText_test.txt',
            'mimetype': 'text/plain',
            'res_model': 'account.move',
            'res_id': invoice_test.id
        }, {
            'datas': TEXT,
            'name': 'fileText_test2.txt',
            'mimetype': 'text/plain',
            'res_model': 'account.move',
            'res_id': invoice_test.id
        }])
        documents = self.env['documents.document'].search([('attachment_id', 'in', attachments.ids)])
        self.assertEqual(len(documents), 2)
        setting.unlink()

    def test_bridge_account_workflow_settings_on_write(self):
        """
        Tests that tags added by a workflow action are not completely overridden by the settings.
        """
        self.env.user.company_id.documents_account_settings = True
        tag_category_a = self.env['documents.facet'].create({
            'folder_id': self.folder_a.id,
            'name': "categ_a",
        })
        tag_a = self.env['documents.tag'].create({
            'facet_id': tag_category_a.id,
            'name': "tag_a",
        })
        tag_b = self.env['documents.tag'].create({
            'facet_id': tag_category_a.id,
            'name': "tag_b",
        })
        tag_action_a = self.env['documents.workflow.action'].create({
            'action': 'add',
            'facet_id': tag_category_a.id,
            'tag_id': tag_a.id,
        })
        self.workflow_rule_vendor_bill.tag_action_ids += tag_action_a

        invoice_test = self.env['account.move'].with_context(default_move_type='in_invoice').create({
            'name': 'invoice_test',
            'move_type': 'in_invoice',
        })
        self.env['documents.account.folder.setting'].create({
            'folder_id': self.folder_a.id,
            'journal_id': invoice_test.journal_id.id,
            'tag_ids': tag_b,
        })
        document_test = self.env['documents.document'].create({
            'name': 'test reconciliation workflow',
            'folder_id': self.folder_a.id,
            'datas': TEXT,
        })
        self.workflow_rule_vendor_bill.apply_actions([document_test.id])
        self.assertEqual(document_test.tag_ids, tag_a | tag_b,
            "The document should have the workflow action's tag(s)")

    def test_bridge_account_sync_partner(self):
        """
        Tests that the partner is always synced on the document, regardless of settings
        """
        partner_1, partner_2 = self.env['res.partner'].create([{'name': 'partner_1'}, {'name': 'partner_2'}])
        self.document_txt.partner_id = partner_1
        self.workflow_rule_vendor_bill.apply_actions([self.document_txt.id, self.document_gif.id])
        move = self.env['account.move'].browse(self.document_txt.res_id)
        self.assertEqual(move.partner_id, partner_1)
        move.partner_id = partner_2
        self.assertEqual(self.document_txt.partner_id, partner_2)

    def test_workflow_create_misc_entry(self):
        misc_entry_rule = self.env.ref('documents_account.misc_entry_rule')
        misc_entry_rule.journal_id = misc_entry_rule.suitable_journal_ids[0]
        misc_entry_action = misc_entry_rule.apply_actions([self.document_txt.id, self.document_gif.id])
        move = self.env['account.move'].browse(self.document_txt.res_id)
        self.assertEqual(misc_entry_action.get('res_model'), 'account.move')
        self.assertEqual(move.move_type, 'entry')
        self.assertTrue(move.journal_id in misc_entry_rule.suitable_journal_ids)

    def test_workflow_create_bank_statement_raise(self):
        with self.assertRaises(UserError): # Could not make sense of the given file.
            self.env.ref('documents_account.bank_statement_rule').apply_actions([self.document_txt.id, self.document_gif.id])

    def test_workflow_create_vendor_bill(self):
        vendor_bill_entry_rule = self.env.ref('documents_account.vendor_bill_rule_financial')
        vendor_bill_entry_action = vendor_bill_entry_rule.apply_actions([self.document_txt.id])
        move = self.env['account.move'].browse(self.document_txt.res_id)
        self.assertEqual(vendor_bill_entry_action.get('res_model'), 'account.move')
        self.assertEqual(move.move_type, 'in_invoice')
        self.assertTrue(move.journal_id in vendor_bill_entry_rule.suitable_journal_ids)

    def test_workflow_create_vendor_receipt(self):
        # Activate the group for the vendor receipt
        self.env['res.config.settings'].create({'group_show_purchase_receipts': True}).execute()
        self.assertTrue(self.env.user.has_group('account.group_purchase_receipts'), 'The "purchase Receipt" feature should be enabled.')
        vendor_receipt_rule = self.env.ref('documents_account.documents_vendor_receipt_rule')
        vendor_receipt_action = vendor_receipt_rule.apply_actions([self.document_txt.id])
        move = self.env['account.move'].browse(self.document_txt.res_id)
        self.assertEqual(vendor_receipt_action.get('res_model'), 'account.move')
        self.assertEqual(move.move_type, 'in_receipt')
        self.assertTrue(move.journal_id in vendor_receipt_rule.suitable_journal_ids)

    def test_workflow_rule_form_journal(self):
        rule_financial = self.env.ref('documents_account.vendor_bill_rule_financial')
        rule_financial.journal_id = rule_financial.suitable_journal_ids[0]
        with Form(rule_financial) as rule:
            # our accounting action has a journal_id
            self.assertTrue(rule.journal_id)

            # switching it to non-accouting action resets its journal_id on write/create
            rule.create_model = 'link.to.record'
            rule.save()
            self.assertFalse(rule.journal_id)

            # switching back gives us the rigth journal_id on write/create
            rule.create_model = 'account.move.out_invoice'
            rule.save()
            self.assertTrue(rule.journal_id.type == 'sale')
            self.assertTrue(rule.journal_id in rule.suitable_journal_ids)

    def test_documents_xml_attachment(self):
        """
        Makes sure pdf and xml created by the system will create a document
        """
        folder_test = self.env['documents.folder'].create({'name': 'Bills'})
        self.env.user.company_id.documents_account_settings = True

        invoice = self.init_invoice("out_invoice", amounts=[1000], post=True)
        setting = self.env['documents.account.folder.setting'].create({
            'folder_id': folder_test.id,
            'journal_id': invoice.journal_id.id,
        })
        att_ids = []
        for fmt in ('xml', 'txt'):
            attachment = self.env["ir.attachment"].create({
                "raw": "<text/>",
                "name": f"attachment-{fmt}.txt",
                "mimetype": f"application/{fmt}",
                "res_model": "account.move",
                "res_id": invoice.id,
            })
            att_ids.append(attachment.id)
        documents = self.env['documents.document'].search([('attachment_id', 'in', att_ids)])
        self.assertEqual(len(documents), 1, "TXT should not create a document")
        attachment_pdf = self.env['ir.attachment'].create({
            'datas': PDF,
            'name': 'file.pdf',
            'mimetype': 'application/pdf',
            'res_model': invoice._name,
            'res_id': invoice.id,
        })
        documents = self.env['documents.document'].search([('attachment_id', '=', attachment_pdf.id)])
        self.assertFalse(documents, "pdf should not be attached if not main attachment")
        attachment_pdf.register_as_main_attachment(force=False)
        documents = self.env['documents.document'].search([('attachment_id', '=', attachment_pdf.id)])
        self.assertTrue(documents, "Pdf registered as main attachment did not create a document")
        setting.unlink()
