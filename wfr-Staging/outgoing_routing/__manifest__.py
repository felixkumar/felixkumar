# Copyright 2020 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'Picking and Reservation Strategy',
    "version": "16.0.1.1.0",
    'author': 'VentorTech',
    'website': 'https://ventor.tech/',
    'license': 'LGPL-3',
    'installable': True,
    'images': ['static/description/images/image1.JPG'],
    'summary': 'Allows to automatically build optimal picking routes and apply custom reservation options',
    'depends': [
        'sale_management',
        'stock_picking_batch',
        'ventor_base',
    ],
    'data': [
        'data/product_removal.xml',
        'views/res_config.xml',
        'views/stock.xml',
        'views/picking.xml',
        'views/report_stockpicking.xml',
        'views/stock_picking_wave.xml',
    ],
}
