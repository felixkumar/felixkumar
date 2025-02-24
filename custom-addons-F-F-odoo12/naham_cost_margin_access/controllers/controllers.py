# -*- coding: utf-8 -*-
from odoo import http

# class MobiPaymentInvoicesMenu(http.Controller):
#     @http.route('/mobi_payment_invoices_menu/mobi_payment_invoices_menu/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mobi_payment_invoices_menu/mobi_payment_invoices_menu/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mobi_payment_invoices_menu.listing', {
#             'root': '/mobi_payment_invoices_menu/mobi_payment_invoices_menu',
#             'objects': http.request.env['mobi_payment_invoices_menu.mobi_payment_invoices_menu'].search([]),
#         })

#     @http.route('/mobi_payment_invoices_menu/mobi_payment_invoices_menu/objects/<model("mobi_payment_invoices_menu.mobi_payment_invoices_menu"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mobi_payment_invoices_menu.object', {
#             'object': obj
#         })