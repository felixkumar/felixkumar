# -*- coding: utf-8 -*-

{
    'name': "3PL Shipstation Extended",

    'summary': """
        Extended shipstation functionality""",

    'description': """
    """,

    'author': "TechUltra Solutions Pvt. Ltd.",
    'website': "https://www.techultrasolutions.com/",

    'category': 'Inventory/Purchase',
    "version": "16.0.12",
    'license': 'LGPL-3',
    'depends': ['shipstation_shipping_odoo_integration', 'edi_3pl_tus', 'warefor_3pl_tus'],
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'data/data.xml',
        'views/sale_view.xml',
        'views/website_shipstation_configuration.xml',
        'views/shipstation_store_view.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
