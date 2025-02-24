# -*- coding: utf-8 -*-
{
    'name': "Custom Backend Theme",
    'version': '16.0.0',
    'summary': """
        This app gives you the possibility to change the backend colors of your Odoo.
    """,

    'description': """
        This app helps you to manage a color theme for the backend of your solution
        for each company you have.
        It includes the possibility to change:
            - Color navbar (with some gradient)
            - Primary Color
            - Secondary Color
            - Hover color
            - Background Image of Odoo Main Screen
    """,

    'author': "Exaly <renaud@exaly.be>",
    'price': 27.00,
    'currency': 'EUR',
    'category': 'Customizations',
    'application': True,
    'installable': True,
    'images': [
        'static/description/screenshot_1.png',
        'static/description/screenshot_2.png',
        'static/description/screenshot_3.png',
    ],
    # any module necessary for this one to work correctly
    'depends': ['base', 'web'],

    # always loaded
    'data': [
        'views/res_company_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_backend_theme/static/src/**/*',
        ],
    },
    'license': 'OPL-1',
}
