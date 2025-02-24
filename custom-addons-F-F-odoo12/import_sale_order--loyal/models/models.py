# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import base64
from io import BytesIO
import time
import tempfile
import binascii
import xlrd
import io
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime,timedelta
from odoo.exceptions import Warning
from odoo import models, fields, exceptions, api, _
from odoo.exceptions import UserError, ValidationError
import pytz
import logging
from xlrd import open_workbook


_logger = logging.getLogger(__name__)

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


class ImportOrder(models.TransientModel):
    _name = "import.sale.order"

    file = fields.Binary('File')
    product_selection = fields.Selection([('code', 'Code'),('ref', 'Reference')], string='Product Selection', default='code')
    import_option = fields.Selection([('xls', 'XLS File')], string='Select', default='xls')
    sample_option = fields.Selection([('xls', 'XLS')], string='Sample Type', default='xls')
    down_samp_file = fields.Boolean(string='Download Sample Files')

    def make_sale_order(self, values):
        invoice_obj = self.env['sale.order']

        partner_id = self.find_partner(values.get('name'))
        # product_id = self.find_product(values.get('order_line'))

        inv_id = invoice_obj.create({
            'partner_id': partner_id.id,
            # 'partner_invoice_id': self.partner.id,
            # 'partner_shipping_id': self.partner.id,
            'order_line':values['order_line']
            # 'order_line': [(0, 0, {'name': partner_id.name,
            #                        'product_id': p.id,
            #                        'product_uom_qty': 5})]
                                   # 'product_uom': p.uom_id.id,
                                   # 'price_unit': p.list_price,
                                   # 'tax_id': self.company_data['default_tax_sale']})],
            # 'pricelist_id': self.company_data['default_pricelist'].id,
        })

        return inv_id


    def find_product(self, name):
        if self.product_selection=='ref':
            currency_obj = self.env['product.product']
            product_search = currency_obj.search([('default_code', '=', name)])
        if self.product_selection=='code':
            currency_obj = self.env['product.customerinfo']
            customer_search = currency_obj.search([('product_code.name', '=', name)])
            product_search = self.env['product.product'].search([('product_tmpl_id','=',customer_search.product_tmpl_id.id)])
        if product_search:
            return product_search
        # else:
        #     raise Warning(_(' "%s" Product are not available.') % name)


    def find_partner(self, name):
        partner_obj = self.env['res.partner']
        partner_search = partner_obj.search([('ref', '=', name)])
        if partner_search:
            return partner_search
        else:
            raise Warning(_(' "%s" Partner are not available.') % name)
            # partner_id = partner_obj.create({
            #     'badge_id': name})
            # return partner_id




    def import_xls(self):
        # wb = xlrd.open_workbook(file_contents=base64.decodestring(self.file))
        # for sheet in wb.sheets():
        #     for row in range(sheet.nrows):
        #         for col in range(sheet.ncols):
        #             print(sheet.cell(row, col).value)
        if self.import_option == 'xls':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                values = {}
                invoice_ids = []
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except Exception:
                raise exceptions.Warning(_("Please select an XLS file or You have selected invalid file"))

            excel_list=[]
            customer_code = ''
            val = {}
            for row_no in range(sheet.nrows):
                if row_no <= 0:
                    fields = map(lambda row: row.value.encode('utf-8'), sheet.row(row_no))
                if row_no == 1:
                    customer_line = list(
                        map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                            sheet.row(row_no)))
                    customer_code = customer_line[1]
                if row_no >= 3:
                    # line = list(
                    #     map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                    #         sheet.row(row_no)))

                    line = [k.value for k in sheet.row(row_no)]

                    if isinstance(line[1], str):
                        line = [k.value for k in sheet.row(row_no)]
                    else:
                        if isinstance(line[1], float):
                            line[1] = int(line[1])
                            line[1] = str(line[1])
                        if isinstance(line[1],int):
                            line[1] = str(line[1])


                    product_val = self.find_product(line[1])

                    if product_val:
                        excel_list.append((0, 0, {'product_id': product_val.id, 'product_uom_qty': line[3]}))

                    # excel_list.append(line[1])
                    if len(line) > 4:
                        raise Warning(_('Your File has extra column please refer sample file'))

            values.update({'name': customer_code,
                            'order_line':excel_list,

                                   })


            res = self.make_sale_order(values)
            invoice_ids.append(res)
        return res

    # def download_auto(self):
    #
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': '/web/binary/download_document?model=import.sale.order&id=%s' % (self.id),
    #         'target': 'new',
    #     }
