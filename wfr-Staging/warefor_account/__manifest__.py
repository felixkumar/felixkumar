# -*- coding: utf-8 -*-
{
    'name': "Warefor Accounting",

    'summary': """
        Extended account for Warefor""",

    'author': "TechUltra Solutions Pvt. Ltd.",
    'website': "https://www.techultrasolutions.com/",

    'category': 'Accounting & Finance',
    "version": "16.0.4",
    'license': 'LGPL-3',
    'depends': ['account', 'warefor_3pl_tus'],

    'data': [
        # 'data/scheduler.xml',
        'security/ir.model.access.csv',
        'views/account_quickbook_type_view.xml',
        'views/account_view.xml',
        'views/account_move_view.xml',
        'views/res_partner_view.xml',
        'views/product_view.xml'
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
