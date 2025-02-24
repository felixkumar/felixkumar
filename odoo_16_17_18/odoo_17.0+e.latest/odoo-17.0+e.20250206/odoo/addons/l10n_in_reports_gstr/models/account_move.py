# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date

from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_in_exception = fields.Html("Exception")
    l10n_in_gst_return_period_id = fields.Many2one("l10n_in.gst.return.period", "GST Return Period")
    l10n_in_gstr2b_reconciliation_status = fields.Selection(selection=[
        ("pending", "Pending"),
        ("matched", "Fully Matched"),
        ("partially_matched", "Partially Matched"),
        ("exception", "Exception"),
        ("bills_not_in_gstr2", "Bills Not in GSTR-2"),
        ("gstr2_bills_not_in_odoo", "GSTR-2 Bills not in Odoo")],
        string="GSTR-2B Reconciliation",
        readonly=True,
        default="pending"
    )
    l10n_in_reversed_entry_warning = fields.Boolean('Display reversed entry warning', compute="_compute_l10n_in_reversed_entry_warning")

    @api.depends('move_type', 'reversed_entry_id', 'state', 'invoice_date')
    def _compute_l10n_in_reversed_entry_warning(self):
        for move in self:
            if move.country_code == 'IN' and move.move_type == 'out_refund' and move.state == 'draft' and move.invoice_date and move.reversed_entry_id and move.line_ids.tax_tag_ids:
                fiscal_year_start_month = (int(move.company_id.fiscalyear_last_month) % 12) + 1
                fiscal_year_start_date = date(move.invoice_date.year, fiscal_year_start_month, 1)
                if move.invoice_date.month <= 11:
                    fiscal_year_start_date = fiscal_year_start_date.replace(year=move.invoice_date.year - 1)
                move.l10n_in_reversed_entry_warning = move.reversed_entry_id.invoice_date < fiscal_year_start_date
            else:
                move.l10n_in_reversed_entry_warning = False

    def _post(self, soft=True):
        for invoice in self:
            if invoice.l10n_in_gstr2b_reconciliation_status == "gstr2_bills_not_in_odoo":
                invoice.l10n_in_gstr2b_reconciliation_status = "pending"
        return super(AccountMove, self)._post(soft=soft)
