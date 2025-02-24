# -*- coding: utf-8 -*-
from odoo import _, Command, models, fields
from odoo.tools import float_is_zero


class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    def _compute_duration(self):
        previous_durations = self.mapped('duration')
        super()._compute_duration()
        for timer, previous_duration in zip(self, previous_durations):
            if timer.workorder_id.production_id.analytic_account_id:
                timer._create_analytic_entry(previous_duration)

    def _create_analytic_entry(self, previous_duration=0):
        for time in self:
            employee_aal = time.workorder_id.employee_analytic_account_line_ids.filtered(
                lambda line: line.employee_id and line.employee_id == time.employee_id
            )
            duration = (time.duration - previous_duration) / 60.0
            amount = - duration * time.employee_cost
            account = time.workorder_id.production_id.analytic_account_id

            if employee_aal:
                employee_aal.write({
                    'unit_amount': employee_aal.unit_amount + duration,
                    'amount': employee_aal.amount + amount,
                })
            elif not float_is_zero(amount, precision_rounding=account.currency_id.rounding):
                aa_vals = time.workorder_id._prepare_analytic_line_values(account, duration, amount)
                aa_vals['name'] = _("[EMPL] %s - %s", time.workorder_id.display_name, time.employee_id.name)
                aa_vals['employee_id'] = time.employee_id.id
                time.workorder_id.employee_analytic_account_line_ids = [Command.create(aa_vals)]

    def unlink(self):
        for time in self:
            # set previous_duration to 2 * time.duration to effectively
            # create an analytic entry for a length of -time.duration
            if time.production_id.analytic_account_id:
                time._create_analytic_entry(2 * time.duration)
        return super().unlink()

class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    employee_analytic_account_line_ids = fields.Many2many('account.analytic.line', copy=False)

    def _compute_duration(self):
        self.filtered(lambda wo: wo.workcenter_id.allow_employee)._create_or_update_analytic_entry()
        super()._compute_duration()
