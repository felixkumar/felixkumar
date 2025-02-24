# -*- coding: utf-8 -*-

import datetime
from collections import Counter
from odoo import models, fields, api, _
from odoo.osv import expression


class WebsiteSnippetFilter(models.Model):
    _inherit = 'website.snippet.filter'

    def _get_hardcoded_sample(self, model):
        samples = super()._get_hardcoded_sample(model)
        if model._name == 'product.public.category':
            data = [{
                'name': _('Category 1'),
                'product_tmpl_ids': '',
                'image_512': b'',
            }, {
                'name': _('Category 2'),
                'product_tmpl_ids': '',
                'image_512': b'',
            }, {
                'name': _('Category 3'),
                'product_tmpl_ids': '',
                'image_512': b'',
            }, {
                'name': _('Category 4'),
                'product_tmpl_ids': '',
                'image_512': b'',
            }, {
                'name': _('Category 5'),
                'product_tmpl_ids': '',
                'image_512': b'',
            }, {
                'name': _('Category 6'),
                'product_tmpl_ids': '',
                'image_512': b'',
            }]
            merged = []
            for index in range(0, max(len(samples), len(data))):
                merged.append({**samples[index % len(samples)], **data[index % len(data)]})
                # merge definitions
            samples = merged
        return samples

    def _get_products_discount_products(self, website, limit, domain, context):
        products = []
        price_list = website.get_current_pricelist()
        product_template_snippet = context.get('product_template_snippet', False)
        pl_items = price_list.item_ids.filtered(lambda r: (
                    (not r.date_start or r.date_start <= datetime.datetime.today()) and (not r.date_end or r.date_end > datetime.datetime.today())))
        products_ids = []
        if pl_items.filtered(lambda r: r.applied_on in ['3_global']):
            if product_template_snippet:
                products = self.env['product.template'].with_context(display_default_code=False, add2cart_rerender=True).search(domain, limit=limit)
            else:
                products = self.env['product.product'].with_context(display_default_code=False, add2cart_rerender=True).search(domain, limit=limit)
        else:
            for line in pl_items:
                if line.applied_on in ['1_product']:
                    if product_template_snippet:
                        products_ids.extend(line.product_id.ids)
                    else:
                        products_ids.extend(line.product_tmpl_id.product_variant_ids.ids)
                elif line.applied_on in ['0_product_variant']:
                    products_ids.extend(line.product_id.ids)
                    # append line.product_id
            products_ids = list(set(products_ids))
        if products_ids:
            domain = expression.AND([domain, [('id', 'in', products_ids)]])
            if product_template_snippet:
                products = self.env['product.template'].with_context(display_default_code=False, add2cart_rerender=True).search(domain, limit=limit)
            else:
                products = self.env['product.product'].with_context(display_default_code=False, add2cart_rerender=True).search(domain, limit=limit)
        return products

    def _render(self, template_key, limit, search_domain=None, with_sample=False):
        website = self.env['website'].get_current_website()
        if not website.display_out_of_stock and (self.model_name == "product.product" or self.model_name == "product.template"):
            search_domain = expression.AND([search_domain, ['|', ('free_qty', '>', 0),
                                                            ('allow_out_of_stock_order', '=', True)]])

        res = super(WebsiteSnippetFilter, self)._render(template_key=template_key,
                                                        limit=limit,
                                                        search_domain=search_domain,
                                                        with_sample=with_sample)
        return res