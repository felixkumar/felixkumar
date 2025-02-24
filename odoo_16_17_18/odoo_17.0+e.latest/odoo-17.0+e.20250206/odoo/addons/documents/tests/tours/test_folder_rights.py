# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("post_install", "-at_install")
class TestDocumentFolderRights(HttpCase):
    def test_document_folder_rights_for_multi_company_tour(self):
        company_a = self.env['res.company'].create({'name': 'Company_A'})
        self.env.ref('base.user_admin').company_ids = [self.env.company.id, company_a.id]
        self.env['documents.folder'].create({
            "name": "Workspace1",
            "company_id": self.env.company.id,
        })

        self.start_tour("/web", 'test_document_folder_rights_for_multi_company', login='admin')
