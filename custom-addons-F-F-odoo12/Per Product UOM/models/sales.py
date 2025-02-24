# -*- coding: utf-8 -*-
from odoo import api, models, fields


# For some reason, odoo's views had trouble finding the category of the uom in sale.order.line on the fly
# This keeps the record in the DB, and allows me to filter UOM categories.
class NewSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    # These computed fields are for calculating the domain on a form edit
    relcatid = fields.Many2one(related='product_uom.category_id', store=True)

    # The default onchange returns a domain, but it also does other stuff. Since we set a default domain, we want don't want it to return a domain
    # So we make a call to the original onchange, and just absorb the return value.  It still does all the other stuff
    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        # We call super and assign the return value to this variable. We do nothing with it, on purpose.
        domain = super(NewSaleOrderLine, self).product_id_change()
        # the original function returned the above domain, but instead we return nothing and just use the default domain in the view
        return {}