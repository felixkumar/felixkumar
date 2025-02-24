# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import request


class BIQuery(http.Controller):

    @http.route('/api_bi/query/', auth='connector_bi', type='json', cors='*', methods=['POST'])
    def _get_categories(self, query):
        request.cr.execute(query)
        return request.cr.dictfetchall()

