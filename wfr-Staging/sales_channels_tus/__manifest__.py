# -*- coding: utf-8 -*-
{
    'name': "Sales Channels Tus",
    'author': "TechUltra Solutions Private Limited",
    'website': "https://www.techultrasolutions.com/",
    'category': 'Uncategorized',
    'version': '17.0.0.1',
    'depends': ['sale_management', 'crm', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/sales_channel_views.xml',
        'views/crm_team_view.xml',
        'report/sales_report.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
