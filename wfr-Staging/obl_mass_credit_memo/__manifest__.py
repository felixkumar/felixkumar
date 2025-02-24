{
    'name': 'OBL Mass Credit Memo',
    'version': '16.0.0.1',
    'summary': 'Allows users to create a credit note for multiple OBL Records',
    'description': 'Allows users to create a credit note for multiple OBL Records',
    'author': 'SIGB',
    'license': 'AGPL-3',
    'depends': ['mc_freight_app', 'edi_export_account'],
    'data': [
        'views/freight_freight.xml',
        'views/account_move.xml',
    ],
    'installable': True,
    'auto_install': False
}
