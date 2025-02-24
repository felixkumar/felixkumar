# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import os
import io
import base64
import mimetypes

from odoo import http, _
from odoo.addons.portal.controllers.portal import pager as portal_pager, CustomerPortal
from odoo.exceptions import AccessError, MissingError
from collections import OrderedDict
from odoo.http import request


class CustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        user = request.env.user
        partner_id = user.partner_id
        if 'inbound_invoice_count' in counters:
            domain = [('partner_id', 'in', partner_id.ids), ('invoice_type', '=', 'wfl_inbound'),
                      ('name', 'not ilike', 'Level')]
            values['inbound_invoice_count'] = request.env['custom.invoice'].search_count(domain) if request.env[
                'custom.invoice'].check_access_rights('read', raise_exception=False) else 0
        if 'storage_invoice_count' in counters:
            domain = [('partner_id', 'in', partner_id.ids), ('invoice_type', '=', 'wfl_storage'),
                      ('name', 'not ilike', 'Level')]
            values['storage_invoice_count'] = request.env['custom.invoice'].search_count(domain) if request.env[
                'custom.invoice'].check_access_rights('read', raise_exception=False) else 0

        if 'product_availability_count' in counters:
            product_qty = request.env["partner.available.quantity"]
            user = request.env.user
            partner_id = user.partner_id
            domain = [('partner_id', 'in', partner_id.ids)]
            product_avl_id = product_qty.search(domain)
            values['product_availability_count'] = product_avl_id.total_product
        return values

    @http.route([
        '/my/invoices/download/<model("custom.invoice"):invoice>',
    ], type='http', auth="user", website=True)
    def download_invoice(self, invoice, **kw):
        """
        Download the invoice file from portal
        """
        if not invoice:
            return request.redirect('/my/')
        attachment = False
        if invoice.invoice_type == 'wfl_storage':
            attachment = invoice.sudo().with_context(is_website_process=True).print_wfl_invoice_pdf_report()
        if invoice.invoice_type == 'wfl_inbound':
            attachment = invoice.sudo().with_context(is_website_process=True).print_invoice_pdf_report()
        if attachment:
            data = io.BytesIO(base64.standard_b64decode(attachment["datas"]))
            # we follow what is done in ir_http's binary_content for the extension management
            extension = os.path.splitext(attachment["name"] or '')[1]
            extension = extension if extension else mimetypes.guess_extension(attachment["mimetype"] or '')
            filename = attachment['name']
            filename = filename if os.path.splitext(filename)[1] else filename + extension
            return http.send_file(data, filename=filename, as_attachment=True)

    @http.route(['/my/inbound/invoices', '/my/inbound/invoices/page/<int:page>'], type='http', auth="user",
                website=True)
    def portal_my_inbound_invoices(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        CustomInvoice = request.env['custom.invoice']
        user = request.env.user
        partner_id = user.partner_id
        domain = [('partner_id', 'in', partner_id.ids), ('invoice_type', '=', 'wfl_inbound'),
                  ('name', 'not ilike', 'Level')]

        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'invoice_date desc'},
            'duedate': {'label': _('Due Date'), 'order': 'due_date desc'},
            'name': {'label': _('Reference'), 'order': 'name desc'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        invoice_count = CustomInvoice.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/inbound/invoices",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=invoice_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        logistic_invoices = CustomInvoice.sudo().search(domain, order=order, limit=self._items_per_page,
                                                        offset=pager['offset'])
        # request.session['my_invoices_history'] = invoices.ids[:100]

        values.update({
            'date': date_begin,
            'logistic_invoices': logistic_invoices,
            'page_name': 'logistic_invoice',
            'pager': pager,
            'default_url': '/my/inbound/invoices',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("warefor_3pl_tus.portal_my_logistic_invoices", values)

    @http.route(['/my/storage/invoices', '/my/storage/invoices/page/<int:page>'], type='http', auth="user",
                website=True)
    def portal_my_storage_invoices(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        CustomInvoice = request.env['custom.invoice']
        user = request.env.user
        partner_id = user.partner_id
        domain = [('partner_id', 'in', partner_id.ids), ('invoice_type', '=', 'wfl_storage'),
                  ('name', 'not ilike', 'Level')]

        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'invoice_date desc'},
            'duedate': {'label': _('Due Date'), 'order': 'due_date desc'},
            'name': {'label': _('Reference'), 'order': 'name desc'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        invoice_count = CustomInvoice.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/storage/invoices",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=invoice_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        logistic_invoices = CustomInvoice.sudo().search(domain, order=order, limit=self._items_per_page,
                                                        offset=pager['offset'])
        # request.session['my_invoices_history'] = invoices.ids[:100]

        values.update({
            'date': date_begin,
            'logistic_invoices': logistic_invoices,
            'page_name': 'logistic_invoice',
            'pager': pager,
            'default_url': '/my/storage/invoices',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("warefor_3pl_tus.portal_my_logistic_invoices", values)


    # Product Availability
    @http.route(['/my/product_availability', '/my/product_availability/page/<int:page>'], type='http', auth="user",
                website=True)
    def portal_my_product_availability(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        product_qty = request.env["partner.available.quantity"]
        user = request.env.user
        partner_id = user.partner_id
        domain = [('partner_id', 'in', partner_id.ids)]

        product_count = product_qty.search(domain)

        # default filter by value
        if not filterby:
            filterby = 'all'


        pager = portal_pager(
            url="/my/product_availability",
            url_args={'sortby': sortby},
            total=product_count.total_product,
            page=page,
            step=self._items_per_page
        )

        available_product = product_qty.sudo().search(domain, order='id ASC', limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'available_product': available_product,
            'page_name': 'available_quantity',
            'pager': pager,
            'default_url': '/my/product_availability',
            'filterby': filterby,
        })

        # user = request.env.user
        return request.render("warefor_3pl_tus.portal_my_products_qty", values)
