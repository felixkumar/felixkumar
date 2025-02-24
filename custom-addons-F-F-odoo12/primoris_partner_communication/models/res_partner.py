# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) BrowseInfo (http://browseinfo.in)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import datetime
from lxml import etree
import math
import pytz
import threading



from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT


class res_partner(models.Model):
    _inherit = "res.partner"

    fax   = fields.Char(string = 'Fax')
    tel1  = fields.Char(string = 'Telephone1')
    contact_person1_phone = fields.Char(string = 'Contact Person Phone1')
    contact_name1 = fields.Char(string = 'Primary Contact Person')
    contact_name2 = fields.Char(string = 'Contact Person Name1')
    phone_type = fields.Char(string = 'Phone Type')

class res_company(models.Model):
    _inherit = "res.company"

    fax   = fields.Char(string = 'Fax')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
