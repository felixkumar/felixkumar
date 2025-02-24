# -*- coding: utf-8 -*-

from odoo import api, models, fields


class SaleOrderLines(models.Model):
    _inherit = 'sale.order.line'

    barcode_scan = fields.Char(string='Product Barcode', help="Here you can provide the barcode for the product")
    @api.onchange('barcode_scan')
    def _onchange_barcode_scan(self):
        product_rec = self.env['product.product']
        if self.barcode_scan:
            product = product_rec.search([('barcode', '=', self.barcode_scan)])
            self.product_id = self.product_id
            
    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.barcode_scan = self.product_id.barcode
        print(self.barcode_scan)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
