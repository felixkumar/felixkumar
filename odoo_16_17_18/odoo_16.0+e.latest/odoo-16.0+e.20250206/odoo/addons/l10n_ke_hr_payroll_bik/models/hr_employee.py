# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    l10n_ke_mortgage = fields.Monetary(string="Mortgage Interest", currency_field='currency_id', groups="hr.group_hr_user")

    @api.constrains('l10n_ke_mortgage')
    def _check_l10n_ke_mortgage(self):
        max_amount_yearly = self.env['hr.rule.parameter'].sudo()._get_parameter_from_code('l10n_ke_max_mortgage', raise_if_not_found=False)
        for employee in self:
            if max_amount_yearly and employee.l10n_ke_mortgage > max_amount_yearly:
                raise UserError(_('The mortgage interest cannot exceed %s Ksh yearly.', max_amount_yearly))
