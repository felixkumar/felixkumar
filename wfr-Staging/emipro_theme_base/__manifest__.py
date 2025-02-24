# -*- coding: utf-8 -*-
{
    # Theme information
    'name': 'Emipro Theme Base',
    'category': 'Base',
    'summary': 'Base module containing common libraries for all Emipro eCommerce themes.',
    'version': '16.2.3',
    'license': 'OPL-1',
    'depends': ["website_sale_stock_wishlist", "website_sale_comparison_wishlist", "website_blog", "website_sale_product_configurator"],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/website_menu_view.xml',
        'views/website.xml',
        'views/search_keyword_report.xml',
        'views/synonym_group.xml',
        'views/product_template.xml',
        'views/product_tabs.xml',
        'views/ir_attachment.xml',
        'views/product_public_category.xml',
        'views/menu_label.xml',
        'views/product_brand.xml',
        'views/snippets/s_dynamic_snippet_products.xml',
        'views/product_attribute_value_view.xml',
        'views/product_pricelist_views.xml',
        'wizard/product_document_config.xml',
        'wizard/product_brand_wizard_view.xml',
        'templates/assets.xml',
        'templates/pwa.xml',
        'templates/offilne.xml',
        'templates/template.xml',
        'templates/image_hotspot_popup.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'emipro_theme_base/static/src/js/frontend/ajax_color_pane.js',
            'emipro_theme_base/static/src/js/frontend/load_more.js',
            'emipro_theme_base/static/src/js/frontend/pwa_web.js',
            'emipro_theme_base/static/src/js/frontend/lazy_load.js',
            'emipro_theme_base/static/src/js/frontend/website_sale.js',
            'emipro_theme_base/static/src/js/frontend/website_sale_options.js',
            'emipro_theme_base/static/src/js/frontend/product_offer_timer.js',
        ],
        'website.assets_editor': [
            'emipro_theme_base/static/src/js/snippet/slider_builder_helper.js',
        ],
        'website.assets_wysiwyg': [
            'emipro_theme_base/static/src/js/snippet/s_dynamic_snippets_products/options.js',
            'emipro_theme_base/static/src/js/snippet/s_dynamic_snippet_category/options.js',
            'emipro_theme_base/static/src/js/snippet/s_dynamic_snippet_brand/options.js',
            'emipro_theme_base/static/src/js/snippet/s_dynamic_snippet_product_templates/options.js',
        ],
    },
    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'https://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

    # Odoo Store Specific
    'images': [
        'static/description/emipro_theme_base.jpg',
    ],

    # Technical
    'installable': True,
    'auto_install': False,
    'price': 70.00,
    'currency': 'USD',
}
