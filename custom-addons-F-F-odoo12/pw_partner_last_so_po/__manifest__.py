# -*- coding: utf-8 -*-
{
    "name": "Partner Last Sale Order and Date| Partner Last Purchase Order and Date",
    "version": "12.0",
    'summary': """
        This module is allow you to track partner last sale order, purchase order and date | Partner Last Purchase with Date | Partner Last Sale with date""",
    'description': """
This module is allow you to track partner last sale order, purchase order and date
        """,    
    "category": "Purchase",
    'author': "Preway IT Solutions",
    "sequence": 2,
    'depends': ['base','purchase','sale','contacts'],
    "data" : [
        'views/res_partner_view.xml',
    ],
    'price': 10.0,
    'currency': 'EUR',
    "installable": True,
    "auto_install": False,
    #"license": "LGPL-3",
    "application": True,
    "images":["static/description/Banner.png"],
}
