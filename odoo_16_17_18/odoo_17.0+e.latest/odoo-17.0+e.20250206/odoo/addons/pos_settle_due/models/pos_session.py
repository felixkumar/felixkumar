# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_res_partner(self):
        result = super()._loader_params_res_partner()
        if self.user_has_groups('account.group_account_readonly'):
            result['search_params']['fields'].extend(['credit_limit', 'total_due', 'use_partner_credit_limit'])
        return result

    def _loader_params_res_company(self):
        result = super()._loader_params_res_company()
        if self.user_has_groups('account.group_account_readonly'):
            result['search_params']['fields'].extend(['account_use_credit_limit'])
        return result

    def _get_pos_ui_res_partner(self, params):
        partners_list = super()._get_pos_ui_res_partner(params)
        self._set_partner_due(partners_list)
        return partners_list

    def _set_partner_due(self, partners_list):
        if self.config_id.currency_id != self.env.company.currency_id and self.user_has_groups('account.group_account_readonly') or self.env.ref('point_of_sale.group_pos_user') in self.env.user.groups_id:
            for partner in partners_list:
                partner_id = self.env['res.partner'].browse(partner['id'])
                partner['total_due'] = partner_id.get_total_due(self.config_id.currency_id.id)

    def get_pos_ui_res_partner_by_params(self, custom_search_params):
        partners = super().get_pos_ui_res_partner_by_params(custom_search_params)
        self._set_partner_due(partners)
        return partners
