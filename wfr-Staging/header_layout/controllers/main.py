# -*- coding: utf-8 -*-
from lxml import etree, html

try:
    from werkzeug.utils import send_file
except ImportError:
    from odoo.tools._vendor.send_file import send_file

from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website.controllers.main import Website

from odoo.tools import lazy

from odoo.http import request
import json


class OxfordWebsiteSale(WebsiteSale):

    @http.route()
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
        Category = request.env['product.public.category']
        website = request.env['website'].get_current_website()
        if request.website.company_id.is_oxford and not category:
            category = Category.search(website.website_domain(), limit=1)
        response = super().shop(page=page, category=category, search=search, min_price=min_price, max_price=max_price,
                                ppg=ppg, **post)
        if request.website.company_id.is_oxford:
            response.template = 'header_layout.shop_layout'

            website_domain = website.website_domain()
            categs_domain = website_domain
            search_product = response.qcontext.get('search')
            if search:
                search_categories = Category.search(
                    [('product_tmpl_ids', 'in', search_product.ids)] + website_domain
                ).parents_and_self
                categs_domain.append(('id', 'in', search_categories.ids))
            else:
                search_categories = Category
            categs = lazy(lambda: Category.search(categs_domain))

            response.qcontext.update(
                categories=categs,
                search_categories_ids=search_categories.ids,

            )
        return response


class OXFWebsite(Website):
    @http.route('/header_layout/get_products_data', type='json', auth='public', website=True)
    def get_products_data(self):
        # Add your logic to fetch dynamic content from the database
        products = request.env['product.template'].sudo().search([('website_published', '=', True)])
        print(products)
        content = request.env['ir.qweb'].with_context(inherit_branding=False)._render('header_layout.dynamic_filter_template_product_template_custom_style', dict(
            records=products,
            is_sample=False,
        ))
        return [etree.tostring(el, encoding='unicode') for el in
                html.fromstring('<root>%s</root>' % str(content)).getchildren()]
        # return products and request.render('header_layout.dynamic_filter_template_product_template_custom_style',
        #                                     {'products': products})

        # return request.env['ir.ui.view'].render_template(
        #     'header_layout.header_layout.product_dynamic_template',
        #     {'dynamic_content': dynamic_content}
        # )

    @http.route('/website/snippet/filters', type='json', auth='public', website=True)
    def get_dynamic_filter(self, filter_id, template_key, limit=None, search_domain=None, with_sample=False):
        dynamic_filter = request.env['website.snippet.filter'].sudo().search(
            [('id', '=', filter_id)] + request.website.website_domain())
        if not request.website.is_view_active(
                template_key) and request.website.company_id.is_oxford and dynamic_filter.model_name == 'product.public.category':
            template_key = 'header_layout.dynamic_filter_template_product_public_category_custom_styles_1'
        if not request.website.is_view_active(
                template_key) and request.website.company_id.is_oxford and dynamic_filter.model_name == 'product.template':
            template_key = 'header_layout.dynamic_filter_template_product_template_custom_style'
        return dynamic_filter and dynamic_filter._render(template_key, limit, search_domain, with_sample) or []
