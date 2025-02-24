# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests.common import HttpCase, TransactionCase, new_test_user
from odoo.modules.module import get_module_resource
from odoo.tools import file_open

from uuid import uuid4
import base64


TEXT = base64.b64encode(bytes("TEST", "utf-8"))
GIF = b"R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs="


class SpreadsheetTestCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(SpreadsheetTestCommon, cls).setUpClass()
        cls.folder = cls.env["documents.folder"].create({"name": "Test folder"})
        cls.spreadsheet_user = new_test_user(
            cls.env, login="spreadsheetDude", groups="documents.group_documents_user"
        )

    def create_spreadsheet(self, values=None, *, user=None, name="Untitled Spreadsheet"):
        if values is None:
            values = {}
        return (
            self.env["documents.document"]
            .with_user(user or self.env.user)
            .create({
                "raw": TEXT,
                "folder_id": self.folder.id,
                "handler": "spreadsheet",
                "mimetype": "application/o-spreadsheet",
                "name": name,
                **values,
            })
        )

    def get_revision(self, spreadsheet):
        return (
            # should be sorted by `create_date` but tests are so fast,
            # there are often no difference between consecutive revision creation.
            spreadsheet.with_context(active_test=False)
                .spreadsheet_revision_ids.sorted("id")[-1:]
                .revision_id or "START_REVISION"
        )

    def new_revision_data(self, spreadsheet, **kwargs):
        return {
            "id": spreadsheet.id,
            "type": "REMOTE_REVISION",
            "clientId": "john",
            "commands": [{"type": "A_COMMAND"}],
            "nextRevisionId": uuid4().hex,
            "serverRevisionId": self.get_revision(spreadsheet),
            **kwargs,
        }

    def snapshot(self, spreadsheet, server_revision_id, snapshot_revision_id, data):
        return spreadsheet.dispatch_spreadsheet_message({
            "type": "SNAPSHOT",
            "nextRevisionId": snapshot_revision_id,
            "serverRevisionId": server_revision_id,
            "data": data,
        })


class SpreadsheetTestTourCommon(SpreadsheetTestCommon, HttpCase):
    @classmethod
    def setUpClass(cls):
        super(SpreadsheetTestTourCommon, cls).setUpClass()
        cls.spreadsheet_user.partner_id.country_id = cls.env.ref("base.us")
        cls.env['res.users'].browse(2).partner_id.country_id = cls.env.ref("base.be")
        # Avoid interference from the demo data which rename the admin user
        cls.env['res.users'].browse(2).write({"name": "AdminDude"})
        data_path = get_module_resource('documents_spreadsheet', 'tests', 'test_spreadsheet_data.json')
        with file_open(data_path, 'rb') as f:
            cls.spreadsheet = cls.env["documents.document"].create({
                "handler": "spreadsheet",
                "folder_id": cls.folder.id,
                "raw": f.read(),
                "name": "Res Partner Test Spreadsheet"
            })
