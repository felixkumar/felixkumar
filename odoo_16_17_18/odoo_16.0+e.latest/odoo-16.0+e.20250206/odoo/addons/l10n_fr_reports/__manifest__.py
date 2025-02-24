# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'France - Accounting Reports',
    'icon': '/l10n_fr/static/description/icon.png',
    'version': '1.1',
    'description': """
Accounting reports for France
================================

    """,
    'category': 'Accounting/Localizations/Reporting',
    'depends': ['l10n_fr', 'account_reports'],
    'data': [
        'data/balance_sheet.xml',
        'data/profit_loss.xml',
        'data/intermediate_management_balances.xml',
        'data/account_report_ec_sales_list_report.xml',
    ],
    'auto_install': ['l10n_fr', 'account_reports'],
    'installable': True,
    'license': 'OEEL-1',
}
