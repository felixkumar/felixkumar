# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import models, fields, _


class HrEmployee(models.Model):
    _inherit = 'hr.payslip'

    def _get_data_files_to_update(self):
        # Note: file order should be maintained
        return super()._get_data_files_to_update() + [(
            'l10n_us_hr_payroll', [
                'data/hr_salary_rule_category_data.xml',
                'data/hr_payroll_structure_type_data.xml',
                'data/hr_payroll_structure_data.xml',
                'data/hr_rule_parameters_data.xml',
            ])]

    def _sum_year_to_date_totals(self, to_date):
        from_date = date(to_date.year, 1, 1)
        result = defaultdict(float)
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute("""
            SELECT sum(total) as amount,
                   code
            FROM (
                SELECT pl.total as total,
                       pl.code as code
                FROM hr_payslip as hp
                JOIN hr_payslip_line as pl ON hp.id = pl.slip_id
                WHERE hp.employee_id = %s
                AND hp.state in ('done', 'paid')
                AND hp.date_from >= %s
                AND hp.date_to <= %s

                UNION ALL

                SELECT hpwd.amount as total,
                       CAST(hpwd.work_entry_type_id as varchar) as code
                FROM hr_payslip as hp
                JOIN hr_payslip_worked_days as hpwd ON hp.id = hpwd.payslip_id
                WHERE hp.employee_id = %s
                AND hp.state in ('done', 'paid')
                AND hp.date_from >= %s
                AND hp.date_to <= %s
            ) as combined
            GROUP BY code
        """, (self.employee_id.id, from_date, to_date, self.employee_id.id, from_date, to_date))

        grouped_payslip_lines = self.env.cr.dictfetchall()
        for payslip_line in grouped_payslip_lines:
            result[payslip_line['code']] = payslip_line['amount']
        return result

    def _get_leave_lines(self):
        self.ensure_one()
        leaves_allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'validate'),
            ('date_from', '<', self.date_to),
            '|',
            ('date_to', '=', False),
            ('date_to', '>', self.date_from),
        ])
        if not leaves_allocations:
            return []

        day_before_period = self.date_from + relativedelta(days=-1)
        before_period_durations_by_leave_type = self.env['hr.work.entry']._get_leaves_duration_between_two_dates(
            self.employee_id, min(leaves_allocations.mapped('date_from')), day_before_period)
        period_durations_by_leave_type = self.env['hr.work.entry']._get_leaves_duration_between_two_dates(
            self.employee_id, self.date_from, self.date_to)

        # Only get the leave types associated to valid allocations
        leave_types = leaves_allocations.holiday_status_id
        leave_lines = []
        for leave_type in leave_types:
            related_allocations = leaves_allocations.filtered(lambda a: a.holiday_status_id == leave_type)

            allocated_before = related_allocations._get_total_allocated(day_before_period)
            allocated_now = related_allocations._get_total_allocated(self.date_to)

            total_used_before = before_period_durations_by_leave_type.get(leave_type, 0.0)
            used = period_durations_by_leave_type.get(leave_type, 0.0)

            gain = allocated_now - allocated_before
            balance = allocated_now - total_used_before - used

            leave_lines.append({
                'type': leave_type.name,
                'used': used,
                'accrual': gain,
                'balance': balance,
            })
        return leave_lines

    # FIXME: this should be removed in master (see https://www.odoo.com/odoo/1251/tasks/3844686)
    def _get_rule_name(self, localdict, rule, employee_lang):
        if self.country_code == 'US' and rule.code == 'GROSS':
            return _('Gross Pay')
        return super()._get_rule_name(localdict, rule, employee_lang)
