# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _default_documents_spreadsheet_folder_id(self):
        folder = self.env.ref('documents_spreadsheet.documents_spreadsheet_folder', raise_if_not_found=False)
        if not folder or folder.company_id:
            return False
        return folder

    documents_spreadsheet_folder_id = fields.Many2one('documents.folder', check_company=True,
        default=_default_documents_spreadsheet_folder_id)

    @api.constrains('documents_spreadsheet_folder_id')
    def _check_documents_spreadsheet_folder_id(self):
        for company in self:
            folder = company.documents_spreadsheet_folder_id
            if folder.company_id and folder.company_id != company:
                raise ValidationError(_("The company of %s should either be undefined or set to %s. Otherwise, it is not "
                                        "possible to link the workspace to the company.", folder.display_name, company.display_name))
