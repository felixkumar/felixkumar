# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class CustomerStatementReport(models.AbstractModel):
    _name = 'report.l10n_account_customer_statements.customer_statements'
    _description = "Customer Statements Report"

    def _get_report_values(self, docids, data=None):
        docs = self.env['res.partner'].browse(docids)
        options = self.env.context.get('report_options', False)
        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': docs,
            'company': self.env.company,
            **(docs._prepare_customer_statement_values(options) if docs.ids else {})
        }
