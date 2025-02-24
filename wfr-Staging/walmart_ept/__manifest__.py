# -*- coding: utf-8 -*-
{

    # App information
    'name': 'Walmart Odoo Connector',
    'version': '16.0.1.0.1',
    'license': 'OPL-1',
    'summary': 'Integrate & Manage all your Walmart account operations from Odoo.Customers can manage their orders, can check the reporting, manage walmart fees & other operations as mentioned in the User documentation.Apart from Odoo Walmart Connector, we do have other ecommerce solutions or applications such as Woocommerce connector , Shopify connector , magento connector and also we have solutions for Marketplace Integration such as Odoo Amazon connector , Odoo eBay connector , Odoo Bol.com Connector.Aside from ecommerce integration and ecommerce marketplace integration, we also provide solutions for various operations, such as shipping , logistics , shipping labels , and shipping carrier management with our shipping integration , known as the Shipstation connector.For the customers who are into Dropship business, we do provide EDI Integration that can help them manage their Dropshipping business with our Dropshipping integration or Dropshipper integration It is listed as Dropshipping EDI integration and Dropshipper EDI integration.Emipro applications can be searched with different keywords like Amazon integration , Shopify integration , Woocommerce integration, Magento integration , Amazon vendor center module , Amazon seller center module , Inter company transfer , eBay integration , Bol.com integration , inventory management , warehouse transfer module , dropship and dropshipper integration and other Odoo integration application or module',

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com/',

    # Dependencies
    'depends': ['common_connector_library'],
    'data': [
        'security/walmart_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'data/ir_sequence.xml',
        'data/product.xml',
        'data/import_offers_attachment.xml',
        'data/res_country_data.xml',
        'view/walmart_main_menu.xml',
        'view/dashboard_view.xml',
        'wizard/queue_process_wizard_view.xml',
        'wizard/walmart_instance_create_views.xml',
        'wizard/walmart_res_config.xml',
        'wizard/walmart_cancel_order_views.xml',
        'view/sale_order_view.xml',
        'view/walmart_reconciliation_report.xml',
        'view/auto_sale_workflow_view.xml',
        'view/delivery_carrier_view.xml',
        'wizard/walmart_process_import_export_view.xml',
        'view/walmart_log_book_view.xml',
        'view/walmart_feed_history_view.xml',
        'view/walmart_marketplace_view.xml',
        'view/walmart_offer_view.xml',
        'view/stock_picking_views.xml',
        'wizard/walmart_update_product_views.xml',
        'view/res_partner_view.xml',
        'report/sale_report_view.xml',
        'view/order_refund_view.xml',
        'wizard/walmart_cron_configuration_ept.xml',
        'wizard/onboarding_configuration_wizard.xml',
        'view/onboarding_panel_view.xml',
        'wizard/onboarding_confirmation_ept_view.xml',
        'view/walmart_product_sync_report_view.xml',
        'wizard/prepare_product_for_export.xml',
        'view/order_queue_view.xml',
        'view/order_queue_line_view.xml',
        'view/account_invoice_view.xml',
        'wizard/refund_order_wizard.xml',
        # 'view/view_app_version.xml',
    ],
    'qweb':['static/src/xml/dashboard_widget_inherit.xml'],
# Odoo Store Specific
    'images': ['static/description/Walmart-v16.jpg'],

    # Technical        
    'installable':True,
    'auto_install':False,
    'application':True,
    'active':False,
    'live_test_url':'https://www.emiprotechnologies.com/r/O9B',
    'price':1500.00,
    'currency':'EUR',
    'assets': {
            'web.assets_backend': [
                '/walmart_ept/static/src/js/walmart_button_collapse.js',
                '/walmart_ept/static/src/css/form_layout.css'
            ],
        },
}
