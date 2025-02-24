# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": """Mexico - Electronic Delivery Guide Comex - Version 3.1""",
    'version': '1.0',
    'category': 'Accounting/Localizations/EDI',
    'description': """
    Bridge module to extend Version 3.1 of the delivery guide (Complemento XML Carta de Porte).
    - Exported goods (COMEX).
    - Extended address fields.
    """,
    'depends': [
        'l10n_mx_edi_stock_extended_30',
    ],
    'data': [
        'data/cfdi_cartaporte.xml',
        'views/report_cartaporte.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'auto_install': True,
    'post_init_hook': '_l10n_mx_edi_stock_extended_post_init_hook',
    'license': 'OEEL-1',
}
