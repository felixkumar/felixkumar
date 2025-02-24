# -*- coding: utf-8 -*-
# Part of WFR.
{
    "name": "Merge Invoices",
    "author": "WFR",
    "website": "",
    "category": "Accounting",
    "license": "OPL-1",
    "summary": """
Merge Invoices
""",
    "description": """

""",
    "version": "16.0.2",
    "depends": [
        "account",
    ],
    "application": True,
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "wizard/sh_merge_invoice_views.xml",
    ],
    "images": ["static/description/background.png", ],
    "auto_install": False,
    "installable": True,
    "price": 30,
    "currency": "EUR"
}
