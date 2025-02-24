from .common import TestL10nKeHrPayrollBase
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged('post_install_l10n', 'post_install', '-at_install')
class L10nKeTestPayslipValues(TestL10nKeHrPayrollBase):

    def test_payslip_zero_revenue_2022(self):
        # Ensure that no error is raised when creating a payslip with zero revenue
        salary_structure = self.env.ref('l10n_ke_hr_payroll.hr_payroll_structure_ken_employee_salary')
        try:
            payslip = self.env['hr.payslip'].create({
                'name': 'Test Payslip',
                'employee_id': self.employee_zero_wage.id,
                'contract_id': self.employee_zero_wage_contract.id,
                'date_from': '2022-01-01',
                'date_to': '2022-01-31',
                'struct_id': salary_structure.id,
            })
            payslip.compute_sheet()
        except UserError as ue:
            self.fail(f'A UserError error was raised when creating a payslip with zero revenue: {ue}')

    def test_payslip_values_paye_limit_under_limit_2022(self):
        # Create a payslip for the employee
        salary_structure = self.env.ref('l10n_ke_hr_payroll.hr_payroll_structure_ken_employee_salary')
        payslip = self.env['hr.payslip'].create({
            'name': 'Test Payslip',
            'employee_id': self.employee_ke_1.id,
            'contract_id': self.employee_ke_1_contract.id,
            'date_from': '2022-01-01',
            'date_to': '2022-01-31',
            'struct_id': salary_structure.id,
        })
        payslip.compute_sheet()
        # check that there is no payslip line for PAYE
        self.assertFalse(payslip.line_ids.filtered(lambda line: line.code == 'PAYE'), 'There should be no payslip line for PAYE since the wage of employee_ke_1 is below the PAYE limit')

    def test_payslip_values_paye_limit_over_limit_2022(self):
        # Create a payslip for the employee
        salary_structure = self.env.ref('l10n_ke_hr_payroll.hr_payroll_structure_ken_employee_salary')
        payslip = self.env['hr.payslip'].create({
            'name': 'Test Payslip',
            'employee_id': self.employee_ke_2.id,
            'contract_id': self.employee_ke_2_contract.id,
            'date_from': '2022-01-01',
            'date_to': '2022-01-31',
            'struct_id': salary_structure.id,
        })
        payslip.compute_sheet()
        # check that there is a payslip line for PAYE
        self.assertTrue(payslip.line_ids.filtered(lambda line: line.code == 'PAYE'), 'There should be a payslip line for PAYE since the wage of employee_ke_2 is above the PAYE limit')
        # check that the PAYE amount is correct
        payslip_line_paye = payslip.line_ids.filtered(lambda line: line.code == 'PAYE')
        # We tolerate a .1% error margin to account for rounding errors
        expected_value = 14025
        self.assertAlmostEqual(payslip_line_paye.total, expected_value, delta=expected_value / 1e3, msg='The PAYE amount should be 14025.0')
