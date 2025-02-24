# -*- coding: utf-8 -*-
{
    "name": "Appointments: Portal and Website",
    "version": "16.0.7",
    "category": "Website",
    'author': "TechUltra Solutions Pvt. Ltd.",
    'website': "https://www.techultrasolutions.com/",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "business_appointment_website","website"

    ],
    "data": [
        'views/templates.xml',
        'views/appointment_confirm_template.xml',
        'views/portal_templates.xml',
        'views/business_appointment_report.xml',
        'reports/ibl_obl_droupout_report.xml',
        'views/business_appointment.xml',
        'views/mail_template.xml',
        'views/views.xml',
        'data/mail_template_new_user.xml',
    ],
    "assets": {
        "web.assets_frontend": [
            'business_appointment_tus/static/src/js/skip_page.js'
        ],
    },
    "qweb": [

    ],
    "js": [
        
    ],
    "demo": [
        
    ],
}