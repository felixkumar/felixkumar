# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Odoo Peruvian Localization Reports",
    "summary": """
        Electronic accounting reports
            - Sales report
            - Purchase report
    """,
    "version": "0.1",
    "author": "Vauxoo",
    "category": "Localization",
    "website": "http://www.vauxoo.com",
    "license": "OEEL-1",
    "depends": [
        "l10n_pe_edi",
        "account_reports",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/account_ple_purchase_8_1_report.xml",
        "data/account_ple_purchase_8_2_report.xml",
        "data/account_ple_sales_14_1_report.xml",
        "data/l10n_pe.ple.usage.csv",
        "data/res.country.csv",
        "views/account_move_view.xml",
    ],
    "demo": [
    ],
    "installable": True,
    "auto_install": True,
}
