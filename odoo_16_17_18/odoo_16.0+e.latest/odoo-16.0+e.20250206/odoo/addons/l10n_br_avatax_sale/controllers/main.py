# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.http import route
from odoo.addons.sale.controllers.portal import CustomerPortal

# TODO: identical to account_avatax_sale, make generic in master.
class CustomerPortalAvatax(CustomerPortal):

    @route()
    def portal_order_page(self, *args, **kwargs):
        response = super().portal_order_page(*args, **kwargs)
        if 'sale_order' not in response.qcontext:
            return response

        # Update taxes before customers see their quotation. This also ensures that tax validation
        # works (e.g. customer has valid address, ...). Otherwise errors will occur during quote
        # confirmation.
        order = response.qcontext['sale_order']
        if order.state in ('draft', 'sent') and order.is_l10n_br_avatax:
            order.button_l10n_br_avatax()

        return response
