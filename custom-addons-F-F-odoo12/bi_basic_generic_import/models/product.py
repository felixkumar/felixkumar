# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import tempfile
import binascii
from odoo.exceptions import Warning ,ValidationError
from odoo import models, fields, exceptions, api, _
import time
from datetime import date, datetime
import io
import logging
_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')
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

class gen_product(models.TransientModel):
    _name = "gen.product"

    file = fields.Binary('File')
    import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')
    product_option = fields.Selection([('create','Create Product'),('update','Update Product')],string='Option', required=True,default="create")
    product_search = fields.Selection([('by_code','Search By Code'),('by_name','Search By Name'),('by_barcode','Search By Barcode')],string='Search Product')
    file_name = fields.Char()
   
    def create_product(self, values):
        product_obj = self.env['product.product']
        product_categ_obj = self.env['product.category']
        product_uom_obj = self.env['uom.uom']
        if values.get('categ_id')=='':
            raise ValidationError(_('CATEGORY field can not be empty'))
        else:
            categ_id = product_categ_obj.search([('name','=',values.get('categ_id'))])
        
        if values.get('type') == 'Consumable':
            categ_type ='consu'
        elif values.get('type') == 'Service':
            categ_type ='service'
        elif values.get('type') == 'Stockable Product':
            categ_type ='product'
        else:
            categ_type = 'product'
        
        if values.get('uom_id')=='':
            uom_id = 1
        else:
            uom_search_id  = product_uom_obj.search([('name','=',values.get('uom_id'))])
            uom_id = uom_search_id.id
        
        if values.get('uom_po_id')=='':
            uom_po_id = 1
        else:
            uom_po_search_id  = product_uom_obj.search([('name','=',values.get('uom_po_id'))])
            uom_po_id = uom_po_search_id.id
        if values.get('barcode') == '':
            barcode = False
        else:
            barcode = values.get('barcode')	

        vals = {
                  'name':values.get('name'),
                  'default_code':values.get('default_code'),
                  'categ_id':categ_id[0].id,
                  'type':categ_type,
                  'barcode':barcode,
                  'uom_id':uom_id,
                  'uom_po_id':uom_po_id,
                  'lst_price':values.get('sale_price'),
                  'standard_price':values.get('cost_price'),
                  'weight':values.get('weight'),
                  'volume':values.get('volume'),
              }
        res = product_obj.create(vals)
        return res

    
    def import_product(self):
        
        if not self.file:
            raise ValidationError(_('Please select the file.'))
        
        if self.import_option == 'csv': 
            if self.file:
                file_name = str(self.file_name)
                extension = file_name.split('.')[1]
            if extension not in ['csv','CSV']:
                raise ValidationError(_('Please upload only csv file.!'))
            keys = ['name','default_code','categ_id','type','barcode','uom_id','uom_po_id','sale_price','cost_price','weight','volume']
            csv_data = base64.b64decode(self.file)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            data_file.seek(0)
            file_reader = []
            res = {}
            csv_reader = csv.reader(data_file, delimiter=',')
            
            try:
                file_reader.extend(csv_reader)
            except Exception:
                raise ValidationError(_("Invalid file!"))
            values = {}
            for i in range(len(file_reader)):
                field = map(str, file_reader[i])
                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                        values.update({'option':self.import_option})
                        if self.product_option == 'create':
                            res = self.create_product(values)
                        else:
                            product_obj = self.env['product.product']
                            product_categ_obj = self.env['product.category']
                            product_uom_obj = self.env['uom.uom']
                            categ_id = False
                            categ_type = False
                            barcode = False
                            uom_id = False
                            uom_po_id = False
                            if values.get('categ_id')=='':
                                pass
                            else:
                                categ_id = product_categ_obj.search([('name','=',values.get('categ_id'))])
                                if not categ_id:
                                    raise ValidationError('CATEGORY field can not be empty')

                            if values.get('type')=='':
                                pass
                            else:
                                if values.get('type') == 'Consumable':
                                    categ_type ='consu'
                                elif values.get('type') == 'Service':
                                    categ_type ='service'
                                elif values.get('type') == 'Stockable Product':
                                    categ_type ='product'
                                else:
                                    categ_type = 'product'
                            
                            if values.get('barcode') == '':
                                pass
                            else:
                                barcode = values.get('barcode')

                            if values.get('uom_id')=='':
                                pass
                            else:
                                uom_search_id  = product_uom_obj.search([('name','=',values.get('uom_id'))])
                                if not uom_search_id:
                                    raise ValidationError(_('UOM field can not be empty'))
                                else:
                                    uom_id = uom_search_id.id
                            
                            if values.get('uom_po_id')=='':
                                pass
                            else:
                                uom_po_search_id  = product_uom_obj.search([('name','=',values.get('uom_po_id'))])
                                if not uom_po_search_id:
                                    raise ValidationError(_('Purchase UOM field can not be empty'))
                                else:
                                    uom_po_id = uom_po_search_id.id
                             
                                
                            if self.product_search == 'by_code':
                                product_ids = self.env['product.product'].search([('default_code','=', values.get('default_code'))])
                                if product_ids:
                                    if categ_id != False:
                                        product_ids.write({'categ_id': categ_id[0].id or False})
                                    if categ_type != False:
                                        product_ids.write({'type': categ_type or False})
                                    if barcode != False:
                                        product_ids.write({'barcode': barcode or False})
                                    if uom_id != False:
                                        product_ids.write({'uom_id': uom_id or False})
                                    if uom_po_id != False:
                                        product_ids.write({'uom_po_id': uom_po_id})
                                    if values.get('sale_price'):
                                        product_ids.write({'lst_price': values.get('sale_price') or False})
                                    if values.get('cost_price'):
                                        product_ids.write({'standard_price': values.get('cost_price') or False})
                                    if values.get('weight'):
                                        product_ids.write({'weight': values.get('weight') or False})
                                    if values.get('volume'):
                                        product_ids.write({'volume': values.get('volume') or False})
                                else:
                                    raise Warning(_('"%s" Product not found.') % values.get('default_code')) 
                            elif self.product_search == 'by_name':
                                product_ids = self.env['product.product'].search([('name','=', values.get('name'))])
                                if product_ids:
                                    if categ_id != False:
                                        product_ids.write({'categ_id': categ_id[0].id or False})
                                    if categ_type != False:
                                        product_ids.write({'type': categ_type or False})
                                    if barcode != False:
                                        product_ids.write({'barcode': barcode or False})
                                    if uom_id != False:
                                        product_ids.write({'uom_id': uom_id or False})
                                    if uom_po_id != False:
                                        product_ids.write({'uom_po_id': uom_po_id})
                                    if values.get('sale_price'):
                                        product_ids.write({'lst_price': values.get('sale_price') or False})
                                    if values.get('cost_price'):
                                        product_ids.write({'standard_price': values.get('cost_price') or False})
                                    if values.get('weight'):
                                        product_ids.write({'weight': values.get('weight') or False})
                                    if values.get('volume'):
                                        product_ids.write({'volume': values.get('volume') or False})
                                else:
                                    raise ValidationError(_('%s product not found.') % values.get('name'))  
                            else:
                                product_ids = self.env['product.product'].search([('barcode','=', values.get('barcode'))])
                                if product_ids:
                                    if categ_id != False:
                                        product_ids.write({'categ_id': categ_id[0].id or False})
                                    if categ_type != False:
                                        product_ids.write({'type': categ_type or False})
                                    if uom_id != False:
                                        product_ids.write({'uom_id': uom_id or False})
                                    if uom_po_id != False:
                                        product_ids.write({'uom_po_id': uom_po_id})
                                    if values.get('sale_price'):
                                        product_ids.write({'lst_price': values.get('sale_price') or False})
                                    if values.get('cost_price'):
                                        product_ids.write({'standard_price': values.get('cost_price') or False})
                                    if values.get('weight'):
                                        product_ids.write({'weight': values.get('weight') or False})
                                    if values.get('volume'):
                                        product_ids.write({'volume': values.get('volume') or False})
                                else:
                                    raise ValidationError(_('%s product not found.') % values.get('barcode')) 
        else:
            if self.file:
                file_name = str(self.file_name)
                extension = file_name.split('.')[1]
            if extension not in ['xls','xlsx','XLS','XLSX']:
                raise ValidationError(_('Please upload only xls file.!'))
            fp = tempfile.NamedTemporaryFile(delete=False,suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            values = {}
            res = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    if self.product_option == 'create':
                        values.update( {'name':line[0],
                                        'default_code': line[1],
                                        'categ_id': line[2],
                                        'type': line[3],
                                        'barcode': line[4],
                                        'uom_id': line[5],
                                        'uom_po_id': line[6],
                                        'sale_price': line[7],
                                        'cost_price': line[8],
                                        'weight': line[9],
                                        'volume': line[10],
                                        
                                        })
                        res = self.create_product(values)
                    else:
                        product_obj = self.env['product.product']
                        product_categ_obj = self.env['product.category']
                        product_uom_obj = self.env['uom.uom']
                        categ_id = False
                        categ_type = False
                        barcode = False
                        uom_id = False
                        uom_po_id = False
                        if line[2]=='':
                            pass
                        else:
                            categ_id = product_categ_obj.search([('name','=',line[2])])
                            if not categ_id:
                                raise ValidationError(_('CATEGORY field can not be empty'))
                        if line[3]=='':
                            pass
                        else:
                            if line[3] == 'Consumable':
                                categ_type ='consu'
                            elif line[3] == 'Service':
                                categ_type ='service'
                            elif line[3] == 'Stockable Product':
                                categ_type ='product'
                            else:
                                categ_type = 'product'
                                
                        if line[4]=='':                             
                            pass
                        else:
                            barcode = line[4]
                        
                        if line[5]=='':
                            pass
                        else:
                            uom_search_id  = product_uom_obj.search([('name','=',line[5])])
                            if not uom_search_id:
                                raise ValidationError(_('UOM field can not be empty'))
                            else:
                                uom_id = uom_search_id.id
                        
                        if line[6]=='':
                            pass
                        else:
                            uom_po_search_id  = product_uom_obj.search([('name','=',line[6])])
                            if not uom_po_search_id:
                                raise ValidationError(_('Purchase UOM field can not be empty'))
                            else:
                                uom_po_id = uom_po_search_id.id
                            
                        if self.product_search == 'by_code':
                            product_ids = self.env['product.product'].search([('default_code','=', line[1])])
                            if product_ids:
                                if categ_id != False:
                                    product_ids.write({'categ_id': categ_id[0].id or False})
                                if categ_type != False:
                                    product_ids.write({'type': categ_type or False})
                                if barcode != False:
                                    product_ids.write({'barcode': barcode or False})
                                if uom_id != False:
                                    product_ids.write({'uom_id': uom_id or False})
                                if uom_po_id != False:
                                    product_ids.write({'uom_po_id': uom_po_id})
                                if line[7]:
                                    product_ids.write({'lst_price': line[7] or False})
                                if line[8]:
                                    product_ids.write({'standard_price': line[8] or False})
                                if line[9]:
                                    product_ids.write({'weight': line[9] or False})
                                if line[10]:
                                    product_ids.write({'volume': line[10] or False})
                            else:
                                raise ValidationError(_('"%s" Product not found.') % line[1]) 
                        elif self.product_search == 'by_name':
                            product_ids = self.env['product.product'].search([('name','=', line[0])])
                            if product_ids:
                                if categ_id != False:
                                    product_ids.write({'categ_id': categ_id[0].id or False})
                                if categ_type != False:
                                    product_ids.write({'type': categ_type or False})
                                if barcode != False:
                                    product_ids.write({'barcode': barcode or False})
                                if uom_id != False:
                                    product_ids.write({'uom_id': uom_id or False})
                                if uom_po_id != False:
                                    product_ids.write({'uom_po_id': uom_po_id})
                                if line[7]:
                                    product_ids.write({'lst_price': line[7] or False})
                                if line[8]:
                                    product_ids.write({'standard_price': line[8] or False})
                                if line[9]:
                                    product_ids.write({'weight': line[9] or False})
                                if line[10]:
                                    product_ids.write({'volume': line[10] or False})
                            else:
                                raise ValidationError(_('%s product not found.') % line[0])  
                        else:
                            product_ids = self.env['product.product'].search([('barcode','=', line[4])])
                            if product_ids:
                                if categ_id != False:
                                    product_ids.write({'categ_id': categ_id[0].id or False})
                                if categ_type != False:
                                    product_ids.write({'type': categ_type or False})
                                if uom_id != False:
                                    product_ids.write({'uom_id': uom_id or False})
                                if uom_po_id != False:
                                    product_ids.write({'uom_po_id': uom_po_id})
                                if line[7]:
                                    product_ids.write({'lst_price': line[7] or False})
                                if line[8]:
                                    product_ids.write({'standard_price': line[8] or False})
                                if line[9]:
                                    product_ids.write({'weight': line[9] or False})
                                if line[10]:
                                    product_ids.write({'volume': line[10] or False})
                            else:
                                raise ValidationError(_('%s product not found.') % line[4])  
        return res

