# -*- coding: utf-8 -*-
{
    'name': "Company header/footer",

    'summary': """
       Allows you to add header and footer image on company and use it on printed sales & invoices""",

    'description': """
        Allows you to add header and footer image on company and use it on printed sales sales & invoice.
    """,
    'version': '10.0.2.2',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'author': "DVIT.ME",
    'website': 'http://dvit.me/',
    'depends': ['sale','account'],
    'data': [
        'views/templates.xml',
        'views/sale_report.xml',
        'views/invoice_report.xml',
    ],
    "images": [
        'static/description/banner.png'
    ],
}
