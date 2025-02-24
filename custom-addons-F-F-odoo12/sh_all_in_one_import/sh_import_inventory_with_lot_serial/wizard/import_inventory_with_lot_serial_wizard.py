# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import csv
import base64
import xlrd
from odoo.tools import ustr


class ImportInventoryWithLotSerialWizard(models.TransientModel):
    _name = "import.inventory.with.lot.serial.wizard"
    _description = "Import Inventory With lot or serial number wizard"

    @api.model
    def _default_location_id(self):
        company_user = self.env.company
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        else:
            raise UserError(
                _('You must define a warehouse for the company: %s.') % (company_user.name,))

    import_type = fields.Selection([
        ('csv', 'CSV File'),
        ('excel', 'Excel File')
    ], default="csv", string="Import File Type", required=True)
    file = fields.Binary(string="File", required=True)

    product_by = fields.Selection([
        ('name', 'Name'),
        ('int_ref', 'Internal Reference'),
        ('barcode', 'Barcode')
    ], default="name", string="Product By", required=True)

    location_id = fields.Many2one("stock.location", string="Location",
                                  domain="[('usage','not in', ['supplier','production'])]", required=True, default=_default_location_id)
    name = fields.Char(string="Inventory Reference", required=True)

    is_create_lot = fields.Boolean(
        string="Create Lot/Serial Number if never exist?")

    def show_success_msg(self, counter, skipped_line_no):
        #open the new success message box
        view = self.env.ref('sh_message.sh_message_wizard')
        context = dict(self._context or {})
        dic_msg = str(counter) + " Records imported successfully"
        if skipped_line_no:
            dic_msg = dic_msg + "\nNote:"
        for k, v in skipped_line_no.items():
            dic_msg = dic_msg + "\nRow No " + k + " " + v + " "
        context['message'] = dic_msg

        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }

    def import_inventory_with_lot_serial_apply(self):
        stock_inventory_obj = self.env['stock.inventory']
        stock_inventory_line_obj = self.env['stock.inventory.line']
        stock_production_lot_obj = self.env['stock.production.lot']
        #perform import lead
        if self and self.file and self.location_id and self.name:
            #For CSV
            if self.import_type == 'csv':
                counter = 1
                skipped_line_no = {}
                try:
                    file = str(base64.decodebytes(self.file).decode('utf-8'))
                    myreader = csv.reader(file.splitlines())
                    skip_header = True
                    created_inventory = False
                    inventory_vals = {
                        'name': self.name,
                    }
                    created_inventory = stock_inventory_obj.create(
                        inventory_vals)
                    if created_inventory:
                        created_inventory.action_start()

                    for row in myreader:
                        try:
                            if skip_header:
                                skip_header = False
                                counter = counter + 1
                                continue

                            if row[0] not in (None, ""):
                                vals = {}

                                field_nm = 'name'
                                if self.product_by == 'name':
                                    field_nm = 'name'
                                elif self.product_by == 'int_ref':
                                    field_nm = 'default_code'
                                elif self.product_by == 'barcode':
                                    field_nm = 'barcode'

                                search_product = self.env['product.product'].search(
                                    [(field_nm, '=', row[0])], limit=1)
                                if search_product and search_product.type == 'product' and search_product.tracking in ['serial', 'lot']:
                                    vals.update(
                                        {'product_id': search_product.id})

                                    if row[1] not in (None, ""):
                                        vals.update({'product_qty': row[1]})
                                    else:
                                        vals.update({'product_qty': 0.0})

                                    if row[2].strip() not in (None, ""):
                                        search_uom = self.env['uom.uom'].search(
                                            [('name', '=', row[2].strip())], limit=1)
                                        if search_uom:
                                            vals.update(
                                                {'product_uom_id': search_uom.id})
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Unit of Measure not found. "
                                            counter = counter + 1
                                            continue
                                    elif search_product.uom_id:
                                        vals.update(
                                            {'product_uom_id': search_product.uom_id.id})
                                    else:
                                        skipped_line_no[str(
                                            counter)] = " - Unit of Measure not defined for this product. "
                                        counter = counter + 1
                                        continue

                                    if row[3] not in (None, ""):
                                        search_lot = stock_production_lot_obj.search([
                                            ('name', '=', row[3]),
                                            ('product_id', '=',
                                             search_product.id)
                                        ], limit=1)
                                        if search_lot:
                                            vals.update(
                                                {'prod_lot_id': search_lot.id})
                                        elif self.is_create_lot:
                                            created_lot = stock_production_lot_obj.create({
                                                'name': row[3],
                                                'product_id': search_product.id,
                                                'company_id': self.env.company.id
                                            })
                                            if created_lot:
                                                vals.update(
                                                    {'prod_lot_id': created_lot.id})
                                            else:
                                                skipped_line_no[str(
                                                    counter)] = " - Lot/Serial Number could not be created for this product. "
                                                counter = counter + 1
                                                continue
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Lot/Serial Number not found. "
                                            counter = counter + 1
                                            continue

                                    #check if stock move line exist or not
                                    if created_inventory:
                                        related_stock_inv_line = stock_inventory_line_obj.sudo().search([('prod_lot_id', '=', vals.get('prod_lot_id')), (
                                            'product_id', '=', search_product.id), ('location_id', '=', self.location_id.id), ('inventory_id', '=', created_inventory.id)])
                                        if related_stock_inv_line:
                                            related_stock_inv_line.write(
                                                {'product_qty': vals.get('product_qty')})
                                        else:
                                            vals.update(
                                                {'location_id': self.location_id.id})
                                            vals.update(
                                                {'inventory_id': created_inventory.id})
                                            stock_inventory_line_obj.create(
                                                vals)
                                    else:
                                        skipped_line_no[str(
                                            counter)] = " - Inventory could not be created. "
                                        counter = counter + 1
                                        continue

                                    counter = counter + 1
                                else:
                                    skipped_line_no[str(
                                        counter)] = " - Product not found or it's not a Stockable Product or it's not traceable by lot/serial number. "
                                    counter = counter + 1
                                    continue
                            else:
                                skipped_line_no[str(
                                    counter)] = " - Product is empty. "
                                counter = counter + 1

                        except Exception as e:
                            skipped_line_no[str(
                                counter)] = " - Value is not valid " + ustr(e)
                            counter = counter + 1
                            continue

                    if created_inventory:
                        created_inventory.action_validate()

                except Exception as e:
                    raise UserError(
                        _("Sorry, Your csv file does not match with our format " + ustr(e)))

                if counter > 1:
                    completed_records = (counter - len(skipped_line_no)) - 2
                    res = self.show_success_msg(
                        completed_records, skipped_line_no)
                    return res

            #For Excel
            if self.import_type == 'excel':
                counter = 1
                skipped_line_no = {}
                try:
                    wb = xlrd.open_workbook(
                        file_contents=base64.decodebytes(self.file))
                    sheet = wb.sheet_by_index(0)
                    skip_header = True
                    created_inventory = False
                    inventory_vals = {
                        'name': self.name,
                    }
                    created_inventory = stock_inventory_obj.create(
                        inventory_vals)
                    if created_inventory:
                        created_inventory.action_start()

                    for row in range(sheet.nrows):
                        try:
                            if skip_header:
                                skip_header = False
                                counter = counter + 1
                                continue

                            if sheet.cell(row, 0).value not in (None, ""):
                                vals = {}

                                field_nm = 'name'
                                if self.product_by == 'name':
                                    field_nm = 'name'
                                elif self.product_by == 'int_ref':
                                    field_nm = 'default_code'
                                elif self.product_by == 'barcode':
                                    field_nm = 'barcode'

                                search_product = self.env['product.product'].search(
                                    [(field_nm, '=', sheet.cell(row, 0).value)], limit=1)
                                if search_product and search_product.type == 'product' and search_product.tracking in ['serial', 'lot']:
                                    vals.update(
                                        {'product_id': search_product.id})

                                    if sheet.cell(row, 1).value not in (None, ""):
                                        vals.update(
                                            {'product_qty': sheet.cell(row, 1).value})
                                    else:
                                        vals.update({'product_qty': 0.0})

                                    if sheet.cell(row, 2).value.strip() not in (None, ""):
                                        search_uom = self.env['uom.uom'].search(
                                            [('name', '=', sheet.cell(row, 2).value.strip())], limit=1)
                                        if search_uom:
                                            vals.update(
                                                {'product_uom_id': search_uom.id})
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Unit of Measure not found. "
                                            counter = counter + 1
                                            continue
                                    elif search_product.uom_id:
                                        vals.update(
                                            {'product_uom_id': search_product.uom_id.id})
                                    else:
                                        skipped_line_no[str(
                                            counter)] = " - Unit of Measure not defined for this product. "
                                        counter = counter + 1
                                        continue

                                    if sheet.cell(row, 3).value not in (None, ""):
                                        search_lot = stock_production_lot_obj.search([
                                            ('name', '=', sheet.cell(row, 3).value),
                                            ('product_id', '=',
                                             search_product.id)
                                        ], limit=1)
                                        if search_lot:
                                            vals.update(
                                                {'prod_lot_id': search_lot.id})
                                        elif self.is_create_lot:
                                            created_lot = stock_production_lot_obj.create({
                                                'name': sheet.cell(row, 3).value,
                                                'product_id': search_product.id,
                                                'company_id': self.env.company.id
                                            })
                                            if created_lot:
                                                vals.update(
                                                    {'prod_lot_id': created_lot.id})
                                            else:
                                                skipped_line_no[str(
                                                    counter)] = " - Lot/Serial Number could not be created for this product. "
                                                counter = counter + 1
                                                continue
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Lot/Serial Number not found. "
                                            counter = counter + 1
                                            continue

                                    #check if stock move line exist or not
                                    if created_inventory:
                                        related_stock_inv_line = stock_inventory_line_obj.sudo().search([('prod_lot_id', '=', vals.get('prod_lot_id')), (
                                            'product_id', '=', search_product.id), ('location_id', '=', self.location_id.id), ('inventory_id', '=', created_inventory.id)])
                                        if related_stock_inv_line:
                                            related_stock_inv_line.write(
                                                {'product_qty': vals.get('product_qty')})
                                        else:
                                            vals.update(
                                                {'location_id': self.location_id.id})
                                            vals.update(
                                                {'inventory_id': created_inventory.id})
                                            stock_inventory_line_obj.create(
                                                vals)
                                    else:
                                        skipped_line_no[str(
                                            counter)] = " - Inventory could not be created. "
                                        counter = counter + 1
                                        continue

                                    counter = counter + 1
                                else:
                                    skipped_line_no[str(
                                        counter)] = " - Product not found or it's not a Stockable Product or it's not traceable by lot/serial number. "
                                    counter = counter + 1
                                    continue
                            else:
                                skipped_line_no[str(
                                    counter)] = " - Product is empty. "
                                counter = counter + 1

                        except Exception as e:
                            skipped_line_no[str(
                                counter)] = " - Value is not valid " + ustr(e)
                            counter = counter + 1
                            continue

                    if created_inventory:
                        created_inventory.action_validate()

                except Exception as e:
                    raise UserError(
                        _("Sorry, Your excel file does not match with our format " + ustr(e)))

                if counter > 1:
                    completed_records = (counter - len(skipped_line_no)) - 2
                    res = self.show_success_msg(
                        completed_records, skipped_line_no)
                    return res
