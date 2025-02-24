from odoo import models, api, fields, _
from odoo.http import request
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _cart_update(self, product_id, line_id=None, add_qty=0, set_qty=0, **kwargs):
        self.ensure_one()
        self = self.with_company(self.company_id)

        if self.state != 'draft':
            request.session.pop('sale_order_id', None)
            request.session.pop('website_sale_cart_quantity', None)
            raise UserError(_('It is forbidden to modify a sales order which is not in draft status.'))

        product = self.env['product.product'].browse(product_id).exists()
        if not product:
            product = self.env['product.template'].browse(product_id).exists()
            if product:
                print(product)

        if not product or not product._is_add_to_cart_allowed():
            raise UserError(_("The given product does not exist therefore it cannot be added to cart."))

        if product.lst_price == 0 and product.website_id.prevent_zero_price_sale:
            raise UserError(_("The given product does not have a price therefore it cannot be added to cart."))

        if line_id is not False:
            order_line = self._cart_find_product_line(product_id, line_id, **kwargs)[:1]
        else:
            order_line = self.env['sale.order.line']

        try:
            if add_qty:
                add_qty = int(add_qty)
        except ValueError:
            add_qty = 1

        try:
            if set_qty:
                set_qty = int(set_qty)
        except ValueError:
            set_qty = 0

        quantity = 0
        if set_qty:
            quantity = set_qty
        elif add_qty is not None:
            if order_line:
                quantity = order_line.product_uom_qty + (add_qty or 0)
            else:
                quantity = add_qty or 0

        if quantity > 0:
            quantity, warning = self._verify_updated_quantity(
                order_line,
                product_id,
                quantity,
                **kwargs,
            )
        else:
            # If the line will be removed anyway, there is no need to verify
            # the requested quantity update.
            warning = ''

        if order_line and quantity <= 0:
            # Remove zero or negative lines
            order_line.unlink()
            order_line = self.env['sale.order.line']
        elif order_line:
            # Update existing line
            update_values = self._prepare_order_line_update_values(order_line, quantity, **kwargs)
            if update_values:
                self._update_cart_line_values(order_line, update_values)
        elif quantity >= 0:
            # Create new line
            order_line_values = self._prepare_order_line_values(product_id, quantity, **kwargs)
            order_line = self.env['sale.order.line'].sudo().create(order_line_values)

        return {
            'line_id': order_line.id,
            'quantity': quantity,
            'option_ids': list(set(order_line.option_line_ids.filtered(lambda l: l.order_id == order_line.order_id).ids)),
            'warning': warning,
        }
