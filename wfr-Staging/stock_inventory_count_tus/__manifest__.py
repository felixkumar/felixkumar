# -*- coding: utf-8 -*-

{
    'name': "Stock Inventory Counting",
    'summary': """
        Stock Inventory Counting
        """,
    'description': """
        - stock inventory count
    """,
    'author': "TechUltra Solutions Pvt. Ltd.",
    'website': "https://www.techultrasolutions.com/",
    'category': 'Inventory',
    "version": "16.2.7",
    'depends': ['stock', 'warefor_3pl_tus'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/stock_inventory_views.xml',
        'views/stock_quant_views.xml',
    ],
    "images": [
        'static/description/banner.png',
    ],
    'assets': {
        'web.assets_backend': [
            'stock_inventory_count_tus/static/src/**/*',
        ]
    },
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3'
}
