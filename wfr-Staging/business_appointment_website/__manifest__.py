# -*- coding: utf-8 -*-
{
    "name": "Universal Appointments: Portal and Website",
    "version": "16.0.1.1.6",
    "category": "Website",
    "author": "faOtools",
    "website": "https://faotools.com/apps/16.0/universal-appointments-portal-and-website-747",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "business_appointment",
        "website",
        "portal",
        "auth_signup",
        "rating"
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/template.xml",
        "data/cron.xml",
        "views/res_config_settings.xml",
        "views/business_resource.xml",
        "views/business_resource_type.xml",
        "views/appointment_product.xml",
        "views/business_appointment_core.xml",
        "views/business_appointment.xml",
        "views/full_details_templates.xml",
        "views/templates.xml",
        "views/portal_templates.xml",
        "reports/appointment_analytic.xml"
    ],
    "assets": {
        "web.assets_frontend": [
                [
                        "include",
                        "business_appointment.time_slots"
                ],
                "business_appointment_website/static/src/scss/website_business_appointments.scss",
                "business_appointment_website/static/src/js/slots_widget.js",
                "business_appointment_website/static/src/js/appointments_portal.js"
        ]
},
    "demo": [
        
    ],
    "external_dependencies": {},
    "summary": "The extension to the Universal Appointments app to schedule appointments on the Odoo website and in the Odoo portal. Online appointments. Online Bookings",
    "description": """For the full details look at static/description/index.html
* Features * 
- Universal website bookings
- Configurable appointment pages
- Portal control of reservations
#odootools_proprietary""",
    "images": [
        "static/description/main.png"
    ],
    "price": "99.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=130&ticket_version=16.0&url_type_id=3",
}