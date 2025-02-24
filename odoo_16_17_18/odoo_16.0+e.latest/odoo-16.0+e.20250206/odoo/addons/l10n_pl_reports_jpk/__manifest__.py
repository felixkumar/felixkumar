# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Poland - JPK_VAT Enterprise',
    'version': '1.0',
    'description': """
        This module provides the possibility to generate the JPK_VAT in xml, for Poland.
        
        Currently, does not report specific values for :
        - Cash basis for entries with input tax (MK)
        - Margin-based operations (MR_T/MR_UZ)
        - Bills for agricultural products (VAT_RR)
        - Operations through electronic interfaces (IED)
        - Invoices done with KSef 
    """,
    'category': 'Accounting/Localizations/Reporting',
    'depends': [
        'l10n_pl_jpk',
        'account_accountant',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/l10n_pl_wizard_xml_export_options_views.xml',
        'data/jpk_export_templates.xml',
        'data/tax_report.xml',
    ],
    'auto_install': True,
    'installable': True,
    'website': 'https://www.odoo.com/app/accounting',
    'license': 'OEEL-1',
}
