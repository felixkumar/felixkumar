# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Saudi Arabia - Payroll',
    'author': 'Odoo S.A.',
    'category': 'Human Resources/Payroll',
    'icon': '/l10n_sa/static/description/icon.png',
    'description': """
Saudi Arabia Payroll and End of Service rules.
===========================================================
- Basic Calculation
- End of Service Calculation
- Other Input Rules (Overtime, Salary Attachments, etc.)
- Split Structures for EOS and Monthly Salaries
- GOSI Employee Deduction
- Unpaid leaves
    """,
    'license': 'OEEL-1',
    'depends': ['hr_payroll', 'l10n_sa'],
    'data': [
        'data/hr_payroll_structure_type_data.xml',
        'data/hr_payroll_structure_data.xml',
        'data/hr_salary_rule_data.xml',
        'views/hr_contract_view.xml',
    ],
    'auto_install': True,
}
