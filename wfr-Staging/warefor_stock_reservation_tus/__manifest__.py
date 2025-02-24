# -*- coding: utf-8 -*-

{
    'name': 'Stock Reservation',
    'version': '16.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': """This app allow you to manage stock reservation from your Outbound Logistics Warehouse ops.""",
    'description': """

    """,
    'author': "TechUltra Solutions Pvt. Ltd.",
    'website': 'https://wwwF.techultrasolutions.com/',
    'license': 'LGPL-3',
    'depends': ['warefor_3pl_tus'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/freight_views.xml',
        'views/stock_reservation_view.xml',

    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3'
}
