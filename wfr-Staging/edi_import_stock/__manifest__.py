{
    'name': 'EDI Import Stock Moves',
    'summary': 'EDI Import Stock Moves',
    'sequence': 100,
    'license': 'OPL-1',
    'website': 'https://www.odoo.com',
    'version': '1.1',
    'author': 'Odoo Inc',
    'description': """
        EDI Import Stock Moves
    """,
    'category': 'Custom Development',
    'cloc_exclude': ['**/*'],
    # any module necessary for this one to work correctly
    'depends': ['edi_import', 'edi_sale_common', 'stock'],
    'data': [
        'data/edi_stock_data.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': '_create_picking_import_xsd'
}
