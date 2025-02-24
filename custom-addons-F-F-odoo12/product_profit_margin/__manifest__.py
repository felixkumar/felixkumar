# -*- coding: utf-8 -*-

{
    'name': "Product Profit Margin",
    'summary': """Set the Price List based on Profit Margin     
               """,
    'version': '12.0.1.0.0',
    'description': """
       Set the Price List based on Profit Margin
    """,
    'author': 'Victor Inojosa',
    'category': 'product',
    'depends': ['sale', 'product_variant_sale_price', 'product_price_taxes_included'],
    'data': ['views/product_view.xml',
             'views/sale_order_view.xml'],
    'installable': True,
    'auto_install': False,
}
