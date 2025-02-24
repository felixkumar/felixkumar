# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': 'Account Assets Multi Vendor',

    'summary': """ Extended account functionality""",

    'description': """
    """,

    'author': "TechUltra Solutions Pvt. Ltd.",
    'website': "https://www.techultrasolutions.com/",

    'category': 'Accounting/Accounting',

    'version': '16.0.1',

    'depends': ['account', 'om_account_asset'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_asset_view.xml',
    ],
    'qweb': [],
    'images': [
        'static/description/logo.png'
    ],
    'license': 'OPL-1',
    'installable': True,
    'application': True,
}
