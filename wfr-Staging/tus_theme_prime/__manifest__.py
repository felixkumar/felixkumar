# -*- coding: utf-8 -*-
{
    # App information
    'name': 'TUS Theme Prime',
    'category': 'Theme/eCommerce',
    'summary': 'Theme Prime Extended',
    'description': 'Managed Theme Prime Theme',
    'version': '16.0.1.0.19',
    'author': 'TechUltra Solution',
    'license': 'LGPL-3',
    'company': 'TechUltra Solution',
    'website': 'https://www.techultrasolution.com',

    # Dependencies
    'depends': ['web', 'theme_prime'],

    # Data
    'data': [
        'views/snippets/custom_snippet_templates.xml',
        'views/snippets.xml',
        'views/templates.xml',
        'views/dr_website_content_views.xml',
    ],

    # Images
    'images': [
    ],
    'assets': {

    },

    # Technical
    'installable': True,
    'auto_install': False,
    'application': False,
}
