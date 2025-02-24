# -*- coding: utf-8 -*-

{
    'name': "Shipstation EPT Extended",

    'summary': """
        Extended ETP shipstation functionality""",

    'description': """
    """,

    'author': "TechUltra Solutions Pvt. Ltd.",
    'website': "https://www.techultrasolutions.com/",

    'category': 'Inventory/Purchase',
    "version": "16.0.5",
    'license': 'LGPL-3',
    'depends': ['shipstation_ept'],
    'demo': [],
    'data': [
        'view/delivery_carrier_views.xml',
        'view/sale_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
