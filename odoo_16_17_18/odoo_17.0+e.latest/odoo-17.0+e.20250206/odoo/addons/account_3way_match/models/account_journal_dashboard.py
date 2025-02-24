# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.osv import expression

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def open_action(self):
        action = super(AccountJournal, self).open_action()
        view = self.env.ref('account.action_move_in_invoice_type')
        if view and action.get("id") == view.id:
            account_purchase_filter = self.env.ref('account_3way_match.account_invoice_filter_inherit_account_3way_match', False)
            action['search_view_id'] = account_purchase_filter and [account_purchase_filter.id, account_purchase_filter.name] or False
        return action

    def _patch_dashboard_query_3way_match(self, query):
        query.add_where("("
            "account_move.move_type NOT IN %s "
            "OR account_move.release_to_pay in ('yes', 'exception') "
        ")", [
            tuple(self.env['account.move'].get_purchase_types(include_receipts=True)),
        ])

    def _get_open_bills_to_pay_query(self):
        query = super()._get_open_bills_to_pay_query()
        self._patch_dashboard_query_3way_match(query)
        return query

    def _get_draft_bills_query(self):
        # OVERRIDE
        domain_sale = [
            ('journal_id', 'in', self.filtered(lambda j: j.type == 'sale').ids),
            ('move_type', 'in', self.env['account.move'].get_sale_types(include_receipts=True))
        ]

        domain_purchase = [
            ('journal_id', 'in', self.filtered(lambda j: j.type == 'purchase').ids),
            ('move_type', 'in', self.env['account.move'].get_purchase_types(include_receipts=False)),
            '|',
            ('invoice_date_due', '<', fields.Date.today()),
            ('release_to_pay', '=', 'yes')
        ]
        domain = expression.AND([
            [('state', '=', 'draft'), ('payment_state', 'in', ('not_paid', 'partial'))],
            expression.OR([domain_sale, domain_purchase])
        ])
        return self.env['account.move']._where_calc([
            *self.env['account.move']._check_company_domain(self.env.companies),
            *domain
        ])

    def _get_late_bills_query(self):
        query = super()._get_late_bills_query()
        self._patch_dashboard_query_3way_match(query)
        return query
