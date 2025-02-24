# -*- coding: utf-8 -*-

{
    'name': "Warehouse Inventory Report",
    'summary': """
        Warehouse Omvemtory Report
        """,
    'description': """
        - Generating stock report in excel file, for different warehouses
    """,
    'author': "Warefor",
    'website': "https://www.warefor.com",
    'category': 'Inventory',
    "version": "16.0.19",
    'depends': ['warefor_3pl_tus'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/stock_warehouse_views.xml',
        'views/product_views.xml',
        'views/stock_inventory_views.xml',
        'wizard/generate_old_days_report_views.xml',
    ],
    "images": [
        'static/description/banner.png',
    ],
    'assets': {
        'web.assets_backend': [
            'warehouse_inventory_report/static/src/xml/tree_button.xml',
            'warehouse_inventory_report/static/src/js/tree_button.js',
        ],
    },
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3'
}
