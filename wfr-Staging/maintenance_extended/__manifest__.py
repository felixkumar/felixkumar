# -*- coding: utf-8 -*-
{
    'name': "Maintenance Extended",
    'summary': """
        Extended functionality in maintenance module""",
    'author': "TechUltra Solutions Pvt. Ltd.",
    'website': "https://www.techultrasolutions.com/",
    'category': 'Inventory',
    "version": "16.0.9",
    'license': 'LGPL-3',
    'depends': ['maintenance', 'account', 'om_account_asset', 'hr'],
    'data': [
        'views/maintenance_views.xml',
        'views/account_move_views.xml',
        'views/account_asset_asset_views.xml',
    ],
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    'assets': {
        'web.assets_backend': [
            'maintenance_extended/static/src/xml/chatter_views.xml',
        ]
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3'
}
