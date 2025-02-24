# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
import tempfile
import binascii
import logging
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import Warning ,ValidationError
from odoo import models, fields, api, exceptions, _
_logger = logging.getLogger(__name__)
from io import StringIO
import io

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')


class account_bank_statement_wizard(models.TransientModel):
    _name= "account.bank.statement.wizard"

    file = fields.Binary('File')
    file_opt = fields.Selection([('excel','Excel'),('csv','CSV')],default='excel')
    file_name = fields.Char()

    
    def import_file(self):
        if not self.file:
            raise ValidationError(_('Please Select File'))
        if self.file_opt == 'csv':
            if self.file:
                file_name = str(self.file_name)
                extension = file_name.split('.')[1]
            if extension not in ['csv','CSV']:
                raise ValidationError(_('Please upload only csv file.!'))
            keys = ['date','ref','partner','memo','amount','currency']                    
            data = base64.b64decode(self.file)
            file_input = io.StringIO(data.decode("utf-8"))
            file_input.seek(0)
            reader_info = []
            reader = csv.reader(file_input, delimiter=',')
 
            try:
                reader_info.extend(reader)
            except Exception:
                raise ValidationError(_("Not a valid file!"))
            values = {}
            for i in range(len(reader_info)):
                field = list(map(str, reader_info[i]))
                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                        res = self._create_statement_lines(values)
        elif self.file_opt == 'excel':
            if self.file:
                file_name = str(self.file_name)
                extension = file_name.split('.')[1]
            if extension not in ['xls','xlsx','XLS','XLSX']:
                raise ValidationError(_('Please upload only xls file.!'))
            fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
            for row_no in range(sheet.nrows):
                if row_no <= 0:
                    fields = list(map(lambda row:row.value.encode('utf-8'), sheet.row(row_no)))
                else:
                    line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    if not line[0]:
                        raise ValidationError('Please Provide Date Field Value')
                        
                    if line[0].split('/'):
                        if len(line[0].split('/')) > 1:
                            raise ValidationError(_('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))
                        if len(line[0]) > 8 or len(line[0]) < 5:
                            raise ValidationError(_('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))    
                    a1 = int(float(line[0]))
                    a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                    date_string = a1_as_datetime.date().strftime('%Y-%m-%d')

                    ref =''
                    memo =''
                    if line[1] == '':
                        ref  == ''

                    else:
                        ref = line[1]
                    if line[3]  == '':
                        memo =''
                    else:
                         memo = line[3]

                    values.update( {'date':date_string,
                                    'ref': ref,
                                    'partner': line[2],
                                    'memo': memo,
                                    'amount': line[4],
                                    'currency' : line[5],
                                    })
                    res = self._create_statement_lines(values)
        self.env['account.bank.statement'].browse(self._context.get('active_id'))._end_balance()
        return res
#

    
    
    def _create_statement_lines(self,val):
        account_bank_statement_line_obj = self.env['account.bank.statement.line']
        partner_id = self._find_partner(val.get('partner'))
        if val.get('currency'):
            currency_id = self._find_currency(val.get('currency'))
        else:
            currency_id = False
        if val.get('date'):    
            date_to = self._find_bank_date(val.get('date'))
        else:
            raise ValidationError(_('Please Provide Date Field Value'))
            
        if not val.get('memo'):
            raise ValidationError(_('Please Provide Memo Field Value'))   
        bank_statement_lines = account_bank_statement_line_obj.create({
                                                'date':date_to,
                                                'payment_ref':val.get('ref'),
                                                'partner_id':partner_id,
                                                'name':val.get('memo'),
                                                'amount':val.get('amount'),
                                                'currency_id':currency_id,
                                                'statement_id':self._context.get('active_id'),
                                                })
        return True
#
    def _find_partner(self,name):
        partner_id = self.env['res.partner'].search([('name','=',name)])
        if partner_id:
            return partner_id.id
        else:
            return

    def _find_currency(self,currency):
        currency_id = self.env['res.currency'].search([('name','=',currency)])
        if currency_id:
            return currency_id.id
        else:
            raise ValidationError(_(' "%s" Currency are not available.') % currency)

    def _find_bank_date(self, date):
        DATETIME_FORMAT = "%Y-%m-%d"
        if date:
            try:
                i_date = datetime.strptime(date, DATETIME_FORMAT).date()
            except Exception:
                raise ValidationError(_('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))
            return i_date
        else:
            raise ValidationError(_('Please Provide Date Field Value'))

