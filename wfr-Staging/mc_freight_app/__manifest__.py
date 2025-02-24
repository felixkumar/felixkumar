# -*- coding: utf-8 -*-
{
    'name': "Transit Application",
    'summary': """
        Create and Monitor Shipments
    """,
    'description': """""",
    'author': "TechUltra Solutions Pvt. Ltd.",
    'website': "https://www.techultrasolutions.com/",
    'category': 'Sales',
    'version': '16.0.20',
    'depends': ['base', 'product', 'mail', 'purchase'],
    'data': [
        'data/freight_stage_data.xml',
        'data/bol_sequence.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/freight_stage_views.xml',
        'views/freight_port_views.xml',
        'views/shipping_custom.xml',
        'views/custom_revision.xml',
        'wizard/tracking_wizard.xml',
        'wizard/shipping_wizard.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
