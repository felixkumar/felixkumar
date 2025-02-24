# -*- coding: utf-8 -*-
{
    'name': "Warefor Accounting Asset",

    'summary': """
        Extended asset for Warefor.""",

    'author': "TechUltra Solutions Pvt. Ltd.",
    'website': "https://www.techultrasolutions.com/",

    'category': 'Accounting',
    "version": "16.0.3",
    'license': 'LGPL-3',
    'depends': ['om_account_asset', 'account_assets_multi_vendor_tus'],

    'data': [
        'views/account_asset_views.xml',
    ],

    "images": [
        'static/description/banner.png',
    ],

    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    'installable': True,
    'application': True,
}
