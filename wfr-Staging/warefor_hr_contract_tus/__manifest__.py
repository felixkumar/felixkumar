# -*- coding: utf-8 -*-
{
    'name': "WareFor Employee Contract TUS",
    'summary': """
        WareFor Employee Contract by TUS
    """,
    'description': """""",
    'author': "TechUltra Solutions Pvt. Ltd.",
    'website': "https://www.techultrasolutions.com/",
    'category': 'Human Resources/Contracts',
    "version": "16.0.11",
    'license': 'LGPL-3',
    'depends': ['hr_payroll', 'hr_hourly_cost', 'hr_timesheet'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_contract_views.xml',
        'views/hour_types_views.xml',
        'views/hr_employees_views.xml',
        'views/account_analytic_line_views.xml',
    ],

    'images': [],
    'qweb': [],

}
