# -*- coding: utf-8 -*-

from odoo import tools
from odoo.addons.mail.tests.common import MailCommon
from odoo.addons.test_mail.data.test_mail_data import MAIL_EML_ATTACHMENT
from odoo.tests.common import RecordCapturer
from odoo.tools import mute_logger


class TestMailGateway(MailCommon):
    """ Test document creation/update on incoming mail.

    Mainly that the partner_id is correctly set on the created document.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.folder = cls.env['documents.folder'].create({
            'name': 'folder',
        })
        cls.share_link = cls.env['documents.share'].create({
            'folder_id': cls.folder.id,
            'name': 'share_link_folder',
            'email_drop': True,
            'alias_name': 'shareFolder',
        })
        cls.alias = cls.env['mail.alias'].create({
            'alias_name': 'inbox-test',
            'alias_model_id': cls.env['ir.model']._get('documents.document').id,
            'alias_parent_model_id': cls.env['ir.model']._get('documents.share').id,
            'alias_parent_thread_id': cls.share_link.id,
            'alias_defaults': f"{{'folder_id': {cls.folder.id}, 'create_share_id': {cls.share_link.id}}}",
            'alias_contact': 'everyone',
        })
        cls.email_with_no_partner = tools.email_normalize('non-existing@test.com')
        cls.pre_existing_partner = cls.env['res.partner'].find_or_create('existing@test.com')
        cls.default_partner = cls.env['res.partner'].find_or_create('default@test.com')
        cls.email_filenames = ['attachment', 'original_msg.eml']
        cls.document = cls.env['documents.document'].with_context(mail_create_nolog=True).create({
            'datas': b"R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs=",
            'name': 'file.gif',
            'mimetype': 'image/gif',
            'folder_id': cls.env['documents.folder'].create({'name': 'folderA'}).id,
        })

    def send_test_mail_with_attachment(self, email_from, msg_id=None, references=None):
        with self.mock_mail_gateway():
            self.format_and_process(
                MAIL_EML_ATTACHMENT,
                email_from,
                f'inbox-test@{self.alias_domain}',
                subject='Test document creation on incoming mail',
                target_model='documents.document',
                references=references or '<f3b9f8f8-28fa-2543-cab2-7aa68f679ebb@odoo.com>',
                msg_id=msg_id or '<cb7eaf62-58dc-2017-148c-305d0c78892f@odoo.com>',
            )
        documents = self.env['documents.document'].search([('name', 'in', self.email_filenames)])
        self.assertEqual(len(documents), len(self.email_filenames))
        return documents

    def test_initial_values(self):
        self.assertFalse(self.env['res.partner'].search([('email', '=', self.email_with_no_partner)]))
        self.assertFalse(self.env['documents.document'].search([('name', 'in', self.email_filenames)]))

    def test_reply_with_attachment(self):
        """ Test reply with an attachment to a message posted on a document. """
        message_ask_files = self.document.with_user(self.user_employee).message_post(
            subject='Could you send the missing files ?', subtype_xmlid='mail.mt_comment')
        with self.mock_mail_gateway(), RecordCapturer(self.env['documents.document'], []) as capture:
            self.format_and_process(
                MAIL_EML_ATTACHMENT,
                'ihavethefiles@example.com',
                'inbox-test@test.com',
                msg_id='<dc8eaf62-58dc-2017-148c-305d0c78892f@odoo.com>',
                references=message_ask_files.message_id,
                subject='Please find the files in attachment',
                target_model='documents.document',
            )

        self.assertFalse(capture.records, "No new document has been created")
        self.assertEqual(self.env['ir.attachment'].search_count(
            [('res_id', '=', self.document.id), ('res_model', '=', self.document._name)]), 3)
        doc_messages = self.env['mail.message'].search(
            [('res_id', '=', self.document.id), ('model', '=', self.document._name)])
        self.assertEqual(len(doc_messages), 2)
        self.assertListEqual(
            doc_messages.mapped('subject'),
            ['Please find the files in attachment', 'Could you send the missing files ?'])

    @mute_logger('odoo.addons.mail.models.mail_thread')
    def test_set_contact_non_existing_partner(self):
        for document in self.send_test_mail_with_attachment(self.email_with_no_partner):
            self.assertFalse(document.partner_id)

    @mute_logger('odoo.addons.mail.models.mail_thread')
    def test_set_contact_existing_partner(self):
        for document in self.send_test_mail_with_attachment(self.pre_existing_partner.email):
            self.assertFalse(document.partner_id)

    @mute_logger('odoo.addons.mail.models.mail_thread')
    def test_set_contact_default_partner_non_existing_partner(self):
        self.share_link.partner_id = self.default_partner
        for document in self.send_test_mail_with_attachment(self.email_with_no_partner):
            self.assertEqual(document.partner_id, self.default_partner)

    @mute_logger('odoo.addons.mail.models.mail_thread')
    def test_set_contact_default_partner_existing_partner(self):
        self.share_link.partner_id = self.default_partner
        for document in self.send_test_mail_with_attachment(self.pre_existing_partner.email):
            self.assertEqual(document.partner_id, self.default_partner)
