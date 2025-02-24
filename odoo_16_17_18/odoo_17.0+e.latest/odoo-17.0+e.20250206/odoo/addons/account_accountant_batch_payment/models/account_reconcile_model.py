# -*- coding: utf-8 -*-

from odoo import models


class AccountReconcileModel(models.Model):
    _inherit = 'account.reconcile.model'

    def _get_invoice_matching_batch_payments_candidates(self, st_line, partner):
        assert self.rule_type == 'invoice_matching'
        self.env['account.batch.payment'].flush_model()

        _numerical_tokens, exact_tokens, _text_tokens = self._get_invoice_matching_st_line_tokens(st_line)
        if not exact_tokens:
            return

        batches = self.env['account.batch.payment'].search([('state', '!=', 'reconciled'), ('name', 'in', exact_tokens)])
        if not batches:
            return

        aml_domain = self._get_invoice_matching_amls_domain(st_line, partner)
        query = self.env['account.move.line']._where_calc(aml_domain)
        tables, where_clause, where_params = query.get_sql()

        self._cr.execute(
            f"""
                SELECT DISTINCT account_move_line.id
                FROM {tables}
                JOIN account_payment pay ON pay.id = account_move_line.payment_id
                JOIN account_batch_payment batch
                    ON batch.id = pay.batch_payment_id
                    AND batch.id = ANY(%s)
                    AND batch.state != 'reconciled'
                WHERE {where_clause}
            """,
            [batches.ids] + where_params,
        )
        candidate_ids = [r[0] for r in self._cr.fetchall()]
        if candidate_ids:
            return {
                'allow_auto_reconcile': True,
                'amls': self.env['account.move.line'].browse(candidate_ids),
            }

    def _get_invoice_matching_rules_map(self):
        # EXTENDS account
        res = super()._get_invoice_matching_rules_map()
        res[0].append(self._get_invoice_matching_batch_payments_candidates)
        return res
