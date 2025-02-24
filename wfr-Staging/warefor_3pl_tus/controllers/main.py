# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.addons.portal.controllers.web import Home
from odoo.addons.web.controllers.dataset import DataSet
from odoo.http import request, SessionExpiredException
from odoo import http
from odoo.addons.web.controllers.utils import clean_action


class Website(Home):

    def _login_redirect(self, uid, redirect=None):
        """ Redirect regular users (employees) to the backend) and others to
        the frontend
        """
        current_user = request.env['res.users'].browse(uid)
        if current_user and current_user.company_ids:
            if current_user.is_select_all_company:
                company_ids = ','.join([str(cid) for cid in current_user.company_ids.ids])
                redirect = '/web?#cids=' + company_ids
        return super()._login_redirect(uid, redirect=redirect)


# class DataSetWebsite(DataSet, http.Controller):
#
#     @http.route('/web/dataset/call_button', type='json', auth="user")
#     def call_button(self, model, method, args, kwargs):
#         if request.env.user.id == 1580:
#             return False
#         action = self._call_kw(model, method, args, kwargs)
#         if isinstance(action, dict) and action.get('type') != '':
#             return clean_action(action, env=request.env)
#         return False
#
#     DataSet.call_button = call_button
