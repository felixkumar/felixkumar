# -*- coding: utf-8 -*-

from collections import defaultdict

from dateutil.relativedelta import relativedelta

from odoo import models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _post(self, soft=True):
        posted_moves = super()._post(soft=soft)
        for move in posted_moves:
            if not move.invoice_line_ids.subscription_id:
                continue
            if move.move_type != 'out_invoice':
                if move.move_type == 'out_refund':
                    body = _("The following refund %s has been made on this contract. Please check the next invoice date if necessary.", move._get_html_link())
                    for so in move.invoice_line_ids.subscription_id:
                        # Normally, only one subscription_id per move, but we handle multiple contracts as a precaution
                        so.message_post(body=body)
                continue
            aml_by_subscription = defaultdict(lambda: self.env['account.move.line'])
            for aml in move.invoice_line_ids:
                aml_by_subscription[aml.subscription_id] |= aml
            for subscription, aml in aml_by_subscription.items():
                sale_order = aml.sale_line_ids.order_id
                if subscription != sale_order:
                    # we are invoicing an upsell
                    continue
                # Normally, only one period_end should exist
                end_dates = [ed for ed in aml.mapped('subscription_end_date') if ed]
                if end_dates and max(end_dates) > subscription.next_invoice_date:
                    subscription.next_invoice_date = max(end_dates) + relativedelta(days=1)
        return posted_moves
