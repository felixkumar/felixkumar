# -*- coding: utf-8 -*-
################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
################################################################################

from odoo import http
from odoo.http import request
import werkzeug


class FacebookShop(http.Controller):
    @http.route(['/shop/<int:id>/content','/shop/<int:id>/content/<string:filename>'], csrf=False, type='http', auth="public",website=True)
    def view_data(self,id=None, filename=None, download=None, mimetype=None, access_token=None, token=None, **kw):
        shop = request.env['fb.facebook.shop'].sudo().browse(id)
        if shop.feeds_security == 'manual' and request.env['res.users'].browse(request.uid)._is_public():
            return request.not_found()
        if shop.feeds_security == "automatic" and shop.enable_token:
            if not token or shop.feed_token != token:
                return request.not_found()
        rec = http.request.env["fb.attachment.mapping"].sudo().search([('fb_shop','=',id),('latest','=',True)],limit=1)
        if rec:
            att_id=rec.attachment_id
            stream = request.env['ir.binary']._get_stream_from(att_id, 'datas')
            response = stream.get_response()
            status = response.status_code
            headers = response.headers
            content = stream.read()
            if status == 304:
                response = werkzeug.wrappers.Response(status=status, headers=headers)
            elif status == 301:
                return werkzeug.utils.redirect(content, code=301)
            elif status != 200:
                response = request.not_found()
            else:
                response = request.make_response(content, headers)
                rec.write({'updated':True})
            if token:
                response.set_cookie('fileToken', token)
            return response
        else:
            return request.not_found()

