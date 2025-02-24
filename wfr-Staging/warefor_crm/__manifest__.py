# -*- coding: utf-8 -*-
{
    'name': "WareFor CRM",
    'summary': """
    WareFor CRM
    """,
    'description': """""",
    'author': "TechUltra Solutions Pvt. Ltd.",
    'website': "https://www.techultrasolutions.com/",
    'category': 'Uncategorized',
    "version": "16.0.4",
    'license': 'LGPL-3',
    'depends': ['product', 'crm', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/stage_data.xml',
        'reports/report_action.xml',
        'views/product_development.xml',
        'views/product_development_state_view.xml',
        'views/crm_lead.xml',
        'views/product_views.xml',
    ],
    # 'assets': {
    #      'web.assets_backend': [
    #          'warefor_crm/static/src/css/chatter.css',
    #      ]
    # },
    'images': ['static/description/icon.png'],
    'qweb': [],

}
