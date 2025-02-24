# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class ProductProduct(models.Model):
    _inherit = "product.template"

    is_add_analytic_account = fields.Boolean(string="Add Analytic Account?")
    
    
class Product(models.Model):
    _inherit = "product.product"

    def name_get(self):
        # if self.env.company.is_oxford and self._context.get('default_move_type') and self._context.get('default_move_type') == 'out_invoice' :
        if self._context.get('default_move_type') and self._context.get('default_move_type') == 'out_invoice' :
            result = []
            self.sudo().read(['name', 'default_code'], load=False)
            for rec in self:
                result.append((rec.id, rec.default_code))
            return result
        else:
            res = super().name_get()
            return res

    @api.depends_context('partner_id')
    def _compute_partner_ref(self):
        if self._context.get('default_move_type') and self._context.get('default_move_type') == 'out_invoice':
            for product in self:
                for supplier_info in product.seller_ids:
                    if supplier_info.partner_id.id == product._context.get('partner_id'):
                        product_name = supplier_info.product_name or product.default_code or product.name
                        product.partner_ref = '%s%s' % (product.code and '[%s] ' % product.code or '', product_name)
                        break
                else:
                    product.partner_ref = product.name
        else:
            return super()._compute_partner_ref()

