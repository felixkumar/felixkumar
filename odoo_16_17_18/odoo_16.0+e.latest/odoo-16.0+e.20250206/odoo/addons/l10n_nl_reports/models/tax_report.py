# -*- coding: utf-8 -*-
from odoo import models

class DutchReportCustomHandler(models.AbstractModel):
    _name = 'l10n_nl.tax.report.handler'
    _inherit = 'account.generic.tax.report.handler'
    _description = 'Dutch Report Custom Handler'

    def _custom_options_initializer(self, report, options, previous_options=None):
        super()._custom_options_initializer(report, options, previous_options=previous_options)
        self.env['account.report'].browse(options['report_id'])._custom_options_add_integer_rounding(options, 'DOWN', previous_options=previous_options)

    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals):
        # Overridden to prevent having unnecessary lines from the generic tax report.
        return []
