# -*- coding: utf-8 -*-

import io
import zipfile

from odoo import http, fields
from odoo.tests.common import HttpCase


class TestDocumentsRoutes(HttpCase):
    def setUp(self):
        super().setUp()
        self.folder_a = self.env['documents.folder'].create({
            'name': 'folder A',
        })
        self.document_txt = self.env['documents.document'].create({
            'raw': b'TEST',
            'name': 'file.txt',
            'mimetype': 'text/plain',
            'folder_id': self.folder_a.id,
        })

    def test_documents_content(self):
        self.authenticate('admin', 'admin')
        response = self.url_open('/documents/content/%s' % self.document_txt.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'TEST')

    def test_documents_zip(self):
        self.authenticate('admin', 'admin')
        response = self.url_open('/document/zip', data={
            'file_ids': [self.document_txt.id],
            'zip_name': 'testZip.zip',
            'csrf_token': http.Request.csrf_token(self),
        })
        self.assertEqual(response.status_code, 200)
        with io.BytesIO(response.content) as buffer, zipfile.ZipFile(buffer) as zipfile_obj:
            self.assertEqual(zipfile_obj.read(self.document_txt.name), b'TEST')

    def test_documents_from_web(self):
        self.authenticate('admin', 'admin')
        raw_gif = b"R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs="
        document_gif = self.env['documents.document'].create({
            'raw': raw_gif,
            'name': 'file.gif',
            'mimetype': 'image/gif',
            'folder_id': self.folder_a.id,
        })
        response = self.url_open('/web/image/%s?model=documents.document' % document_gif.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, raw_gif)

    def test_documents_share_expired_link(self):
        self.authenticate('admin', 'admin')
        # Test on available link
        tomorrow = fields.Date.from_string(fields.Date.add(fields.Date.today(), days=1))
        vals = {
            'document_ids': [(6, 0, [self.document_txt.id])],
            'folder_id': self.folder_a.id,
            'date_deadline': tomorrow,
            'type': 'ids',
        }
        self.result_share_documents_act = self.env['documents.share'].create(vals)
        response = self.url_open(self.result_share_documents_act.full_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'TEST', "Failed route test on available link")

        # Test on expired link
        vals = {
            'document_ids': [(6, 0, [self.document_txt.id])],
            'folder_id': self.folder_a.id,
            'date_deadline': '2001-11-05',
            'type': 'ids',
        }
        self.result_share_documents_act = self.env['documents.share'].create(vals)
        response = self.url_open(self.result_share_documents_act.full_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'This link has expired' in response.content, "Failed route test on expired link")
