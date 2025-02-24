{
    'name': 'EDI Sale Import',
    'summary': 'EDI Sale Import',
    'sequence': 100,
    'license': 'OPL-1',
    'website': 'https://www.odoo.com',
    'version': '1.5',
    'author': 'Odoo Inc',
    'description': """
        Configuration for EDI Sale Import
    """,
    'category': 'Custom Development',
    'cloc_exclude': ['**/*'],
    # any module necessary for this one to work correctly
    'depends': ['edi_import', 'edi_sale_common'],
    'data': [
        'data/edi_sale_data.xml',
        'views/res_partner_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': '_create_sale_import_xsd'
}
