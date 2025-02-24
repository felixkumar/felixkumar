# -*- coding: utf-8 -*-
{
    'name': "WareFor Reports",
    'summary': """
        WareFor Reports
    """,
    'description': """""",
    'author': "TechUltra Solutions Pvt. Ltd.",
    'website': "https://www.techultrasolutions.com/",
    'category': 'Human Resources/Contracts',
    "version": "16.0.16",
    'license': 'LGPL-3',
    'depends': ['mc_freight_app', 'warefor_3pl_tus'],
    'data': [
        'security/ir.model.access.csv',
        'views/sscc18_view.xml',
        'views/custom_views.xml',
        # 'views/custom_button_view_freight.xml',
        'wizard/loaded__with_pride_wizard_view.xml',
        'wizard/master_bol_wizard_view.xml',
        # 'wizard/house_bol_wizard_view.xml',
        'report/loaded_with_pride_template.xml',
        'report/master_bil_of_lading_template.xml',
        'report/shipment_manifest_template.xml',
        'report/pallet_labels_template.xml',
        'report/house_bill__of_lading_template.xml',
        'report/inherit_invoice.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'warefor_reports/static/src/js/report_popup.js',
        ],
    },

}
