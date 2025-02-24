# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "SEPA pain.001.001.09",
    'summary': """Export payments as SEPA Credit Transfer files""",
    'category': 'Accounting/Accounting',
    'description': """
        Support for the new SEPA pain.001.001.09 format.
        Generate payment orders as recommended by the SEPA norm, thanks to pain.001 messages.
        The generated XML file can then be uploaded to your bank.

        This module follows the implementation guidelines issued by the European Payment Council.
        For more information about the SEPA standards : http://www.iso20022.org/ and http://www.europeanpaymentscouncil.eu/
    """,
    'version': '1.0',
    'depends': ['account_sepa'],
    'data': [
        'views/account_payment_views.xml',
        'views/res_company_views.xml',
        'views/res_partner_views.xml',
    ],
    'auto_install': True,
    'license': 'OEEL-1',
}
