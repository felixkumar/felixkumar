{
    'name': "SEPA Direct Debit pain 008.001.08",
    'summary': """SEPA Direct Debit Schema (Pain 008.001.08) support.""",
    'category': 'Accounting/Accounting',
    'description': """
        Support for the new SEPA Direct Debit Schema (Pain 008.001.08) format.
        This module follows the implementation guidelines issued by the European Payment Council.
        For more information about the SEPA standards : http://www.iso20022.org/ and http://www.europeanpaymentscouncil.eu/
    """,
    'version': '1.0',
    'depends': ['account_sepa_direct_debit'],
    'data': [
        'views/account_journal_views.xml',
    ],
    'auto_install': True,
    'license': 'OEEL-1',
}
