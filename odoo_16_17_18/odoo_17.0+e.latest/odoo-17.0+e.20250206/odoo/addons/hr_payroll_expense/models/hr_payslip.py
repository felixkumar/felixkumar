# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, _, Command
from odoo.exceptions import AccessError, UserError


_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    expense_sheet_ids = fields.One2many(
        'hr.expense.sheet', 'payslip_id', string='Expenses',
        help="Expenses to reimburse to employee.")
    expenses_count = fields.Integer(compute='_compute_expenses_count')

    @api.depends('expense_sheet_ids.nb_expense', 'expense_sheet_ids.payslip_id')
    def _compute_expenses_count(self):
        for payslip in self:
            payslip.expenses_count = sum(payslip.mapped('expense_sheet_ids.nb_expense'))

    def action_payslip_cancel(self):
        # Remove the link to the cancelled payslip so it can be linked to another payslip
        res = super().action_payslip_cancel()
        if self.expense_sheet_ids.account_move_ids:
            self.expense_sheet_ids._do_reverse_moves()
        self.expense_sheet_ids.payslip_id = False
        self._update_expense_input_line_ids()
        return res

    def action_payslip_draft(self):
        # We can add the new or previously unlinked expenses to the payslip
        res = super().action_payslip_draft()
        self._link_expenses_to_payslip(clear_existing=False)  # Add the new expenses to the payslip, but keep the already linked ones
        return res

    @api.model_create_multi
    def create(self, vals_list):
        payslips = super().create(vals_list)
        draft_slips = payslips.filtered(lambda p: p.employee_id and p.state == 'draft')
        if not draft_slips:
            return payslips
        draft_slips._link_expenses_to_payslip()
        return payslips

    def write(self, vals):
        res = super().write(vals)
        if 'expense_sheet_ids' in vals:
            self._update_expense_input_line_ids()
        if 'input_line_ids' in vals:
            self._update_expense_sheets()
        return res

    def _compute_expense_input_line_ids(self):
        # DEPRECATED
        return self._update_expense_input_line_ids()

    def _link_expenses_to_payslip(self, clear_existing=True):
        """
        Link expenses to a payslip if the payslip is in draft state and the expense is not already linked to a payslip.
        """
        if not (self.env.is_superuser() or self.user_has_groups('hr_payroll.group_hr_payroll_user')):
            raise AccessError(_(
                "You don't have the access rights to link an expense report to a payslip. You need to be a payroll officer to do that.")
            )

        sheets_by_employee = dict(self.env['hr.expense.sheet'].sudo()._read_group([
                ('employee_id', 'in', self.employee_id.ids),
                ('state', '=', 'approve'),
                ('payment_mode', '=', 'own_account'),
                ('refund_in_payslip', '=', True),
                ('payslip_id', '=', False)],
                groupby=['employee_id'], aggregates=['id:recordset'])
        )

        for slip_sudo in self.sudo():
            if clear_existing:
                slip_sudo.expense_sheet_ids = [Command.clear()]
            payslip_sheets = sheets_by_employee.get(slip_sudo.employee_id, self.env['hr.expense.sheet'])
            if payslip_sheets:
                slip_sudo.expense_sheet_ids = [Command.link(sheet.id) for sheet in payslip_sheets]

    def _update_expense_input_line_ids(self):
        expense_type = self.env.ref('hr_payroll_expense.expense_other_input', raise_if_not_found=False)
        if not expense_type:
            _logger.warning("The 'hr_payroll_expense.expense_other_input' payslip input type is missing.")
            return  # We cannot do anything without the expense type
        for payslip in self:
            # Sudo to bypass access rights, as we just need to read the expense sheet's total amounts
            total = sum(payslip.sudo().expense_sheet_ids.mapped('total_amount'))
            lines_to_remove = payslip.input_line_ids.filtered(lambda x: x.input_type_id == expense_type)
            input_lines_vals = [Command.delete(line.id) for line in lines_to_remove]
            if total:
                input_lines_vals.append(Command.create({
                    'amount': total,
                    'input_type_id': expense_type.id
                }))
            payslip.input_line_ids = input_lines_vals

    def _update_expense_sheets(self):
        expense_type = self.env.ref('hr_payroll_expense.expense_other_input', raise_if_not_found=False)
        if not expense_type:
            return  # We cannot do anything without the expense type
        for payslip_sudo in self.sudo():
            if not payslip_sudo.input_line_ids.filtered(lambda line: line.input_type_id == expense_type):
                # Sudo to bypass access rights, as we just need to unlink the two models
                payslip_sudo.expense_sheet_ids.payslip_id = False

    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        for expense in self.expense_sheet_ids:
            expense.action_sheet_move_create()
            expense.set_to_paid()
            expense.payment_state = 'paid'
        return res

    def open_expenses(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reimbursed Expenses'),
            'res_model': 'hr.expense',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.mapped('expense_sheet_ids.expense_line_ids').ids)],
        }
