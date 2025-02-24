from odoo import models, fields, _
from odoo.tools import format_date

# Used for printing a task report

class Task(models.Model):
    _inherit = 'project.task'

    l10n_din5008_template_data = fields.Binary(compute='_compute_l10n_din5008_template_data')
    l10n_din5008_document_title = fields.Char(compute='_compute_l10n_din5008_document_title')

    def _compute_l10n_din5008_template_data(self):
        for record in self:
            record.l10n_din5008_template_data = [
                (_("Date:"), format_date(self.env, fields.Date.today()))
            ]

    def _compute_l10n_din5008_document_title(self):
        for record in self:
            record.l10n_din5008_document_title = record.name
