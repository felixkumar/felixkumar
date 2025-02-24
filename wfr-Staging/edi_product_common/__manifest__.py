{
    'name': 'EDI Product',
    'summary': 'Description',
    'sequence': 100,
    'license': 'OPL-1',
    'website': 'https://www.odoo.com',
    'version': '1.4',
    'author': 'Odoo Inc',
    'description': """
        - Add Product Fields Common to EDI
    """,
    'category': 'Custom Development',
    'cloc_exclude': ['**/*'],

    # any module necessary for this one to work correctly
    'depends': ['product'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
