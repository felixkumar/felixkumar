# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'EDI Document Synchronization Base',
    'version': '1.4',
    'category': 'Tools',
    'description': """
Allows you to configure EDI document exchange configurations
==============================================================
You can perform your own EDI XML export and import via FTP.
""",
    'author': "Odoo Inc",
    'website': "http://www.odoo.com",
    'license': 'OEEL-1',
    'depends': ['mail'],
    'data': [
        'security/base_edi_security.xml',
        'security/ir.model.access.csv',
        'views/edi_config_views.xml',
        'views/edi_mapping_views.xml',
        'views/res_partner_views.xml',
        'views/xml_xsd_views.xml',
        'wizard/xsd_import_views.xml',
        'data/ir_cron_data.xml',
    ],
    'demo': [
        'demo/xml_xsd_data.xml',
    ],
    'cloc_exclude': [
        'models/edi_config.py',
        'models/edi_message.py',
        'models/ftp_connection.py',
        'models/res_partner.py',
        'models/sftp_connection.py',
        'models/xml_xsd.py',
        'views/xml_xsd_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'base_edi/static/src/mapping_list_renderer/mapping_list_renderer.js',
            'base_edi/static/src/mapping_list_renderer/mapping_list_renderer.xml',
            'base_edi/static/src/mapping_widget/mapping_widget.js',
        ],
    },
    'installable': True,
}
