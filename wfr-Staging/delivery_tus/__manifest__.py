# -*- coding: utf-8 -*-

{
    'name': "Delivery Tus",

    'summary': """
        Extended delivery carrier feature at transfer level""",

    'description': """
    """,

    'author': "TechUltra Solutions Pvt. Ltd.",
    "support": "contact@techultrasolutions.com",
    'website': "https://www.techultrasolutions.com/",

    'category': 'Inventory',
    "version": "16.0.1",
    'license': 'LGPL-3',
    'depends': ['delivery'],

    'data': [
        'views/stock_picking_view.xml',
        'wizard/choose_delivery_carrier_views.xml',
    ],

    'qweb': [
    ],
    'assets': {
    },

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
