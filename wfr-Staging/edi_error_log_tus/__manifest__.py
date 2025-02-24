# -*- coding: utf-8 -*-

{
    'name': "EDI Error LOGS Tus",

    'summary': """
        Identify any unmapped fields in the incoming edi data""",

    'description': """
    """,

    'author': "TechUltra Solutions Pvt. Ltd.",
    "support": "contact@techultrasolutions.com",
    'website': "https://www.techultrasolutions.com/",

    'category': 'Inventory',
    "version": "16.0.1",
    'license': 'LGPL-3',
    'depends': ['base', 'edi_import'],

    'data': ['security/ir.model.access.csv',
        'views/edi_error_log.xml',
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
