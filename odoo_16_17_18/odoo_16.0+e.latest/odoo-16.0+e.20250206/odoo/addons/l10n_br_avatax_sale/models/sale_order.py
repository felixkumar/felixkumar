# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, _
from odoo.tools import formatLang


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'l10n_br.account.avatax']

    def _l10n_br_get_date_avatax(self):
        return self.date_order

    def _l10n_br_get_operation_type(self):
        return "standardSales"

    def _l10n_br_get_invoice_refs(self):
        return {}

    def _action_confirm(self):
        self.button_l10n_br_avatax()
        return super()._action_confirm()

    def action_quotation_send(self):
        self.button_l10n_br_avatax()
        return super().action_quotation_send()

    def button_l10n_br_avatax(self):
        for avatax_order in self.filtered('is_l10n_br_avatax'):
            mapped_taxes, _ = avatax_order._l10n_br_map_avatax()
            to_flush = self.env['sale.order.line']
            for line, detail in mapped_taxes.items():
                line.tax_id = detail['tax_ids']
                to_flush += line

            # Trigger field computation due to changing the tax id. Do
            # this here because we will manually change the taxes.
            to_flush.flush_recordset(['price_tax', 'price_subtotal', 'price_total'])

            for line, detail in mapped_taxes.items():
                line.price_tax = detail['tax_amount']
                line.price_subtotal = detail['total']
                line.price_total = detail['tax_amount'] + detail['total']

            # This amount is wrong with price-included taxes.
            avatax_order.amount_untaxed = sum(avatax_order.order_line.mapped('price_subtotal'))

        return True

    def _l10n_br_get_avatax_lines(self):
        res = []
        for line in self.order_line.filtered(lambda l: not l.display_type):
            # Clear all taxes (e.g. default customer tax). Not every line will be sent to Avatax, so these
            # lines would keep their default taxes otherwise.
            line.tax_id = False

            # price-included taxes decrease price_subtotal, so we need to compute it ourselves
            subtotal = line.product_uom_qty * line.price_unit
            discount = subtotal * (line.discount / 100.0)
            res.append(self._l10n_br_build_avatax_line(line.product_id, subtotal, discount, line.id))

        return res

    def _compute_tax_totals(self):
        """ This overrides the standard values which come from
        account.tax. The percentage (amount field) on account.tax
        won't be correct in case of (partial) exemptions. As always we
        should rely purely on the values Avatax returns, not the
        values Odoo computes. This will create a single tax group
        using the amount_* fields on the order which come from Avatax.

        TODO: identical to the account_avatax_sale method apart from the amount_untaxed field. Make this generic in master
        """
        res = super()._compute_tax_totals()
        group_name = _('Untaxed Amount')
        for order in self.filtered('is_l10n_br_avatax'):
            currency = order.currency_id
            tax_totals = order.tax_totals

            tax_totals['groups_by_subtotal'] = {
                group_name: [{
                    'tax_group_name': _('Taxes'),
                    'tax_group_amount': order.amount_tax,
                    'tax_group_base_amount': order.amount_untaxed,
                    'formatted_tax_group_amount': formatLang(self.env, order.amount_tax, currency_obj=currency),
                    'formatted_tax_group_base_amount': formatLang(self.env, order.amount_untaxed, currency_obj=currency),
                    'tax_group_id': 1,
                    'group_key': 1,
                }]
            }
            tax_totals['subtotals'] = [{
                'name': group_name,
                'amount': order.amount_untaxed,
                'formatted_amount': formatLang(self.env, order.amount_untaxed, currency_obj=currency),
            }]
            tax_totals['amount_total'] = order.amount_total
            tax_totals['amount_untaxed'] = order.amount_untaxed
            tax_totals['formatted_amount_total'] = formatLang(self.env, order.amount_total, currency_obj=currency)

            order.tax_totals = tax_totals

        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):
        """ Override to clear tax_ids on lines. Brazilian taxes are variable and don't have the right amount set in Odoo (always 1%),
        so taxes are always unless recomputed with button_update_avatax. Although this automatically happens when needed, clearing the
        taxes here avoids potential confusion.
        """
        res = super()._prepare_invoice_line(**optional_values)

        if self.order_id.is_l10n_br_avatax:
            res['tax_ids'] = False

        return res
