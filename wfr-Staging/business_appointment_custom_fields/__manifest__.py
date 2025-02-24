# -*- coding: utf-8 -*-
{
    "name": "Universal Appointments: Custom Fields",
    "version": "16.0.1.0.3",
    "category": "Extra Tools",
    "author": "faOtools",
    "website": "https://faotools.com/apps/16.0/universal-appointments-custom-fields-748",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "custom_fields",
        "business_appointment"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/custom_appointment_contact_info_field.xml",
        "views/custom_business_resource_type_field.xml",
        "views/custom_business_resource_field.xml",
        "views/custom_appointment_product_field.xml",
        "views/business_appointment_core.xml",
        "views/business_appointment.xml",
        "wizard/choose_appointment_customer.xml",
        "views/business_resource_type.xml",
        "views/business_resource.xml",
        "views/appointment_product.xml",
        "views/menu.xml",
        "data/data.xml"
    ],
    "assets": {},
    "demo": [
        
    ],
    "external_dependencies": {},
    "summary": "The extension to the Universal Appointments app introduces custom details for appointments, resources, and services",
    "description": """For the full details look at static/description/index.html
* Features * 
#odootools_proprietary""",
    "images": [
        "static/description/main.png"
    ],
    "price": "20.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=133&ticket_version=16.0&url_type_id=3",
}