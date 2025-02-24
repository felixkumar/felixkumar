# -*- coding: utf-8 -*-
{
    'name': 'Header Layout TUS',
    'description': 'Header Layout  ',
    'summary': 'Header Layout',
    'category': 'Website',
    'version': '16.0.0.52',
    'license': 'LGPL-3',
    'depends': ['website_sale'],
    'author': "TechUltra Solutions Pvt. Ltd.",
    'website': "https://www.techultrasolutions.com/",

    'data': [
        'views/templates.xml',
        'data/data.xml',
        'data/sale_cart_recovery_mail_template.xml',
        'views/snippets/header_snippet.xml',
        'views/snippets.xml',
        'views/product_template_views.xml',
        'views/website_views.xml',
        'views/shop_layout.xml',
        'views/cart_layout.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Libraries
            'header_layout/static/lib/OwlCarousel2-2.3.4/assets/owl.carousel.css',
            'header_layout/static/lib/OwlCarousel2-2.3.4/assets/owl.theme.default.css',
            'header_layout/static/lib/OwlCarousel2-2.3.4/owl.carousel.js',

            # Frontend
            'header_layout/static/src/css/style.css',
            'header_layout/static/src/scss/website_sale.scss',
            'header_layout/static/src/xml/portal_ratings.xml',
            'header_layout/static/src/js/content/add_to_cart_sticky.js',
            'header_layout/static/src/js/content/mega_menu.js',
            'header_layout/static/src/js/frontend/login_popup.js',
            'header_layout/static/src/js/frontend/website_sale.js',
            'header_layout/static/src/js/frontend/portal_chatter.js',

            # MIXINS
            'header_layout/static/src/js/core/mixin.js',

            # SNIPPETS
            'header_layout/static/src/snippets/s_dynamic_snippet_carousel/000.xml',
            'header_layout/static/src/snippets/s_dynamic_snippet_carousel/000.js',


        ],

    },
    'installable': True,
    'auto_install': False,
}
