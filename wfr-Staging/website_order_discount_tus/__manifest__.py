# -*- coding: utf-8 -*-

{
    'name': 'Website Order Discount',
    'version': '16.0.0.2',
    'category': 'sale',
    'summary': """This app allow you to manage discount on your fist order from website.""",
    'description': """
            This app allow you to manage discount on your fist order from website.
    """,
    'author': "TechUltra Solutions Pvt. Ltd.",
    'website': 'https://wwwF.techultrasolutions.com/',
    'license': 'LGPL-3',
    'depends': ['website', 'website_sale', 'mail', 'loyalty', 'mass_mailing'],
    'data': [
        'security/ir.model.access.csv',
        'views/loyalty_program_views.xml',
        'data/mail_template.xml',

    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3'
}
