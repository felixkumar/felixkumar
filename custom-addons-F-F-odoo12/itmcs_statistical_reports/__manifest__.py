{
    'name': 'Business Analytics Reports',
    'category': 'Business Analytics',
    'author': 'ITMusketeers Consultancy Services LLP',
    'description': """
================================================================================
Installation
================================================================================

Make sure you have ``xlsxwriter`` Python module installed::

$ pip install xlsxwriter

Usage
================================================================================

1.Generate customer or warehouse wise report in pdf and xls file.
2.Generate overdue report in pdf and xlsx file for customer.
3.Display sale price change log details. 
================================================================================
""",
    'depends': ['sales_team' , 'web', 'base', 'hr', 'sale', 'product', 'stock', 'sale_stock', 'sale_margin', 'purchase', 'point_of_sale', 'web_widget_color','report_xlsx'],
    'summary': ' To Generate custom reports ',

    'data': [
             'security/ir.model.access.csv',
            'security/sale_margin_report_group.xml',
            'views/custom_sale_report_templates.xml',
            'static/src/xml/web_assets_view.xml',
             # 'views/overdue_report_view.xml',
            'views/sale_report_view.xml',
            'views/custom_header_layout.xml',
             # 'views/stock_report_view.xml',
             # 'views/overdue_report_templates.xml',
             # 'views/stock_report_templates.xml',
             # 'views/profit_analysis_templates.xml',
             # 'views/purchase_analysis_templates.xml',
             # 'views/cash_report_template.xml',
             # 'views/cash_report_view.xml',
             # 'wizard/overdue_report_wizard.xml',
             'wizard/sale_analysis_report_wizard.xml',
             # 'wizard/stock_report_wizard.xml',
             # 'wizard/profit_analysis_wizard.xml',
             # 'wizard/purchase_analysis_report.xml',
             # 'wizard/cash_report_wizard.xml',
             'views/custom_xlsx.xml',
             'views/res_company.xml',
             'views/custom_report.xml',
             ],
    'price': '99.00',
    'currency': "EUR",
    'images':['static/description/Banner.png'],
    'installable': True,
}
