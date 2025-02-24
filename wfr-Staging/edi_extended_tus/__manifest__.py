# -*- coding: utf-8 -*-

{
    'name': "EDI Extended Tus",

    'summary': """Extended Edi  feature """,

    'description': """
    """,

    'author': "TechUltra Solutions Pvt. Ltd.",
    "support": "contact@techultrasolutions.com",
    'website': "https://www.techultrasolutions.com/",

    'category': 'Custom Development',
    "version": "16.0.1",
    'license': 'LGPL-3',
    'depends': ['izi_marketplace','shipstation_shipping_odoo_integration', 'edi_3pl_tus'],

    'data': [
        'views/sale_order_view.xml',
        'views/res_partner_view.xml',
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
