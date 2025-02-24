# -*- coding: utf-8 -*-
{
    'name': "Warefor Sale",

    'summary': """
        Extended sale for Warefor.""",

    'author': "TechUltra Solutions Pvt. Ltd.",
    'website': "https://www.techultrasolutions.com/",

    'category': 'Sales',
    "version": "16.0.1",
    'license': 'LGPL-3',
    'depends': ['base', 'sale'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/res_config_settings_view.xml',
        'views/sale_order_extend.xml',
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
