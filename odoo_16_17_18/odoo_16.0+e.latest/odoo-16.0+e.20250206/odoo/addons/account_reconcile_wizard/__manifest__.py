{
    'name': 'Account Reconcile Wizard',
    'category': 'Accounting/Accounting',
    'version': '1.0',
    'description': """Backports the reconciliation wizard introduced in version 16.3.""",
    'depends': ['account_accountant'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'wizard/account_reconcile_wizard.xml',
    ],
    'license': 'OEEL-1',
}
