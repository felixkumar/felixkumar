# -*- coding: utf-8 -*-

{
    'name': "Warehouse Aging Report",
    'summary': """
        Warehouse Aging Report
        """,
    'description': """
    """,
    'author': "Warefor",
    'website': "https://www.warefor.com",
    'category': 'Inventory',
    "version": "16.0.4",
    'depends': ['warefor_3pl_tus'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/generate_aging_report_views.xml',
        'wizard/product_views.xml',
    ],
    "images": [
        'static/description/banner.png',
    ],
    'assets': {
    },
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3'
}
