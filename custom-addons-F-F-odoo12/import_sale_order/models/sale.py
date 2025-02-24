# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import logging
import time
import tempfile
import binascii
import xlrd
import io
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from odoo.exceptions import Warning, ValidationError
from odoo import models, fields, exceptions, api, _

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

class sale_order(models.Model):
	_inherit = 'sale.order'

	custom_seq = fields.Boolean('Custom Sequence')
	system_seq = fields.Boolean('System Sequence')
	sale_name = fields.Char('Sale Name')


class gen_sale(models.TransientModel):
	_name = "gen.sale"

	file = fields.Binary('File')
	sequence_opt = fields.Selection([('custom', 'Use Excel/CSV Sequence Number'), ('system', 'Use System Default Sequence Number')], string='Sequence Option',default='custom')
	import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')
	stage = fields.Selection([('draft','Import Draft Quotation'),('confirm','Confirm Quotation Automatically With Import')], string="Quotation Stage Option",default='draft')
	import_prod_option = fields.Selection([('name', 'Name'),('code', 'Code'),('barcode', 'Barcode')],string='Import Product By ',default='name')

	sample_option = fields.Selection([('csv', 'CSV'),('xls', 'XLS')],string='Sample Type',default='csv')
	down_samp_file = fields.Boolean(string='Download Sample Files')


	def make_sale(self, values):
		sale_id=self.env["sale.order.type"].search([('name','=','Rental Order'),("company_id", "in", [self.env.user.company_id.id, False])], limit=1)
		sale_obj = self.env['sale.order']
		if self.sequence_opt == "custom":
			sale_search = sale_obj.search([
				('name', '=', values.get('order'))
			])
		else:
			sale_search = sale_obj.search([
				('sale_name', '=', values.get('order'))
			])
		if sale_search:
			sale_search = sale_search[0]

			if sale_search.partner_id.name == values.get('customer'):
				if  sale_search.pricelist_id.name == values.get('pricelist'):
					if sale_search.client_order_ref == values.get('customer_ref'):
						lines = self.make_order_line(values, sale_search)
						return sale_search
					else:
						raise ValidationError(_('Customer Reference is different for "%s" .\n Please define same.') % values.get('customer_ref'))
				else:
					raise ValidationError(_('Pricelist is different for "%s" .\n Please define same.') % values.get('order'))
			else:
				raise ValidationError(_('Customer name is different for "%s" .\n Please define same.') % values.get('order'))
		else:
			if values.get('seq_opt') == 'system':
				name = self.env['ir.sequence'].next_by_code('sale.order')
			elif values.get('seq_opt') == 'custom':
				name = values.get('order')
			else:
				name = ''
			partner_id = self.find_partner(values.get('customer'))
			currency_id = self.find_currency(values.get('pricelist'))
			user_id  = self.find_user(values.get('user'))
			if values.get('date') == '':
				raise ValidationError(_('Please assign a order date'))
			else:
				order_date = self.make_order_date(values.get('date'))
			if values.get('commitment_date') == '':
				raise ValidationError(_('Please assign a delivery date'))
			else:
				delivery_date = self.make_order_date(values.get('commitment_date'))

			sale_id = sale_obj.create({
				'partner_id' : partner_id.id,
				'pricelist_id' : currency_id.id,
				'name':name,
				'user_id': user_id.id,
				'date_order':order_date,
				'client_order_ref':values.get('customer_ref'),
				'commitment_date':delivery_date,
				'custom_seq': True if values.get('seq_opt') == 'custom' else False,
				'system_seq': True if values.get('seq_opt') == 'system' else False,
				'sale_name' : values.get('order'),
				'type_id': 2, #Rental Order
			})
			lines = self.make_order_line(values, sale_id)
			return sale_id


	def make_order_line(self, values, sale_id):
		product_obj = self.env['product.product']
		order_line_obj = self.env['sale.order.line']
		current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')

		if self.import_prod_option == 'barcode':
			prefix = values['product'].startswith('0')
			if prefix:
				product_search = product_obj.search([('barcode', '=', values['product'])])
			else:
				res = values['product'].replace('.', '', 1).isdigit()
				if res == True:
					product_search = product_obj.search([('barcode','=',int(float(values['product'])))])
				else:
					product_search = product_obj.search([('barcode', '=', values['product'])])

		elif self.import_prod_option == 'code':
			product_search = product_obj.search([('default_code', '=',values['product'])])
		else:
			product_search = product_obj.search([('name', '=',values['product'])])

		product_uom = self.env['uom.uom'].search([('name', '=', values.get('uom'))])
		if product_uom.id == False:
			raise ValidationError(_(' "%s" Product UOM category is not available.') % values.get('uom'))

		if product_search:
			product_id = product_search[0]
		else:
			if self.import_prod_option == 'name':
				product_id = product_obj.create({
													'name':values.get('product'),
													'lst_price':values.get('price'),
													'uom_id':product_uom.id,
													'uom_po_id':product_uom.id
												 })
			else:
				raise ValidationError(_('"%s" product is not found .\n If you want to create product then first select Import Product By Name option .') % values.get('product'))

		tax_ids = []
		if values.get('tax'):
			if ';' in  values.get('tax'):
				tax_names = values.get('tax').split(';')
				for name in tax_names:
					tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')])
					if not tax:
						raise ValidationError(_('"%s" Tax not in your system') % name)
					tax_ids.append(tax.id)

			elif ',' in  values.get('tax'):
				tax_names = values.get('tax').split(',')
				for name in tax_names:
					tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')])
					if not tax:
						raise ValidationError(_('"%s" Tax not in your system') % name)
					tax_ids.append(tax.id)
			else:
				tax_names = values.get('tax').split(',')
				for name in tax_names:
					tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'sale')])
					if not tax:
						raise ValidationError(_('"%s" Tax not in your system') % name)
					tax_ids.append(tax.id)

		print({
											'order_id':sale_id.id,
											'product_id':product_id.product_rental_day_id.id,
											'name':values.get('description'),
											'product_uom_qty':values.get('quantity'),
											'rental_qty':values.get('quantity'),
											'product_uom':product_uom.id,
											'price_unit':values.get('price'),
											'discount':values.get('discount'),
											'product_template_id':product_id.product_tmpl_id.id,
											'display_product_id':product_id.id,
											'rental':True,
											'rental_type':'new_rental',
											'start_date':values.get('start_date'),
											'end_date':values.get('end_date'),
											})

		so_order_lines = order_line_obj.create({
											'order_id':sale_id.id,
											#'product_id':product_id.id,
											'product_id':product_id.product_rental_day_id.id,
											'name':values.get('description'),
											'product_uom_qty':values.get('quantity'),
											'rental_qty':values.get('quantity'),
											'product_uom':product_uom.id,
											'price_unit':values.get('price'),
											'discount':values.get('discount'),
											'product_template_id':product_id.product_tmpl_id.id,
											'display_product_id':product_id.id,
											'rental':True,
											'rental_type':'new_rental',
											'start_date':values.get('start_date'),
											'end_date':values.get('end_date'),
											})
		if tax_ids:
			so_order_lines.write({'tax_id':([(6,0,tax_ids)])})
		return True


	def make_order_date(self, date):
		DATETIME_FORMAT = "%Y-%m-%d"
		try:
			i_date = datetime.strptime(date, DATETIME_FORMAT)
			return i_date
		except Exception:
			raise ValidationError(_('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))


	def find_user(self, name):
		user_obj = self.env['res.users']
		user_search = user_obj.search([('name', '=', name)])
		if user_search:
			return user_search
		else:
			raise ValidationError(_(' "%s" User is not available.') % name)


	def find_currency(self, name):
		currency_obj = self.env['product.pricelist']
		currency_search = currency_obj.search([('name', '=', name)])
		if currency_search:
			return currency_search
		else:
			raise ValidationError(_(' "%s" Pricelist are not available.') % name)

	def find_partner(self, name):
		partner_obj = self.env['res.partner']
		partner_search = partner_obj.search([('name', '=', name)])
		if partner_search:
			return partner_search
		else:
			partner_id = partner_obj.create({
				'name' : name})
			return partner_id

	def import_sale(self):

		confirmed_list = []
		canceled_list = []


		"""Load Inventory data from the CSV file."""
		if self.import_option == 'csv':
			keys = ['order', 'customer', 'pricelist','product', 'quantity', 'uom', 'description', 'price','user','tax','date','discount','customer_ref','commitment_date']
			try:
				csv_data = base64.b64decode(self.file)
				data_file = io.StringIO(csv_data.decode("utf-8"))
				data_file.seek(0)
				file_reader = []
				sale_ids = []
				csv_reader = csv.reader(data_file, delimiter=',')
				file_reader.extend(csv_reader)
			except Exception:
				raise exceptions.ValidationError(_("Invalid file!"))
			values = {}
			for i in range(len(file_reader)):
				#                val = {}
				field = list(map(str, file_reader[i]))
				values = dict(zip(keys, field))
				if values:
					if i == 0:
						continue
					else:
						values.update({'option':self.import_option,'seq_opt':self.sequence_opt})
						res = self.make_sale(values)
						sale_ids.append(res)

			confirmed_string = ''
			canceled_string = ''
			for rec in sale_ids:
				if rec.state == 'sale':
					if rec.name not in confirmed_list:
						if len(confirmed_list) == 0:
							confirmed_string+= rec.name
						else:
							confirmed_string+= ','+rec.name
						confirmed_list.append(rec.name)
				elif rec.state == 'cancel':
					if rec.name not in canceled_list:
						if len(canceled_list) == 0:
							canceled_string+= rec.name
						else:
							canceled_string+= ','+rec.name
						canceled_list.append(rec.name)

			if len(confirmed_list) > 0 and len(canceled_list) > 0 :
				raise ValidationError(_('Only draft sale orders can be imported. Sale orders %s are in confirmed state and %s are in canceled state in the system.') % (confirmed_string,canceled_string))

			elif len(confirmed_list) > 0 and len(canceled_list) == 0 :
				raise ValidationError(_('Only draft sale orders can be imported. Sale orders %s are in confirmed state in the system.') % confirmed_string)

			elif len(confirmed_list) == 0 and len(canceled_list) > 0 :
				raise ValidationError(_('Only draft sale orders can be imported. Sale orders %s are in canceled state in the system.') % canceled_string)

			if self.stage == 'confirm':
				for res in sale_ids:
					if res.state in ['draft', 'sent']:
						res.action_confirm()

		else:
			try:
				fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
				fp.write(binascii.a2b_base64(self.file))
				fp.seek(0)
				values = {}
				sale_ids = []
				workbook = xlrd.open_workbook(fp.name)
				sheet = workbook.sheet_by_index(0)
			except Exception:
				raise exceptions.ValidationError(_("Invalid file!"))

			for row_no in range(sheet.nrows):
				val = {}
				if row_no <= 0:
					fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
				else:
					line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
					print(line,"========================dfdfdfdfdf")
					if line[10] == '':
						raise ValidationError(_('Please assign a order date'))
					else:
						if line[10] != '':
							if line[10].split('/'):
								if len(line[10].split('/')) > 1:
									raise ValidationError(_('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))
								if len(line[10]) > 8 or len(line[10]) < 5:
									raise ValidationError(_('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))
						a1 = int(float(line[10]))
						a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
						date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
						#############inicio
						if len(line) > 14:
							inicio = int(float(line[14]))
							inicio_as_datetime = datetime(*xlrd.xldate_as_tuple(inicio, workbook.datemode))
							date_string_inicio = inicio_as_datetime.date().strftime('%Y-%m-%d')
							values.update({'start_date': date_string_inicio})
						###################Finañ
						if len(line) > 15:
							fin = int(float(line[15]))
							fin_as_datetime = datetime(*xlrd.xldate_as_tuple(fin, workbook.datemode))
							date_string_fin = fin_as_datetime.date().strftime('%Y-%m-%d')
							values.update({'end_date': date_string_fin})
					if line[13] == '':
						raise ValidationError(_('Please assign a delivery date'))
					else:
						if line[13] != '':
							if line[13].split('/'):
								if len(line[13].split('/')) > 1:
									raise ValidationError(_('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))
								if len(line[13]) > 8 or len(line[13]) < 5:
									raise ValidationError(_('Wrong Date Format. Date Should be in format YYYY-MM-DD.'))

						a2 = int(float(line[13]))
						a2_as_datetime = datetime(*xlrd.xldate_as_tuple(a2, workbook.datemode))
						date_string2 = a2_as_datetime.date().strftime('%Y-%m-%d')
					values.update( {'order':line[0],
									'customer': line[1],
									'pricelist': line[2],
									'product': line[3],
									'quantity': line[4],
									'uom': line[5],
									'description': line[6],
									'price': line[7],
									'user': line[8],
									'tax': line[9],
									'discount':line[11],
									'customer_ref':line[12],
									'date':date_string,
									'commitment_date':date_string2,
									'seq_opt':self.sequence_opt,
									'rental':True,
									'rental_type':'new_rental',
									})

					res = self.make_sale(values)
					sale_ids.append(res)

			confirmed_string = ''
			canceled_string = ''
			for rec in sale_ids:
				if rec.state == 'sale':
					if rec.name not in confirmed_list:
						if len(confirmed_list) == 0:
							confirmed_string+= rec.name
						else:
							confirmed_string+= ','+rec.name
						confirmed_list.append(rec.name)
				elif rec.state == 'cancel':
					if rec.name not in canceled_list:
						if len(canceled_list) == 0:
							canceled_string+= rec.name
						else:
							canceled_string+= ','+rec.name
						canceled_list.append(rec.name)

			if len(confirmed_list) > 0 and len(canceled_list) > 0 :
				raise ValidationError(_('Only draft sale orders can be imported. Sale orders %s are in confirmed state and %s are in canceled state in the system.') % (confirmed_string,canceled_string))

			elif len(confirmed_list) > 0 and len(canceled_list) == 0 :
				raise ValidationError(_('Only draft sale orders can be imported. Sale orders %s are in confirmed state in the system.') % confirmed_string)

			elif len(confirmed_list) == 0 and len(canceled_list) > 0 :
				raise ValidationError(_('Only draft sale orders can be imported. Sale orders %s are in canceled state in the system.') % canceled_string)

			if self.stage == 'confirm':
				for res in sale_ids:
					if res.state in ['draft', 'sent']:
						res.action_confirm()


		return res


	def download_auto(self):
		return {
             'type' : 'ir.actions.act_url',
             'url': '/web/binary/download_document?model=gen.sale&id=%s'%(self.id),
             'target': 'new',
             }

