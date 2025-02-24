# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    l10n_hk_leave_id = fields.Many2one('hr.leave', string='Leave', readonly=True)

    @api.depends('is_paid', 'number_of_hours', 'payslip_id', 'contract_id', 'payslip_id.sum_worked_hours', 'number_of_days')
    def _compute_amount(self):
        monthly_self = self.filtered(lambda wd: not wd.payslip_id.edited and wd.payslip_id.wage_type == "monthly")

        hk_wds = monthly_self.filtered(
            lambda wd: wd.payslip_id.struct_id.country_id.code == "HK")

        if hk_wds:
            unpaid_hk_wds = hk_wds.filtered(lambda wd: not wd.is_paid)
            paid_hk_wds = hk_wds - unpaid_hk_wds
            paid_hk_out_wds = paid_hk_wds.filtered(lambda wd: wd.code == 'OUT')
            paid_hk_main_wds = paid_hk_wds - paid_hk_out_wds

            for hk_wd in paid_hk_main_wds:
                payslip = hk_wd.payslip_id
                if hk_wd.l10n_hk_leave_id:
                    payslip = self.env['hr.payslip'].search([
                        ('employee_id', '=', hk_wd.payslip_id.employee_id.id),
                        ('date_from', '<=', hk_wd.l10n_hk_leave_id.date_from),
                        ('date_to', '>=', hk_wd.l10n_hk_leave_id.date_from),
                        ('state', 'in', ['done', 'paid']),
                    ], limit=1)
                    if not payslip:
                        payslip = hk_wd.payslip_id
                daily_wage_dict = payslip._get_daily_wage()
                daily_wage = daily_wage_dict['average']
                if hk_wd.work_entry_type_id.l10n_hk_use_713:
                    daily_wage = max(daily_wage_dict['average'], daily_wage_dict['moving'])

                worked_day_amount = daily_wage * hk_wd.number_of_days
                if hk_wd.work_entry_type_id.l10n_hk_non_full_pay:
                    worked_day_amount *= 0.8
                hk_wd.amount = worked_day_amount

        super(HrPayslipWorkedDays, self - hk_wds)._compute_amount()
