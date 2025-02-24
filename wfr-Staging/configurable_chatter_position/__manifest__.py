{
    "name": "Configurable Chatter Position",
    "version": "16.0.1.0.1",
    "license": "Other proprietary",
    "summary": "Allows the user to configure if the chatter should be positioned on the right side of the form"
                " view or at the bottom.",
    "description": "Allows the user to configure if the chatter should be positioned on the right side of the form"
                   " view or at the bottom.",
    "license": "LGPL-3",
    "author": "Mainframe Monkey BV",
    "price": 49.95,
    "currency": "EUR",
    "depends": ["mail"],
    "images": [
        "static/description/banner.jpg",
    ],
    "data": [
        "views/res_users.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'configurable_chatter_position/static/src/xml/configurable_chatter_position.xml',
            'configurable_chatter_position/static/src/js/chatter_position.js',
        ],
    },
    "installable": True,
}
