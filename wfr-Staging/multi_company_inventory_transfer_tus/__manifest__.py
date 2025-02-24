# -*- coding: utf-8 -*-

{
    'name': "Multi-Company Inventory Transfer",
    'summary': """
        Multi-Company Inventory Transfer
        """,
    'description': """
        - Multi-Company Inventory Transfer.
    """,
    'author': "TechUltra Solutions Pvt. Ltd.",
    'website': "https://www.techultrasolutions.com/",
    'category': 'Inventory/Purchase',
    "version": "16.0.1",
    'depends': ['stock', 'product_multi_company'],
    'data': [
        'views/res_config_sets_extend_view.xml',
        'views/res_company_view.xml',
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
