# -*- coding: utf-8 -*-
{
    'name': "Sale Order Importer",

    'summary': """
        Sale orders import from JSON files and sale confirming usin .csv, .xls, xlsx files
    """,

    'description': """
        Sale order import functionality. Import orders, customers and products from simply JSON file. 
        Includes a wizard to confirm sales using .csv, .xls, .xlsx and .ods extension files. 
    """,

    'author': "Oscar Otero Millán",
    'website': "https://www.linkedin.com/in/osotemi",

    'category': 'Sales',
    'version': '12.0.0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale'
    ],

    # always loaded
    'data': [
        'wizard/sale_order_json_importer_views.xml',
        'wizard/sale_order_confirmation_files_views.xml'
    ],
    # only loaded in demonstration mode
    #'demo': [
    #    'demo/demo.xml',
    #],
}