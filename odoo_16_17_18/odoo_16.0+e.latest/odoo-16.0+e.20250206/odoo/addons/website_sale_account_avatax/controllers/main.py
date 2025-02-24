# coding: utf-8
from odoo import _
from odoo.exceptions import UserError

from odoo.addons.website_sale.controllers.main import WebsiteSale

class WebsiteSaleAvatax(WebsiteSale):

    def _get_shop_payment_errors(self, order):
        errors = super()._get_shop_payment_errors(order)
        if order.fiscal_position_id.is_avatax and order.state != 'done':
            try:
                order.button_update_avatax()
            except UserError as e:
                errors.append((
                    _("Validation Error"),
                    _("This address does not appear to be valid. Please make sure it has been filled in correctly. Error details: %s", e),
                ))
        return errors

    def _get_shop_payment_values(self, order, **kwargs):
        res = super()._get_shop_payment_values(order, **kwargs)
        res['on_payment_step'] = True
        return res

    def _update_so_external_taxes(self, order):
        super()._update_so_external_taxes(order)
        if order.fiscal_position_id.is_avatax:
            try:
                order.button_update_avatax()
            # Ignore any error here. It will be handled in next step of the checkout process (/shop/payment).
            except UserError:
                pass
