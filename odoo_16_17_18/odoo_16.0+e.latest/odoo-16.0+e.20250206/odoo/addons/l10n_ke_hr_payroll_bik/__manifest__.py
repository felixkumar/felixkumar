# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Kenya - Payroll additionnal fields',
    'author': 'Odoo',
    'version': '1.0',
    'category': 'Human Resources',
    'description': """
Kenyan Payroll Rules
========================================
This module is only temporary for its purpose is to add new fields in a stable version (16.0, 16.1).
    """,
    'depends': ['l10n_ke_hr_payroll'],
    'data': [
        'data/hr_salary_rule_data.xml',
        'views/hr_contract_views.xml',
        'views/hr_employee_views.xml',
    ],
    'license': 'OEEL-1',
    'auto_install': True,
}
