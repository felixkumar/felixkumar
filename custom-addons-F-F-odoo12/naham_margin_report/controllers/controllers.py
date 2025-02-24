# -*- coding: utf-8 -*-
# from odoo import http


# class NahamMarginReport(http.Controller):
#     @http.route('/naham_margin_report/naham_margin_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/naham_margin_report/naham_margin_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('naham_margin_report.listing', {
#             'root': '/naham_margin_report/naham_margin_report',
#             'objects': http.request.env['naham_margin_report.naham_margin_report'].search([]),
#         })

#     @http.route('/naham_margin_report/naham_margin_report/objects/<model("naham_margin_report.naham_margin_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('naham_margin_report.object', {
#             'object': obj
#         })
