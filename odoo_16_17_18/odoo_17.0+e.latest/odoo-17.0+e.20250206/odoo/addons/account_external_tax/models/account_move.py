# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, _
from odoo.tools import formatLang


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'account.external.tax.mixin']

    def _compute_tax_totals(self):
        """ super() computes these using account.tax.compute_all(). For price-included taxes this will show the wrong totals
        because it uses the percentage amount on the tax which will always be 1%. This sets the correct totals using
        account.move.line fields set by `_set_external_taxes()`. """
        res = super()._compute_tax_totals()
        for move in self.filtered(lambda move: move.is_tax_computed_externally and move.tax_totals):
            currency = move.currency_id
            lines = move.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
            move.tax_totals['amount_total'] = move.currency_id.round(sum(lines.mapped('price_total')))
            move.tax_totals['formatted_amount_total'] = formatLang(self.env, move.tax_totals['amount_total'],
                                                                   currency_obj=currency)

            move.tax_totals['amount_untaxed'] = move.currency_id.round(sum(lines.mapped('price_subtotal')))
            move.tax_totals['formatted_amount_untaxed'] = formatLang(self.env, move.tax_totals['amount_untaxed'],
                                                                     currency_obj=currency)

            move.tax_totals['subtotals'] = [
                {
                    'amount': move.tax_totals['amount_untaxed'],
                    'formatted_amount': move.tax_totals['formatted_amount_untaxed'],
                    'name': move.tax_totals['subtotals'][0]['name'] if len(move.tax_totals['subtotals']) == 1 else _("Untaxed Amount")
                }
            ]

            for groups in move.tax_totals['groups_by_subtotal'].values():
                for group in groups:
                    group['tax_group_base_amount'] = move.tax_totals['amount_untaxed']
                    group['formatted_tax_group_base_amount'] = move.tax_totals['formatted_amount_untaxed']

        return res

    def button_draft(self):
        res = super().button_draft()
        self._filtered_external_tax_moves()._uncommit_external_taxes()
        return res

    def unlink(self):
        self._filtered_external_tax_moves()._void_external_taxes()
        return super().unlink()

    def _post(self, soft=True):
        """ Ensure taxes are correct before posting. """
        self._get_and_set_external_taxes_on_eligible_records()
        return super()._post(soft=soft)

    def _filtered_external_tax_moves(self):
        return self.filtered(lambda move: move.is_tax_computed_externally and
                                          move.move_type in ('out_invoice', 'out_refund') and
                                          not move._is_downpayment())

    def _get_and_set_external_taxes_on_eligible_records(self):
        """ account.external.tax.mixin override. """
        eligible_moves = self._filtered_external_tax_moves().filtered(lambda move: move.state != 'posted')
        eligible_moves._set_external_taxes(*eligible_moves._get_external_taxes())
        return super()._get_and_set_external_taxes_on_eligible_records()

    def _get_lines_eligible_for_external_taxes(self):
        """ account.external.tax.mixin override. """
        return self.invoice_line_ids.filtered(lambda line: line.display_type == 'product' and not line._get_downpayment_lines())

    def _get_date_for_external_taxes(self):
        """ account.external.tax.mixin override. """
        return self.invoice_date

    def _get_line_data_for_external_taxes(self):
        """ account.external.tax.mixin override. """
        res = []
        for line in self._get_lines_eligible_for_external_taxes():
            # Clear all taxes (e.g. default customer tax). Not every line will be sent to the external tax
            # calculation service, those lines would keep their default taxes otherwise.
            if line.parent_state != 'posted':
                line.tax_ids = False

            res.append({
                "id": line.id,
                "model_name": line._name,
                "product_id": line.product_id,
                "qty": line.quantity,
                "price_subtotal": line.price_subtotal,
                "price_unit": line.price_unit,
                "discount": line.discount,
                "is_refund": self.move_type == 'out_refund',
            })

        return res

    def _set_external_taxes(self, mapped_taxes, summary):
        """ account.external.tax.mixin override. """
        for line, detail in mapped_taxes.items():
            line.tax_ids = detail['tax_ids']
            line.price_total = detail['tax_amount'] + detail['total']
            line.price_subtotal = detail['total']

        for record in self:
            for tax, external_amount in summary.get(record, {}).items():
                tax_lines = record.line_ids.filtered(lambda l: l.tax_line_id == tax)
                if not tax_lines:
                    continue

                # Check that the computed taxes are close enough. For exemptions this could not be the case
                # since some integrations will return the non-exempt rate%. In that case this will manually fix the tax
                # lines to what the external service says they should be.
                computed_taxes = sum(tax_lines.mapped('amount_currency'))
                if record.currency_id.compare_amounts(computed_taxes, external_amount) != 0:
                    diff = external_amount - computed_taxes
                    for i, tax_line in enumerate(tax_lines):
                        line_diff = record.currency_id.round(diff / (len(tax_lines) - i))
                        diff -= line_diff
                        tax_line.amount_currency += line_diff
