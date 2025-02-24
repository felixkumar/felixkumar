# -*- coding: utf-8 -*-
{
    "name": "Custom Fields: Core",
    "version": "16.0.1.0.5",
    "category": "Extra Tools",
    "author": "faOtools",
    "website": "https://faotools.com/apps/16.0/custom-fields-core-707",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "web_editor"
    ],
    "data": [
        "wizard/custom_fields_prepare_selection.xml",
        "security/ir.model.access.csv",
        "data/data.xml"
    ],
    "assets": {
        "web.assets_frontend": [
                "custom_fields/static/src/custom_input_form/*.js",
                "custom_fields/static/src/custom_input_form/*.scss"
        ]
},
    "demo": [
        
    ],
    "external_dependencies": {},
    "summary": "The technical core to add new fields for Odoo documents without any special knowledge",
    "description": """For the full details look at static/description/index.html
* Features * 
#odootools_proprietary""",
    "images": [
        "static/description/main.png"
    ],
    "price": "28.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=108&ticket_version=16.0&url_type_id=3",
}