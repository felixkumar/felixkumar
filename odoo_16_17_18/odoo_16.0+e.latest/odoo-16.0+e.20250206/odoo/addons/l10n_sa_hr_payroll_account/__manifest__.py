# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Saudi Arabia - Payroll with Accounting',
    'author': 'Odoo S.A.',
    'version': '1.0',
    'category': 'Human Resources',
    'icon': '/l10n_sa/static/description/icon.png',
    'description': """
Accounting Data for Saudi Arabia Payroll Rules.
=======================================================

    """,
    'depends': ['hr_payroll_account', 'l10n_sa', 'l10n_sa_hr_payroll'],
    'data': [
        'data/account_chart_template_data.xml',
        'data/l10n_sa_hr_payroll_account_data.xml',
    ],
    'license': 'OEEL-1',
    'auto_install': True,
}
