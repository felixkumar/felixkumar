# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright © 2018 Primoris Systems. (<https://primorissystems.com>).
#    Copyright (C) 2004-2016 Odoo S.A. (<http://www.odoo.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Total Weight and volume Estimation",

    'summary': """
        Calculates Total Gross Weight Total Net Weight and Volume.
        """,

    'description': """
        This module will calculate the total Gross Weight, Net Weight and volume of every product in the order line and invoice lines.
        """,

    'author': "Primoris Systems",
    'website': "https://primorissystems.com",
    'category': 'Accounting',
    'version': '0.1',
    'depends': ['base', 'sale', 'account', 'purchase', 'stock', 'sale_stock' ,'stock_account',],
    'data': [
        'sale_order_weight.xml',
        'purchase_order_weight.xml',
        'acc_invoice_weight.xml',
        'delivery_order_weight.xml',
    ],
}
