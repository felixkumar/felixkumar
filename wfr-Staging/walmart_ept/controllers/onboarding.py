# -*- coding: UTF-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request


class WalmartOnboarding(http.Controller):
    @http.route('/walmart_instances/walmart_instances_onboarding_panel', auth='user', type='json')
    def walmart_instances_onboarding_panel(self):
        """ Returns the `banner` for the Walmart onboarding panel.It can be empty if the user has closed it or if he
            doesn't have the permission to see it.
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 22 July 2021.
            Task_id: 176151 : Walmart Panel [Walmart Marketplace || v14
        """
        current_company_id = request.httprequest.cookies.get('cids').split(',') if request.httprequest.cookies.get(
            'cids', []) else []
        company = False
        if len(current_company_id) > 0 and current_company_id[0] and current_company_id[0].isdigit():
            company = request.env['res.company'].sudo().search([('id', '=', int(current_company_id[0]))])
        if not company:
            company = request.env.company
        hide_panel = company.walmart_onboarding_toggle_state != 'open'
        btn_value = 'Create More Walmart Instance' if hide_panel else 'Hide On boarding Panel'
        walmart_manager_group = request.env.ref("walmart_ept.group_walmart_manager")
        if request.env.uid not in walmart_manager_group.users.ids:
            return {}
        return {
            'html': request.env['ir.ui.view']._render_template('walmart_ept.walmart_instances_onboarding_panel_ept',{
                'company': company,
                'toggle_company_id': company.id,
                'hide_panel': hide_panel,
                'btn_value': btn_value,
                'state': company.get_and_update_walmart_instances_onboarding_state(),
                'is_button_active': company.is_create_walmart_more_instance
            })
        }
