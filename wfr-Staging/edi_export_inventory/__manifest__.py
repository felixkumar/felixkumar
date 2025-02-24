{
    'name': 'EDI ',
    'summary': 'EDI ',
    'sequence': 100,
    'license': 'OPL-1',
    'website': 'https://www.odoo.com',
    'version': '1.1',
    'author': 'Odoo Inc',
    'description': """
        Configuration for EDI 
    """,
    'category': 'Custom Development',
    'cloc_exclude': ['**/*'],

    # any module necessary for this one to work correctly
    'depends': ['edi_export', 'edi_sale_common', 'product'],
    'data': [
       'data/data.xml',
       'views/res_partner_views.xml',
       'views/product_template_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': '_create_inventory_inquiry_export_xsd'
}
