# -*- coding: utf-8 -*-

{
    'name': "EDI 3PL Development",

    'summary': """ EDI 3PL Development """,

    'description': """
    """,

    'author': "TechUltra Solutions Pvt. Ltd.",
    "support": "contact@techultrasolutions.com",
    'website': "https://www.techultrasolutions.com/",

    'category': 'Custom Development',
    "version": "16.0.9",
    'license': 'LGPL-3',
    'depends': ['sale_stock', 'website'],

    'data': [
        'security/ir.model.access.csv',
        'views/website_views.xml',
        'views/company_view.xml',
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
