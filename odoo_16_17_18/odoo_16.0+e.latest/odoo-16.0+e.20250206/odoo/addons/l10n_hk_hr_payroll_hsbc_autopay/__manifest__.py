# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Hong Kong - Payroll HSBC AutoPay',
    'category': 'Human Resources',
    'depends': ['l10n_hk_hr_payroll'],
    'version': '1.0',
    'description': """
Hong Kong Payroll Rules.
========================
    """,
    'data': [
        "security/ir.model.access.csv",
        "views/hr_employee_views.xml",
        "views/hr_payslip_run_views.xml",
        "views/res_bank_views.xml",
        "views/res_config_settings_views.xml",
        "wizards/hr_payroll_hsbc_autopay_wizard_views.xml",
    ],
    'license': 'OEEL-1',
    'auto_install': True,
}
