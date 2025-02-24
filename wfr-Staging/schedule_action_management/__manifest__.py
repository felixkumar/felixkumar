# -*- coding: utf-8 -*-
{
    'name': 'Schedule Action Management',
    'category': 'Settings',
    'summary': 'Manage schedule actions sequentially',
    'version': '16.0.0',
    'author': "Warefor",
    'website': "https://wfr1.odoo.com",
    'description': """
        This module will help us to manage schedule actions sequentially
    """,
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/ir_cron_management.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
}
