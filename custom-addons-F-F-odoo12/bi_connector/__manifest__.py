# -*- encoding: UTF-8 -*-
##############################################################################
#
# Odoo, Open Source Management Solution
# Copyright (C) 2020-Today Xetechs.
# (<https://xetechs.com>)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    'name': "Xetechs BI connector",
    'summary': """
        Connector for the Xetechs BI App""",
    'description': """
         Connector for the Xetechs BI App
    """,
    'website': 'https://www.xetechs.odoo.com',
    'author': 'Fernando Flores --> fflores@xetechs.com',

    'category': 'Extra Tools',
    'version': '0.1',
    'depends': ['base'],
    'data': [
        'views/bi_connector_settings.xml'
    ]
}
