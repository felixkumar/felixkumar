# -*- coding: utf-8 -*-

import base64
from odoo.tools import file_open
from odoo.tests.common import TransactionCase

GIF = b"R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs="


class TestCaseDocumentsBridgeSign(TransactionCase):
    """

    """
    def setUp(self):
        super(TestCaseDocumentsBridgeSign, self).setUp()

        with file_open('sign/static/demo/sample_contract.pdf', "rb") as f:
            pdf_content = f.read()

        self.folder_a = self.env['documents.folder'].create({
            'name': 'folder A',
        })
        self.folder_a_a = self.env['documents.folder'].create({
            'name': 'folder A - A',
            'parent_folder_id': self.folder_a.id,
        })
        self.document_pdf = self.env['documents.document'].create({
            'datas': base64.encodebytes(pdf_content),
            'name': 'file.pdf',
            'folder_id': self.folder_a_a.id,
        })
        self.workflow_rule_template = self.env['documents.workflow.rule'].create({
            'domain_folder_id': self.folder_a.id,
            'name': 'workflow rule create template on f_a',
            'create_model': 'sign.template.new',
        })

        self.workflow_rule_direct_sign = self.env['documents.workflow.rule'].create({
            'domain_folder_id': self.folder_a.id,
            'name': 'workflow rule direct sign',
            'create_model': 'sign.template.direct',
        })
        self.user = self.env['res.users'].create({
            'name': "foo",
            'login': "foo",
            'email': "foo@bar.com",
            'groups_id': [(6, 0, [self.env.ref('documents.group_documents_user').id,
                                  self.env.ref('sign.group_sign_user').id])]
        })

    def test_bridge_folder_workflow(self):
        """
        tests the create new business model (sign).
    
        """
        self.assertEqual(self.document_pdf.res_model, 'documents.document', "failed at default res model")
        self.workflow_rule_template.apply_actions([self.document_pdf.id])
        self.assertTrue(self.workflow_rule_direct_sign.limited_to_single_record,
                        "this rule should only be available on single records")
    
        self.assertEqual(self.document_pdf.res_model, 'sign.template',
                         "failed at workflow_bridge_dms_sign new res_model")
        template = self.env['sign.template'].search([('id', '=', self.document_pdf.res_id)])
        self.assertTrue(template.exists(), 'failed at workflow_bridge_dms_account template')
        self.assertEqual(self.document_pdf.res_id, template.id, "failed at workflow_bridge_dms_account res_id")

    def test_apply_sign_action_attachment_ownership(self):
        """ Test the attachment ownership while applying a sign action on a document.
        Note that we apply the action with a user that doesn't own the document nor the attachment.
        """
        attachment_count = self.env['ir.attachment'].search_count([])
        doc_attachment_id = self.document_pdf.attachment_id
        self.assertEqual(self.document_pdf.attachment_id.res_model, 'documents.document')
        action = self.workflow_rule_template.with_user(user=self.user).apply_actions([self.document_pdf.id])
        sign_template = self.env['sign.template'].browse(action['params']['id'])
        self.assertTrue(sign_template.exists())
        self.assertEqual(self.document_pdf.attachment_id, doc_attachment_id,
                         'Attachment is still linked to the document')
        self.assertEqual(doc_attachment_id.res_model, 'sign.template',
                         'Sign template got the ownership on the document attachment')
        self.assertEqual(sign_template.id, doc_attachment_id.res_id,
                         'Sign template got the ownership on the document attachment')
        self.assertEqual(self.env['ir.attachment'].search_count([]), attachment_count)

        action2 = self.workflow_rule_template.with_user(user=self.user).apply_actions([self.document_pdf.id])
        sign_template2 = self.env['sign.template'].browse(action2['params']['id'])
        self.assertTrue(sign_template2.exists())
        self.assertNotEqual(sign_template2.attachment_id, doc_attachment_id,
                            "A new attachment is created because the document doesn't own the attachment")
        self.assertEqual(self.document_pdf.attachment_id, doc_attachment_id,
                         "The document is still linked to the original attachment")
        self.assertEqual(doc_attachment_id.res_id, sign_template.id,
                         "The orginal attachment is still owned by the first sign template")
        self.assertEqual(self.env['ir.attachment'].search_count([]), attachment_count + 1)

        sign_template.unlink()
        self.assertFalse(
            self.document_pdf.exists(),
            "Deleting the sign template that has the ownership on the attachment, delete the original document")
        self.assertTrue(sign_template2.exists(), "The second template owning a duplicated attachment is preserved")
