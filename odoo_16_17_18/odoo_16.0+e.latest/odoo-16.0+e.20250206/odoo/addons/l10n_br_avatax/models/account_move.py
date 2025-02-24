# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models
from odoo.tools import formatLang, float_compare


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'l10n_br.account.avatax']

    def _post(self, soft=True):
        # Ensure taxes are correct before posting
        self.button_l10n_br_avatax()
        return super()._post(soft)

    def button_l10n_br_avatax(self):
        for move in self.filtered(lambda move: move.is_l10n_br_avatax and move.move_type in ("out_invoice", "out_refund")):
            move._l10n_br_avatax_compute_taxes()

    def _l10n_br_get_date_avatax(self):
        return self.invoice_date

    def _l10n_br_get_operation_type(self):
        return "salesReturn" if self.move_type == "out_refund" else "standardSales"

    def _l10n_br_get_invoice_refs(self):
        origin = self.reversed_entry_id
        if origin:
            return {
                "invoicesRefs": [
                    {
                        "type": "documentCode",
                        "documentCode": f"account.move_{origin.id}",
                    }
                ]
            }

        return {}

    def _compute_tax_totals(self):
        """ super() computes these using account.tax.compute_all(). For price-included taxes this will show the wrong totals
        because it uses the percentage amount on the tax which will always be 1%. This sets the correct totals using
        account.move.line fields set by _compute_avalara_taxes(). """
        res = super()._compute_tax_totals()
        for move in self:
            if not move.is_l10n_br_avatax or not move.tax_totals:
                continue

            currency = move.currency_id
            lines = move.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
            move.tax_totals['amount_total'] = move.currency_id.round(sum(lines.mapped('price_total')))
            move.tax_totals['formatted_amount_total'] = formatLang(move.env, move.tax_totals['amount_total'], currency_obj=currency)

            move.tax_totals['amount_untaxed'] = move.currency_id.round(sum(lines.mapped('price_subtotal')))
            move.tax_totals['formatted_amount_untaxed'] = formatLang(move.env, move.tax_totals['amount_untaxed'], currency_obj=currency)

            move.tax_totals['subtotals'] = [
                {
                    'amount': move.tax_totals['amount_untaxed'],
                    'formatted_amount': move.tax_totals['formatted_amount_untaxed'],
                    'name': 'Untaxed Amount'
                }
            ]

            for _, groups in move.tax_totals['groups_by_subtotal'].items():
                for group in groups:
                    group['tax_group_base_amount'] = move.tax_totals['amount_untaxed']
                    group['formatted_tax_group_base_amount'] = move.tax_totals['formatted_amount_untaxed']

        return res

    def _l10n_br_get_avatax_lines(self):
        res = []
        for line in self.invoice_line_ids.filtered(lambda l: l.display_type == 'product'):
            # Clear all taxes (e.g. default customer tax). Not every line will be sent to Avatax, so these
            # lines would keep these taxes otherwise.
            if line.parent_state != 'posted':
                line.tax_ids = False

            # price-included taxes decrease price_subtotal, so we need to compute it ourselves
            subtotal = line.quantity * line.price_unit
            discount = subtotal * (line.discount / 100.0)
            res.append(self._l10n_br_build_avatax_line(line.product_id, subtotal, discount, line.id))

        return res

    def _l10n_br_avatax_compute_taxes(self):
        """ This calls the Avatax API and will set the taxes it returns on this invoice. """
        if not self.is_l10n_br_avatax:
            return

        mapped_taxes, summary = self._l10n_br_map_avatax()

        for line, detail in mapped_taxes.items():
            line.tax_ids = detail['tax_ids']
            line.price_total = detail['tax_amount'] + detail['total']
            line.price_subtotal = detail['total']

        # Check that Odoo computation = Avatax computation
        for record in self:
            for tax, avatax_amount in summary[record].items():
                tax_line = record.line_ids.filtered(lambda l: l.tax_line_id == tax)

                # Tax avatax returns is opposite from aml balance (avatax is positive on invoice, negative on refund)
                avatax_balance = -avatax_amount

                # Check that the computed taxes are close enough. For exemptions this will never be the case
                # since Avatax will return the non-exempt rate%. In that case this will manually fix the tax
                # lines to what Avatax says they should be.
                if float_compare(tax_line.balance, avatax_balance, precision_rounding=record.currency_id.rounding) != 0:
                    tax_line.balance = avatax_balance
