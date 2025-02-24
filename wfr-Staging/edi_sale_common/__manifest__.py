{
    'name': 'Sale Order EDI',
    'summary': 'Sale Order EDI',
    'sequence': 100,
    'license': 'OPL-1',
    'website': 'https://www.odoo.com',
    'version': '1.3',
    'author': 'Odoo Inc',
    'description': """
        Common Fields for Sale Order EDI
    """,
    'category': 'Custom Development',
    'cloc_exclude': ['**/*'],
    # any module necessary for this one to work correctly
    'depends': ['base_edi', 'sale_management', 'edi_product_common'],
    'data': [
        'security/ir.model.access.csv',
        'data/actions.xml',
        'data/defaults.xml',
        'views/charge_allowance.xml',
        'views/partner_views.xml',
        'views/payment_term_views.xml',
        'views/product_views.xml',
        'views/sale_views.xml',
        'views/uom_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
