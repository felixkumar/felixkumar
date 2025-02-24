from odoo import models, fields, api
from lxml.etree import Element
class L10nNlTaxReportSBRWizard(models.TransientModel):
    _inherit = 'l10n_nl_reports_sbr.tax.report.wizard'

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    password = fields.Char(default=lambda self: self.env.company.l10n_nl_reports_sbr_password, store=True)

    def send_xbrl(self):
        # Extends to write the password on the company if it didn't exist.
        # TODO change this in master to add the password directly in the base SBR module.
        sudo_company = self.company_id.sudo()
        if self.password != sudo_company.l10n_nl_reports_sbr_password:
            password_bytes = bytes(self.password or '', 'utf-8')
            # Should raise if the password is not the correct one.
            sudo_company._l10n_nl_get_certificate_and_key_bytes(password_bytes)
            sudo_company.l10n_nl_reports_sbr_password = self.password
        return super().send_xbrl()

    def _additional_processing(self, options, kenmerk, closing_move):
        # OVERRIDE
        self.env['l10n_nl_reports_sbr.status.service'].create({
            'kenmerk': kenmerk,
            'company_id': self.env.company.id,
            'report_name': self.env['account.report'].browse(options['report_id']).name,
            'closing_entry_id': closing_move.id,
            'is_test': self.is_test,
        })._cron_process_submission_status()

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        # TODO this needs to go in the merge of the SBR modules (company_id should be set, invisible, in the view)
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == 'form':
            node = arch.find(".//field[@name='can_report_be_sent']...")
            if node is not None:
                pwd_element = Element('field')
                pwd_element.set('name', 'company_id')
                pwd_element.set('invisible', '1')
                node.append(pwd_element)
            if self.env.company.l10n_nl_reports_sbr_password:
                password_node = arch.find(".//field[@name='password']")
                password_node.set('invisible', '1')
        return arch, view
