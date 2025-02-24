{
    'name': 'EDI Document Import',
    'summary': 'Description',
    'sequence': 100,
    'license': 'OPL-1',
    'website': 'https://www.odoo.com',
    'version': '1.5',
    'author': 'Odoo Inc',
    'description': """
        EDI Document Import
    """,
    'category': 'Custom Development',
    'cloc_exclude': ['**/*'],
    # any module necessary for this one to work correctly
    'depends': ['base_edi'],
    'data': [
        'security/ir.model.access.csv',
        'views/edi_mapping_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
