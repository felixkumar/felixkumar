{
    'name': 'Shipstation Odoo Shipping Connector',
    'version': '16.1.15',
    'author': "Vraja Technologies",
    'price': 98,
    'currency': 'EUR',
    'license': 'OPL-1',
    'category': "Website",
    'summary': """""",
    'description': """
    Shipstation Odoo Integration helps you integrate & manage your shipstation account in odoo. manage your Delivery/shipping operations directly from odoo.
    Export Order To Shipstation On Validate Delivery Order.
    Auto Import Tracking Detail From Shipstation to odoo.
    Generate Label in Odoo..
    Also Possible To Import Order From Marketplace/Store.
    We also Provide the ups,dhl,bigcommerce,shiphero,gls,fedex,usps,easyship,stamp.com,dpd,canada post,bpost
""",
    'depends': ['delivery', 'sale', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'data/product_demo.xml',
        'view/shipstation_odoo_integration_config.xml',
        'view/shipstation_store_view.xml',
        'view/shipstaion_operation_detail.xml',
        'view/shipstation_delivery_carrier.xml',
        'view/shipstation_delivery_carrier_service.xml',
        'view/delivery_carrier.xml',
        'view/shipstation_delivery_carrier_package.xml',
        'view/stock_picking.xml',
        'view/sale_order.xml',
        'view/stock_warehouse.xml',
        'view/res_company.xml',
        'view/shipstaion_operation_detail.xml',
    ],
    'images': [
        'static/description/odoo_shipstation.png',
    ],
    'demo': [],
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',
    'installable': True,
    'auto_install': False,
    'application': True,
}

#FIX account_intrastat Issue 