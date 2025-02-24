# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Mexico - Month 13 Trial Balance",
    'icon': '/l10n_mx/static/description/icon.png',
    "summary": """
        Mexico Month 13 Trial Balance Report
    """,
    "version": "1.0",
    "author": "Vauxoo / Odoo",
    "category": "Accounting/Localizations/Reporting",
    "website": "http://www.odoo.com",
    "license": "OEEL-1",
    "depends": [
        "l10n_mx_reports",
    ],
    "demo": [
    ],
    "data": [
        "views/account_move_views.xml",
        "views/account_report_views.xml",
    ],
    "installable": True,
    "auto_install": True,
}
