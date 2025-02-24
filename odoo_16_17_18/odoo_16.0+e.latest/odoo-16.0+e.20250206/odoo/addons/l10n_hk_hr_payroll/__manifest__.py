# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Hong Kong - Payroll',
    'icon': '/l10n_hk/static/description/icon.png',
    'category': 'Human Resources/Payroll',
    'depends': [
        'hr_payroll',
        'hr_contract_reports',
        'hr_work_entry_holidays',
        'hr_payroll_holidays',
    ],
    'version': '1.0',
    'description': """
Hong Kong Payroll Rules.
========================
    """,
    'data': [
        "data/hr_work_entry_type_data.xml",
        "data/resource_calendar_data.xml",
        "data/hr_payroll_structure_type_data.xml",
        "data/hr_payroll_structure_data.xml",
        "data/hr_payslip_input_type_data.xml",
        "data/hr_salary_rule_category_data.xml",
        "data/hr_rule_parameters_data.xml",
        "data/hr_leave_type_data.xml",
        "data/cap57/employee_salary_data.xml",
        "data/cap57/employee_payment_in_lieu_of_notice_data.xml",
        "data/cap57/employee_long_service_payment_data.xml",
        "data/cap57/employee_severance_payment_data.xml",
        "views/hr_payslip_views.xml",
        "views/hr_contract_views.xml",
        "views/hr_employee_views.xml",
        "views/hr_work_entry_views.xml",
    ],
    'demo': [
        'data/l10n_hk_hr_payroll_demo.xml',
    ],
    'license': 'OEEL-1',
}
