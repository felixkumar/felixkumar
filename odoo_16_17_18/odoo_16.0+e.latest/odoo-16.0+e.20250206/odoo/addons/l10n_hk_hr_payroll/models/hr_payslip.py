# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools.float_utils import float_compare


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    l10n_hk_worked_days_leaves_count = fields.Integer(
        'Worked Days Leaves Count',
        compute='_compute_worked_days_leaves_count')
    l10n_hk_713_gross = fields.Monetary(
        '713 Gross',
        compute='_compute_gross',
        store=True)
    l10n_hk_mpf_gross = fields.Monetary(
        'MPF Gross',
        compute='_compute_gross',
        store=True)
    l10n_hk_autopay_gross = fields.Monetary(
        'AutoPay Gross',
        compute='_compute_gross',
        store=True)
    l10n_hk_second_batch_autopay_gross = fields.Monetary(
        'Second Batch AutoPay Gross',
        compute='_compute_gross',
        store=True)

    @api.depends('worked_days_line_ids')
    def _compute_worked_days_leaves_count(self):
        for payslip in self:
            payslip.l10n_hk_worked_days_leaves_count = len(payslip.worked_days_line_ids.filtered(lambda wd: wd.l10n_hk_leave_id))

    @api.depends('line_ids.total')
    def _compute_gross(self):
        line_values = (self._origin)._get_line_values(['713_GROSS', 'MPF_GROSS', 'MEA', 'SBA'])
        for payslip in self:
            payslip.l10n_hk_713_gross = line_values['713_GROSS'][payslip._origin.id]['total']
            payslip.l10n_hk_mpf_gross = line_values['MPF_GROSS'][payslip._origin.id]['total']
            payslip.l10n_hk_autopay_gross = line_values['MEA'][payslip._origin.id]['total']
            payslip.l10n_hk_second_batch_autopay_gross = line_values['SBA'][payslip._origin.id]['total']

    def _get_paid_amount(self):
        self.ensure_one()
        res = super()._get_paid_amount()
        if self.struct_id.country_id.code != 'HK':
            return res
        if float_compare(res, self._get_contract_wage(), precision_rounding=0.1) == 0:
            return self._get_contract_wage()
        return res

    def _get_daily_wage(self):
        self.ensure_one()
        res = {
            "average": 0,
            "moving": 0,
        }
        date_from, date_to = min(self.mapped('date_from')), max(self.mapped('date_to'))
        payslips_per_employee = self._get_last_year_payslips_per_employee(date_from, date_to)
        wage = self.contract_id.wage
        payslip_day = (self.date_to - self.date_from).days + 1
        res['average'] = wage / payslip_day
        moving_daily_wage = sum(self.input_line_ids.filtered(lambda line: line.code == 'MOVING_DAILY_WAGE').mapped('amount'))
        if moving_daily_wage:
            res['moving'] = moving_daily_wage
        else:
            payslips = payslips_per_employee[self.employee_id]
            domain = self._get_last_year_payslips_domain(self.date_from, self.date_to)
            last_year_payslips = payslips.filtered_domain(domain).sorted(lambda x: x.date_from)
            if last_year_payslips:
                gross = last_year_payslips._get_line_values(['713_GROSS'], compute_sum=True)['713_GROSS']['sum']['total']
                gross -= last_year_payslips._get_total_non_full_pay()
                actual_worked_days = 0
                for payslip in last_year_payslips:
                    actual_worked_days += payslip._get_actual_work_days(skip_non_full_pay=True)
                if actual_worked_days > 0:
                    res['moving'] = gross / actual_worked_days
        return res

    def _get_actual_work_days(self, skip_non_full_pay=False):
        self.ensure_one()

        def _filtered_worked_days_line(line):
            if line.code in ['LEAVE90', 'OUT']:
                return True
            if skip_non_full_pay and line.work_entry_type_id.l10n_hk_non_full_pay:
                return True
            return False

        day_count = (self.date_to - self.date_from).days + 1
        skip_worked_days_count = sum(self.worked_days_line_ids.filtered(_filtered_worked_days_line).mapped('number_of_days'))
        return day_count - skip_worked_days_count

    def _get_actual_work_rate(self):
        self.ensure_one()
        days_count = (self.date_to - self.date_from).days + 1
        actual_work_days = self._get_actual_work_days()
        return actual_work_days / days_count

    @api.model
    def _get_last_year_payslips_domain(self, date_from, date_to, employee_ids=None):
        domain = [
            ('state', 'in', ['paid', 'done']),
            ('date_from', '>=', date_from + relativedelta(months=-12, day=1)),
            ('date_to', '<', date_to + relativedelta(day=1))]
        if employee_ids:
            domain = expression.AND([domain, [('employee_id', 'in', employee_ids)]])
        return domain

    def _get_last_year_payslips_per_employee(self, date_from, date_to):
        domain = self._get_last_year_payslips_domain(date_from, date_to, self.employee_id.ids)
        payslips = self.env['hr.payslip'].search(domain)
        payslips_per_employee = defaultdict(lambda: self.env['hr.payslip'])
        for payslip in payslips:
            payslips_per_employee[payslip.employee_id] += payslip
        return payslips_per_employee

    def _get_worked_day_lines_values(self, domain=None):
        self.ensure_one()
        res = super()._get_worked_day_lines_values(domain)
        if self.struct_id.country_id.code != 'HK':
            return res

        current_month_domain = expression.AND(
            [domain, ['|', ('leave_id', '=', False), ('leave_id.date_from', '>=', self.date_from)]])
        res = super()._get_worked_day_lines_values(current_month_domain)

        hours_per_day = self._get_worked_day_lines_hours_per_day()
        date_from = datetime.combine(self.date_from, datetime.min.time())
        date_to = datetime.combine(self.date_to, datetime.max.time())
        remainig_work_entries_domain = expression.AND([domain, [('leave_id.date_from', '<', self.date_from)]])
        work_entries = defaultdict(tuple)
        work_entries_dict = self.env['hr.work.entry']._read_group(
            self.contract_id._get_work_hours_domain(date_from, date_to, domain=remainig_work_entries_domain, inside=True),
            ['hours:sum(duration)', 'leave_id', 'work_entry_type_id'],
            ['leave_id', 'work_entry_type_id'],
            lazy=False
        )
        work_entries.update({(
            data['work_entry_type_id'][0] if data['work_entry_type_id'] else False,
            data['leave_id'][0] if data['leave_id'] else False
        ): data['hours'] for data in work_entries_dict})
        for work_entry, hours in work_entries.items():
            work_entry_id, leave_id = work_entry
            work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_id)
            days = round(hours / hours_per_day, 5) if hours_per_day else 0
            day_rounded = self._round_days(work_entry_type, days)
            res.append({
                'sequence': work_entry_type.sequence,
                'work_entry_type_id': work_entry_id,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
                'l10n_hk_leave_id': leave_id,
            })
        return res

    def _get_worked_day_lines(self, domain=None, check_out_of_contract=True):
        self.ensure_one()
        res = super()._get_worked_day_lines(domain, check_out_of_contract)
        if self.struct_id.country_id.code != 'HK':
            return res

        contract = self.contract_id
        if contract.resource_calendar_id:
            reference_calendar = self._get_out_of_contract_calendar()
            payslip_days = (self.date_to - self.date_from).days + 1
            remaining_days, remaining_hours = payslip_days, payslip_days * reference_calendar.hours_per_day
            for worked_days in res:
                remaining_days -= worked_days['number_of_days']
                remaining_hours -= worked_days['number_of_hours']

            if remaining_days or remaining_hours:
                work_entry_type = self.env.ref('hr_payroll.hr_work_entry_type_out_of_contract')
                existing = False
                for worked_days in res:
                    if worked_days['work_entry_type_id'] == work_entry_type.id:
                        worked_days['number_of_days'] += remaining_days
                        worked_days['number_of_hours'] += remaining_hours
                        existing = True
                        break
                if not existing:
                    res.append({
                        'sequence': work_entry_type.sequence,
                        'work_entry_type_id': work_entry_type.id,
                        'number_of_days': remaining_days,
                        'number_of_hours': remaining_hours,
                    })
        return res

    def _get_total_non_full_pay(self):
        total = 0
        for wd_line in self.worked_days_line_ids:
            if not wd_line.work_entry_type_id.l10n_hk_non_full_pay:
                continue
            total += wd_line.amount
        return total

    def write(self, vals):
        res = super().write(vals)
        if 'input_line_ids' in vals:
            self.filtered(lambda p: p.struct_id.country_id.code == 'HK' and p.state in ['draft', 'verify']).action_refresh_from_work_entries()
        return res

    def action_payslip_done(self):
        res = super().action_payslip_done()
        if self.struct_id.country_id.code != 'HK':
            return res
        future_payslips = self.sudo().search([
            ('id', 'not in', self.ids),
            ('state', 'in', ['draft', 'verify']),
            ('employee_id', 'in', self.mapped('employee_id').ids),
            ('date_from', '>=', min(self.mapped('date_to'))),
        ])
        if future_payslips:
            future_payslips.action_refresh_from_work_entries()
        return res
