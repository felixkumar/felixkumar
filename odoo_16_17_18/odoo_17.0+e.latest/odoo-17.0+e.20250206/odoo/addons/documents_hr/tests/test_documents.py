# -*- coding: utf-8 -*-

import base64
from odoo.tests.common import tagged, TransactionCase

TEXT = base64.b64encode(bytes("documents_hr", 'utf-8'))


@tagged('post_install', '-at_install', 'test_document_bridge')
class TestCaseDocumentsBridgeHR(TransactionCase):

    def setUp(self):
        super().setUp()
        self.documents_user = self.env['res.users'].create({
            'name': "documents test basic user",
            'login': "dtbu",
            'email': "dtbu@yourcompany.com",
            'groups_id': [(6, 0, [self.ref('documents.group_documents_user')])]
        })

        self.folder_test = self.env['documents.folder'].create({'name': 'folder_test'})
        company = self.env.user.company_id
        company.documents_hr_settings = True
        company.documents_hr_folder = self.folder_test.id
        self.employee = self.env['hr.employee'].create({
            'name': 'User Empl Employee',
            'user_id': self.documents_user.id,
            'work_contact_id': self.documents_user.partner_id.id,
        })

    def test_bridge_hr_settings_on_write(self):
        """
        Makes sure the settings apply their values when an ir_attachment is set as message_main_attachment_id
        on invoices.
        """
        attachment_txt_test = self.env['ir.attachment'].create({
            'datas': TEXT,
            'name': 'fileText_test.txt',
            'mimetype': 'text/plain',
            'res_model': 'hr.employee',
            'res_id': self.employee.id,
        })

        document = self.env['documents.document'].search([('attachment_id', '=', attachment_txt_test.id)])
        self.assertTrue(document.exists(), "There should be a new document created from the attachment")
        self.assertEqual(document.owner_id, self.documents_user, "The owner_id should be the document user")
        self.assertEqual(document.partner_id, self.employee.work_contact_id, "The partner_id should be the employee's address")

    def test_upload_employee_attachment(self):
        """
        Make sure an employee's attachment is linked to the existing document
        and a new one is not created.
        """
        document = self.env['documents.document'].create({
            'name': 'Doc',
            'folder_id': self.folder_test.id,
            'res_model': self.employee._name,
            'res_id': self.employee.id,
        })
        document.write({
            'datas': TEXT,
            'mimetype': 'text/plain',
        })
        self.assertTrue(document.attachment_id, "An attachment should have been created")

    def test_open_document_from_hr(self):
        """ Test that opening the document app from an employee (hr app) is opening it in the right context. """
        action = self.employee.action_open_documents()
        context = action['context']
        self.assertTrue(context['searchpanel_default_folder_id'])
        self.assertEqual(context['default_res_model'], 'hr.employee')
        self.assertEqual(context['default_res_id'], self.employee.id)
        self.assertEqual(context['default_partner_id'], self.employee.work_contact_id.id)
        self.env['documents.document'].create([
            {'name': 'employee doc1', 'folder_id': self.folder_test.id, 'partner_id': self.employee.work_contact_id.id},
            {'name': 'employee doc2', 'folder_id': self.folder_test.id, 'owner_id': self.employee.user_id.id},
            {'name': 'non employee', 'folder_id': self.folder_test.id},
        ])
        filtered_documents = self.env['documents.document'].search(action['domain'])
        self.assertEqual(
            len(filtered_documents.filtered(
                lambda doc: doc.owner_id == self.employee.user_id or doc.partner_id == self.employee.work_contact_id)),
            2,
            "Employee related documents are visible")
        self.assertEqual(len(filtered_documents), 2, "Only employee related documents are visible")
