from odoo import models


class ItalianReportCustomHandler(models.AbstractModel):
    _name = 'l10n_it.report.handler'
    _inherit = 'account.tax.report.handler'
    _description = 'Italian Report Custom Handler'

    def _custom_options_initializer(self, report, options, previous_options=None):
        super()._custom_options_initializer(report, options, previous_options=previous_options)

        report._custom_options_add_integer_rounding(options, 'HALF-UP', previous_options=previous_options)
