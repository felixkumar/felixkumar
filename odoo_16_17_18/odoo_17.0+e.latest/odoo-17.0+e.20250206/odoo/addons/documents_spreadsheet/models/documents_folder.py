# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, models
from odoo.exceptions import ValidationError

class DocumentFolder(models.Model):
    _inherit = "documents.folder"

    @api.constrains('company_id')
    def _check_company_id(self):
        res = self.env['res.company'].sudo()._read_group(
            [('documents_spreadsheet_folder_id', 'in', self.ids)],
            ['documents_spreadsheet_folder_id'],
            ['id:count'],
            [('id:count', '>', 1)],
        )
        if res:
            folder_names = ', '.join([folder.display_name for folder, _count, in res])
            raise ValidationError(_("The following folders are the spreadsheet workspaces for several companies and, as"
                                    " such, can not be specific to any single company: %s", folder_names))
