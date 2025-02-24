# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from odoo.exceptions import Warning ,ValidationError
from odoo import models, fields, exceptions, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from xlrd import open_workbook
import os
import tempfile
import binascii
from xlwt import Workbook
import logging
_logger = logging.getLogger(__name__)
from io import StringIO
import io

try:
    import xmlrpclib
except ImportError:
    _logger.debug('Cannot `import xmlrpclib`.')

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

class gen_inv(models.TransientModel):
    _name = "gen.inv"

    file = fields.Binary('File')
    inv_name = fields.Char('Inventory Name')
    location_ids = fields.Many2many('stock.location','rel_location_wizard',string= "Location")
    import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')
    import_prod_option = fields.Selection([('barcode', 'Barcode'),('code', 'Code'),('name', 'Name')],string='Import Product By ',default='code')
    lot_option = fields.Boolean(string="Import Serial/Lot number with Expiry Date")
    location_id_option = fields.Boolean(string="Allow to Import Location on inventory line from file")
    file_name = fields.Char()
    
    
    def make_inventory_date(self, date):
        DATETIME_FORMAT = "%Y-%m-%d"
        if date:
            try:
                i_date = datetime.strptime(date, DATETIME_FORMAT).date()
            except Exception:
                raise ValidationError(_('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))
            return i_date
        else:
            raise ValidationError(_('Date field is blank in sheet Please add the date.'))

    def import_csv(self):
        """Load Inventory data from the CSV file."""
        if not self.file:
            raise ValidationError(_("Please select a file first then proceed"))
        if self.import_option == 'csv': 
            """Load Inventory data from the CSV file."""
            if self.file:
                file_name = str(self.file_name)
                extension = file_name.split('.')[1]
            if extension not in ['csv','CSV']:
                raise ValidationError(_('Please upload only csv file.!'))
            
            if self.lot_option == True:
                if self.location_id_option == True:
                    keys=['code', 'quantity','UOM','lot','life_date','line_location_id'] 
                else:
                    keys=['code', 'quantity','UOM','lot','life_date']
            elif self.location_id_option == True:
                keys=['code', 'quantity','UOM','lot','line_location_id']
            else:
                keys=['code', 'quantity','UOM','lot'] 
            ctx = self._context
            stloc_obj = self.env['stock.location']
            inventory_obj = self.env['stock.quant']
            product_obj = self.env['product.product']
            stock_lot_obj = self.env['stock.production.lot']
            csv_data = base64.b64decode(self.file)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            data_file.seek(0)
            file_reader = []
            csv_reader = csv.reader(data_file, delimiter=',')
            try:
                file_reader.extend(csv_reader)
            except Exception:
                raise ValidationError(_("Invalid file!"))
            values = {}
            product_ids_inv = []
            inventory_id = self.env['stock.quant'].create({'name':self.inv_name,'location_ids':self.location_ids.ids,'company_id' : self.env.user.company_id.id})

            for i in range(len(file_reader)):
                val = {}
                try:
                     field = list(map(str, file_reader[i]))
                except ValueError:
                     raise ValidationError(_("Don't Use Character only use numbers"))
                
                values = dict(zip(keys, field))
                if self.import_prod_option == 'barcode':
                    prod_lst = product_obj.search([('barcode',  '=',values['code'])])
                    if len(prod_lst) == 0:
                        raise ValidationError(_('Products with barcode not found in file.'))

                elif self.import_prod_option == 'code':
                    prod_lst = product_obj.search([('default_code', '=', values['code'])])
                    if len(prod_lst) == 0:
                        raise ValidationError(_('Products with code not found in file.'))

                else:
                    prod_lst = product_obj.search([('name', '=', values['code'])])
                           

                if len(prod_lst):
                    if  prod_lst[0].id not in product_ids_inv:
                        product_ids_inv.append(prod_lst[0].id)
                inventory_id.product_ids = product_ids_inv
                if self.lot_option == True:
                    if self.location_id_option == True:
                        if prod_lst:
                            val['product'] = prod_lst[0].id
                            val['quantity'] = values['quantity']
                            val['UOM'] = values['UOM']
                            val['lot'] = values['lot']
                            val['life_date'] = values['life_date']
                        if bool(val):
                            product_uom_obj = self.env['uom.uom']
                            product_uom_id = product_uom_obj.search([('name','=',val['UOM'])])
                            if not product_uom_id:
                                raise UserError(_('"%s" Product UOM category is not available.')%(val['UOM'] ))
                                
                            stock_location_id = self.env['stock.location'].search([('name','=',values['line_location_id'])])
                            if not stock_location_id:
                                raise UserError(_('"%s" Location is not available.')%(values['line_location_id']))

                            lot_id = stock_lot_obj.search([('product_id','=',val['product']),('name','=',val['lot'])])
                            for lot in lot_id:
                                lot_obj = stock_lot_obj.browse(lot_id)
                                
                            if not lot_id:
                                date_exp = self.make_inventory_date(val['life_date'])
                                lot = stock_lot_obj.create({'name': val['lot'],
                                                      'product_id': val['product'],
                                                        'expiration_date': date_exp,
                                                        'company_id' : self.env.user.company_id.id})
                                lot_id = lot


                            inventory_id.action_open_inventory_lines()
                            lines = self.env['stock.inventory.line'].create({'product_id':val['product'] , 'inventory_id' : inventory_id.id ,'location_id' : stock_location_id.id, 'product_uom_id' : product_uom_id.id  ,'product_qty': val['quantity'],'prod_lot_id':lot_id.id})                        
                        else:
                            continue
                    else:
                        if prod_lst:
                            val['product'] = prod_lst[0].id
                            val['quantity'] = values['quantity']
                            val['UOM'] = values['UOM']
                            val['lot'] = values['lot']
                            val['life_date'] = values['life_date']
                        if bool(val):
                            product_uom_obj = self.env['uom.uom']
                            product_uom_id = product_uom_obj.search([('name','=',val['UOM'])])
                            if not product_uom_id:
                                raise UserError(_('"%s" Product UOM category is not available.')%(val['UOM'] ))
                                
                            lot_id = stock_lot_obj.search([('product_id','=',val['product']),('name','=',val['lot'])])
                            for lot in lot_id:
                                lot_obj = stock_lot_obj.browse(lot_id)
                                
                            if not lot_id:
                                date_exp = self.make_inventory_date(val['life_date'])
                                lot = stock_lot_obj.create({'name': val['lot'],
                                                      'product_id': val['product'],
                                                        'expiration_date': date_exp,
                                                        'company_id' : self.env.user.company_id.id})
                                lot_id = lot

                            inventory_id.action_open_inventory_lines()
                            lines = self.env['stock.inventory.line'].create({'product_id':val['product'] , 'inventory_id' : inventory_id.id , 'location_id' : self.location_ids[0].id, 'product_uom_id' : product_uom_id.id  ,'product_qty': val['quantity'],'prod_lot_id':lot_id.id})
                        else:
                            continue
                else:
                    if self.location_id_option == True:
                        if prod_lst:
                            val['product'] = prod_lst[0].id
                            val['quantity'] = values['quantity']
                            val['UOM'] = values['UOM']
                            val['lot'] = values['lot']
                        if bool(val):
                            product_uom_obj = self.env['uom.uom']
                            product_uom_id = product_uom_obj.search([('name','=',val['UOM'])])
                            if not product_uom_id:
                                raise UserError(_('"%s" Product UOM category is not available.')%(val['UOM'] ))
                                
                            stock_location_id = self.env['stock.location'].search([('name','=',values['line_location_id'])])
                            if not stock_location_id:
                                raise UserError(_('"%s" Location is not available.')%(values['line_location_id']))

                            lot_id = stock_lot_obj.search([('product_id','=',val['product']),('name','=',val['lot'])])
                            for lot in lot_id:
                                lot_obj = stock_lot_obj.browse(lot_id)
                                
                            if not lot_id:
                                lot = stock_lot_obj.create({'name': val['lot'],
                                                      'product_id': val['product'],
                                                      'company_id' : self.env.user.company_id.id})
                                lot_id = lot


                            inventory_id.action_open_inventory_lines()
                            lines = self.env['stock.inventory.line'].create({'product_id':val['product'] , 'inventory_id' : inventory_id.id ,'location_id' : stock_location_id.id, 'product_uom_id' : product_uom_id.id  ,'product_qty': val['quantity'],'prod_lot_id':lot_id.id})
                        else:
                            continue 
                    else:   
                        if prod_lst:
                            val['product'] = prod_lst[0].id
                            val['quantity'] = values['quantity']
                            val['UOM'] = values['UOM']
                            val['lot'] = values['lot']
                        if bool(val):
                            product_uom_obj = self.env['uom.uom']
                            product_uom_id = product_uom_obj.search([('name','=',val['UOM'])])
                            if not product_uom_id:
                                raise UserError(_('"%s" Product UOM category is not available.')%(val['UOM'] ))
                                
                            lot_id = stock_lot_obj.search([('product_id','=',val['product']),('name','=',val['lot'])])
                            for lot in lot_id:
                                lot_obj = stock_lot_obj.browse(lot_id)
                                
                            if not lot_id:
                                lot = stock_lot_obj.create({'name': val['lot'],
                                                      'product_id': val['product'],
                                                      'company_id' : self.env.user.company_id.id})
                                lot_id = lot
                            inventory_id.action_open_inventory_lines()
                            lines = self.env['stock.inventory.line'].create({'product_id':val['product'] , 'inventory_id' : inventory_id.id , 'location_id' : self.location_ids[0].id, 'product_uom_id' : product_uom_id.id  ,'product_qty': val['quantity'],'prod_lot_id':lot_id.id})
                        else:
                            continue 
                        
            res = inventory_obj.with_context(ids=inventory_id).prepare_inventory()
            return res
        else:
            if self.file:
                file_name = str(self.file_name)
                extension = file_name.split('.')[1]
            if extension not in ['xls','xlsx','XLS','XLSX']:
                raise ValidationError(_('Please upload only xls file.!'))
            fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
            product_ids_inv = []
            inventory_id = self.env['stock.inventory'].create({'name':self.inv_name,'location_ids':self.location_ids.ids,'company_id' : self.env.user.company_id.id})
            product_obj = self.env['product.product']
            stock_lot_obj = self.env['stock.production.lot']
            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    fields = list(map(lambda row:row.value.encode('utf-8'), sheet.row(row_no)))
                else:
                    line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))

                    if self.lot_option == True:
                        if self.location_id_option == True:
                            if line:
                                values.update({'code':line[0],'quantity':line[1],'UOM':line[2],'lot':line[3],'life_date':line[4],'line_location_id':line[5]})
                                if line[4] != '':
                                    if line[4].split('/'):
                                        if len(line[4].split('/')) > 1:
                                            raise ValidationError(_('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))
                                        if len(line[4]) > 8 or len(line[4]) < 5:
                                            raise ValidationError(_('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))
                                a1 = int(float(line[4]))
                                a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                                date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
                                if self.import_prod_option == 'barcode':
                                    prod_lst = product_obj.search([('barcode',  '=',values['code'])])
                                    if len(prod_lst) == 0:
                                        raise ValidationError(_('Products with barcode not found in file.'))
                                elif self.import_prod_option == 'code':
                                    prod_lst = product_obj.search([('default_code', '=', values['code'])])
                                    if len(prod_lst) == 0:
                                        raise ValidationError(_('Products with code not found in file.'))
                                else:
                                    prod_lst = product_obj.search([('name', '=', values['code'])])
                                    if len(prod_lst) == 0:
                                        raise ValidationError(_('Products with name not found in file.'))
                                if len(prod_lst):
                                    if  prod_lst[0].id not in product_ids_inv:
                                        product_ids_inv.append(prod_lst[0].id)
                                inventory_id.product_ids = product_ids_inv

                                if prod_lst:
                                    val['product'] = prod_lst[0].id
                                    val['quantity'] = values['quantity']
                                    val['UOM'] = values['UOM']
                                    val['lot'] = values['lot']
                                    val['life_date'] = date_string
                                if bool(val):
                                    product_uom_obj = self.env['uom.uom']
                                    product_uom_id = product_uom_obj.search([('name','=',val['UOM'])])
                                    if not product_uom_id:
                                        raise UserError(_('"%s" Product UOM category is not available.')%(val['UOM'] ))
                                        
                                    stock_location_id = self.env['stock.location'].search([('name','=',values['line_location_id'])])
                                    if not stock_location_id:
                                        raise UserError(_('"%s" Location is not available.')%(values['line_location_id']))

                                    lot_id = stock_lot_obj.search([('product_id','=',val['product']),('name','=',val['lot'])])
                                    for lot in lot_id:
                                        lot_obj = stock_lot_obj.browse(lot_id)
                                
                                    if not lot_id:
                                        lot = stock_lot_obj.create({'name': val['lot'],
                                                      'product_id': val['product'],
                                                              'expiration_date': date_string,
                                                              'company_id' : self.env.user.company_id.id})
                                        lot_id = lot
                                    inventory_id.action_open_inventory_lines()
                                    lines = self.env['stock.inventory.line'].create({'product_id':val['product'] ,'inventory_id' : inventory_id.id, 'location_id' : stock_location_id.id, 'product_uom_id' : product_uom_id.id  ,'product_qty': val['quantity'],'prod_lot_id':lot_id.id})
                                else:
                                    continue
                        else:
                            if line:
                                values.update({'code':line[0],'quantity':line[1],'UOM':line[2],'lot':line[3],'life_date':line[4]})
                                if line[4] != '':
                                    if line[4].split('/'):
                                        if len(line[4].split('/')) > 1:
                                            raise ValidationError(_('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))
                                        if len(line[4]) > 8 or len(line[4]) < 5:
                                            raise ValidationError(_('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))
                                a1 = int(float(line[4]))
                                a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                                date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
                                if self.import_prod_option == 'barcode':
                                    prod_lst = product_obj.search([('barcode',  '=',values['code'])])
                                    if len(prod_lst) == 0:
                                        raise ValidationError(_('Products with barcode not found in file.'))
                                elif self.import_prod_option == 'code':
                                    prod_lst = product_obj.search([('default_code', '=', values['code'])])
                                    if len(prod_lst) == 0:
                                        raise ValidationError(_('Products with code not found in file.'))
                                else:
                                    prod_lst = product_obj.search([('name', '=', values['code'])]) 
                                    if len(prod_lst) == 0:
                                        raise ValidationError(_('Products with name not found in file.'))  
                                if len(prod_lst):
                                    if  prod_lst[0].id not in product_ids_inv:
                                        product_ids_inv.append(prod_lst[0].id)
                                inventory_id.product_ids = product_ids_inv                                             
                                if prod_lst:
                                    val['product'] = prod_lst[0].id
                                    val['quantity'] = values['quantity']
                                    val['UOM'] = values['UOM']
                                    val['lot'] = values['lot']
                                    val['life_date'] = date_string
                                if bool(val):
                                    product_uom_obj = self.env['uom.uom']
                                    product_uom_id = product_uom_obj.search([('name','=',val['UOM'])])
                                    if not product_uom_id:
                                        raise UserError(_('"%s" Product UOM category is not available.')%(val['UOM'] ))
                                        
                                    lot_id = stock_lot_obj.search([('product_id','=',val['product']),('name','=',val['lot'])])
                                    for lot in lot_id:
                                        lot_obj = stock_lot_obj.browse(lot_id)
                                
                                    if not lot_id:
                                        lot = stock_lot_obj.create({'name': val['lot'],
                                                      'product_id': val['product'],
                                                              'expiration_date': date_string,
                                                              'company_id' : self.env.user.company_id.id})
                                        lot_id = lot


                                    inventory_id.action_open_inventory_lines()
                                    lines = self.env['stock.inventory.line'].create({'product_id':val['product'] ,'inventory_id' : inventory_id.id , 'location_id' : self.location_ids[0].id, 'product_uom_id' : product_uom_id.id  ,'product_qty': val['quantity'],'prod_lot_id':lot_id.id})
                                else:
                                    continue
                    else:
                        if self.location_id_option == True:
                            if line:
                                values.update({'code':line[0],'quantity':line[1],'UOM':line[2],'lot':line[3],'line_location_id':line[4]})
                                if self.import_prod_option == 'barcode':
                                    prod_lst = product_obj.search([('barcode',  '=',values['code'])])
                                    if len(prod_lst) == 0:
                                        raise ValidationError(_('Products with barcode not found in file.'))
                                elif self.import_prod_option == 'code':
                                    prod_lst = product_obj.search([('default_code', '=', values['code'])])
                                    if len(prod_lst) == 0:
                                        raise ValidationError(_('Products with code not found in file.'))
                                else:
                                    prod_lst = product_obj.search([('name', '=', values['code'])])
                                    if len(prod_lst) == 0:
                                        raise ValidationError(_('Products with name not found in file.'))
                                
                                if len(prod_lst):
                                    if  prod_lst[0].id not in product_ids_inv:
                                        product_ids_inv.append(prod_lst[0].id)
                                inventory_id.product_ids = product_ids_inv
                                if prod_lst:
                                    val['product'] = prod_lst[0].id
                                    val['quantity'] = values['quantity']
                                    val['UOM'] = values['UOM']
                                    val['lot'] = values['lot']
                                if bool(val):
                                    product_uom_obj = self.env['uom.uom']
                                    product_uom_id = product_uom_obj.search([('name','=',val['UOM'])])
                                    if not product_uom_id:
                                        raise UserError(_('"%s" Product UOM category is not available.')%(val['UOM'] ))
                                        
                                    stock_location_id = self.env['stock.location'].search([('name','=',values['line_location_id'])])
                                    if not stock_location_id:
                                        raise UserError(_('"%s" Location is not available.')%(values['line_location_id']))

                                    lot_id = stock_lot_obj.search([('product_id','=',val['product']),('name','=',val['lot'])])
                                    for lot in lot_id:
                                        lot_obj = stock_lot_obj.browse(lot_id)
                                
                                    if not lot_id:
                                        lot = stock_lot_obj.create({'name': val['lot'],
                                                      'product_id': val['product'],
                                                      'company_id' : self.env.user.company_id.id})
                                        lot_id = lot

                                    inventory_id.action_open_inventory_lines()
                                    lines = self.env['stock.inventory.line'].create({'product_id':val['product'] ,'inventory_id' : inventory_id.id , 'location_id' : stock_location_id.id, 'product_uom_id' : product_uom_id.id  ,'product_qty': val['quantity'],'prod_lot_id':lot_id.id})
                                else:
                                    continue 
                        else:
                            if line:
                                values.update({'code':line[0],'quantity':line[1],'UOM':line[2],'lot':line[3]})
                                if self.import_prod_option == 'barcode':
                                    prod_lst = product_obj.search([('barcode',  '=',values['code'])])
                                    if len(prod_lst) == 0:
                                        raise ValidationError(_('Products with barcode not found in file.'))
                                elif self.import_prod_option == 'code':
                                    prod_lst = product_obj.search([('default_code', '=', values['code'])])
                                    if len(prod_lst) == 0:
                                        raise ValidationError(_('Products with code not found in file.'))
                                else:
                                    prod_lst = product_obj.search([('name', '=', values['code'])]) 
                                    if len(prod_lst) == 0:
                                        raise ValidationError(_('Products with name not found in file.'))
                                if len(prod_lst):
                                    if  prod_lst[0].id not in product_ids_inv:
                                        product_ids_inv.append(prod_lst[0].id)
                                inventory_id.product_ids = product_ids_inv           
                                if prod_lst:
                                    val['product'] = prod_lst[0].id
                                    val['quantity'] = values['quantity']
                                    val['UOM'] = values['UOM']
                                    val['lot'] = values['lot']
                                if bool(val):
                                    product_uom_obj = self.env['uom.uom']
                                    product_uom_id = product_uom_obj.search([('name','=',val['UOM'])])
                                    if not product_uom_id:
                                        raise UserError(_('"%s" Product UOM category is not available.')%(val['UOM'] ))
                                        
                                    lot_id = stock_lot_obj.search([('product_id','=',val['product']),('name','=',val['lot'])])
                                    for lot in lot_id:
                                        lot_obj = stock_lot_obj.browse(lot_id)
                                
                                    if not lot_id:
                                        lot = stock_lot_obj.create({'name': val['lot'],
                                                      'product_id': val['product'],
                                                      'company_id' : self.env.user.company_id.id})
                                        lot_id = lot

                                    inventory_id.action_open_inventory_lines()  
                                    lines = self.env['stock.inventory.line'].create({'product_id':val['product'] ,'inventory_id' : inventory_id.id , 'location_id' : self.location_ids[0].id, 'product_uom_id' : product_uom_id.id  ,'product_qty': val['quantity'],'prod_lot_id':lot_id.id})
                                else:
                                    continue                            
                                                                  
            res = self.env['stock.inventory'].with_context(ids=inventory_id).prepare_inventory()
            return res

class stock_inventory(models.Model):
    _inherit = "stock.inventory"


    
    def action_start(self):
        if self._context.get('ids'):
            self = self._context.get('ids')
            for inventory in self:
                vals = {'state': 'confirm', 'date': fields.Datetime.now()}
                vals.update({'line_ids': inventory.line_ids.ids})
                inventory.write(vals)
        else:
            super(stock_inventory, self).action_start()
        return True
    prepare_inventory = action_start

