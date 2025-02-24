# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import Command
from odoo.addons.hr_payroll.tests.common import TestPayslipBase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestPayrollExpense(TestPayslipBase):

    def test_expense_in_payroll_payment_state(self):
        product_a = self.env['product.product'].create({
            'name': 'test',
            'list_price': 100,
            'standard_price': 100,
        })
        expense_sheet = self.env['hr.expense.sheet'].create({
            'name': 'Test Expenses',
            'employee_id': self.richard_emp.id,
            'accounting_date': '2018-01-02',
            'expense_line_ids': [(0, 0, {
                'name': 'Expense line',
                'employee_id': self.richard_emp.id,
                'product_id': product_a.id,
            })]
        })
        expense_sheet.action_submit_sheet()
        expense_sheet.action_approve_expense_sheets()
        expense_sheet.action_report_in_next_payslip()

        self.richard_emp.contract_ids[0].state = 'open'
        richard_partner_id = self.env['res.partner'].create({'name': 'Richard', 'phone': '21454'}).id
        self.richard_emp.write({
            'address_id': richard_partner_id,
            'work_contact_id': richard_partner_id,
            'work_email': 'email@email',
        })

        payslip = self.env['hr.payslip'].create({
            'name': 'Payslip',
            'employee_id': self.richard_emp.id,
        })


        payslip.write({'expense_sheet_ids': expense_sheet.ids})
        payslip.compute_sheet()
        payslip.action_payslip_done()

        # Verify that the payslip is in done state
        self.assertEqual(payslip.state, 'done', 'State not changed!')

        # Click on the 'Mark as paid' button on payslip
        payslip.action_payslip_paid()

        # Verify that the payslip is in paid state
        self.assertEqual(payslip.state, 'paid', 'State not changed!')

        # Verify expense is paid as well
        self.assertEqual(expense_sheet.payment_state, 'paid', 'Expense not paid in payslip')

    def test_expense_set_to_approved_after_payslip_cancel(self):

        """
        Test Steps:
            1. Create an expense sheet for the employee Richard.
            2. Set the sheet to be reimbursed in the next payslip.
            3. Create a payslip for Richard.
            4. Compute payslip lines (compute_sheet).
            5. The expense sheet is now linked to the payslip and its state is 'approve'. Also, the account
                moves related to the expense sheet are created.
            6. Confirm the payslip.
                a. This will set the state of the payslip to 'Done'.
                b. This will set the state of the linked expense sheet to 'Done' too.
            7. Cancel the payslip.
                a. This will set the state of the payslip to 'Cancel'.
                b. The state of the linked expense sheet should be reset to 'approve'.
        """

        product_a = self.env['product.product'].create({
            'name': 'test',
            'list_price': 100,
            'standard_price': 100,
        })
        expense_sheet = self.env['hr.expense.sheet'].create({
            'name': 'Test Expenses',
            'employee_id': self.richard_emp.id,
            'accounting_date': '2018-01-02',
            'expense_line_ids': [Command.create({
                'name': 'Expense line',
                'employee_id': self.richard_emp.id,
                'product_id': product_a.id,
            })]
        })
        expense_sheet.action_submit_sheet()
        expense_sheet.action_approve_expense_sheets()
        expense_sheet.action_report_in_next_payslip()

        self.richard_emp.contract_ids[0].state = 'open'
        richard_partner_id = self.env['res.partner'].create({'name': 'Richard', 'phone': '21454'}).id
        self.richard_emp.write({
            'address_id': richard_partner_id,
            'work_contact_id': richard_partner_id,
            'work_email': 'email@email',
        })

        payslip = self.env['hr.payslip'].create({
            'name': 'Payslip',
            'employee_id': self.richard_emp.id,
        })

        payslip.compute_sheet()
        payslip.action_payslip_done()

        # Verify that the payslip is in done state
        self.assertEqual(payslip.state, 'done')

        # Verify that the expense_sheet is in done state, its payment_state is paid
        # and the account moves have been created for the expense sheet.
        self.assertEqual(expense_sheet.state, 'done')
        self.assertEqual(expense_sheet.payment_state, 'paid')
        self.assertEqual(bool(expense_sheet.account_move_ids), True)

        # Click on the 'Cancel' button on payslip
        payslip.action_payslip_cancel()

        # Verify that the payslip is in cancel state
        self.assertEqual(payslip.state, 'cancel')

        # Verify that the expense_sheet is in approve state, its payment_state is not_paid
        # and the account moves have been unlinked from the expense sheet.
        self.assertEqual(expense_sheet.state, 'approve')
        self.assertEqual(expense_sheet.payment_state, 'not_paid')
        self.assertEqual(bool(expense_sheet.account_move_ids), False)
