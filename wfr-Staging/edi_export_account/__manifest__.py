{
    'name': 'Export Invoice EDI Document',
    'summary': 'Description',
    'sequence': 100,
    'license': 'OPL-1',
    'website': 'https://www.odoo.com',
    'version': '1.2',
    'author': 'Odoo Inc',
    'description': """
        Export Invoice EDI Document
    """,
    'category': 'Custom Development',
    'cloc_exclude': ['**/*'],
    # any module necessary for this one to work correctly
    'depends': ['edi_export', 'edi_sale_common'],
    'data': [
        'data/account_move_data.xml',
        'views/account_move_views.xml',
        'views/account_tax_views.xml',
        'views/res_partner_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': '_create_invoice_export_xsd'
}
