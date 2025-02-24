# -*- encoding: utf-8 -*-
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Pakistan - Accounting Reports',
    'icon': '/l10n_pk/static/description/icon.png',
    'version': '1.0',
    'author': 'Odoo S.A.',
    'description': """
Accounting Reports for Pakistan (Profit and Loss report and Balance Sheet)
    """,
    'category': 'Accounting/Localizations/Reporting',
    'depends': ['l10n_pk', 'account_reports'],
    'data': [
        'data/balance_sheet.xml',
        'data/profit_and_loss.xml',
    ],
    'auto_install': ['l10n_pk', 'account_reports'],
    'installable': True,
    'license': 'OEEL-1',
}
