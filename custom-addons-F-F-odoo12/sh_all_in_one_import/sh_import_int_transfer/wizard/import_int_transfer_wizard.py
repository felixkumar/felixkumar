# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime
import csv
import base64
import xlrd
from odoo.tools import ustr


class ImportIntTransferWizard(models.TransientModel):
    _name = "import.int.transfer.wizard"
    _description = "Import Internal Transfer Wizard"

    @api.model
    def _default_schedule_date(self):
        return datetime.datetime.now()

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

    scheduled_date = fields.Datetime(
        string="Scheduled Date", default=_default_schedule_date, required=True)
    location_id = fields.Many2one(
        'stock.location', "Source Location",
        required=True,
        default=_default_location_id)

    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        required=True,
        default=_default_location_id)

    product_by = fields.Selection([
        ('name', 'Name'),
        ('int_ref', 'Internal Reference'),
        ('barcode', 'Barcode')
    ], default="name", string="Product By", required=True)

    file = fields.Binary(string="File", required=True)

    import_type = fields.Selection([
        ('csv', 'CSV File'),
        ('excel', 'Excel File')
    ], default="csv", string="Import File Type", required=True)

    def show_success_msg(self, counter, skipped_line_no):
        # open the new success message box
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

    def import_int_transfer_apply(self):
        stock_picking_obj = self.env['stock.picking']
        stock_move_obj = self.env['stock.move']
        # perform import lead
        if self and self.file and self.location_id and self.location_dest_id and self.scheduled_date:
            # For CSV
            if self.import_type == 'csv':
                counter = 1
                skipped_line_no = {}
                try:
                    file = str(base64.decodebytes(self.file).decode('utf-8'))
                    myreader = csv.reader(file.splitlines())
                    skip_header = True
                    created_picking = False
                    search_warehouse = False
                    search_picking_type = False
                    search_warehouse = self.env['stock.warehouse'].search([
                        ('company_id', '=', self.env.company.id)
                    ], limit=1)
                    if search_warehouse:
                        search_picking_type = self.env['stock.picking.type'].search([
                            ('code', '=', 'internal'),
                            ('warehouse_id', '=', search_warehouse.id)
                        ], limit=1)

                    picking_vals = {}
                    if search_picking_type:
                        picking_vals.update({
                            'picking_type_code': 'internal',
                            'location_id': self.location_id.id,
                            'location_dest_id': self.location_dest_id.id,
                            'scheduled_date': self.scheduled_date,
                            'picking_type_id': search_picking_type.id
                        })

                        created_picking = stock_picking_obj.create(
                            picking_vals)
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
                                if search_product and search_product.type in ['product', 'consu']:
                                    search_uom = False
                                    vals.update(
                                        {'product_id': search_product.id})
                                    vals.update({'name': search_product.name})
                                    if row[1] not in (None, ""):
                                        vals.update({'quantity_done': row[1]})
                                    else:
                                        vals.update({'quantity_done': 0.0})

                                    if row[2].strip() not in (None, ""):
                                        search_uom = self.env['uom.uom'].search(
                                            [('name', '=', row[2].strip())], limit=1)
                                        if search_uom:
                                            vals.update(
                                                {'product_uom': search_uom.id})
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Unit of Measure not found. "
                                            counter = counter + 1
                                            continue
                                    elif search_product.uom_id:
                                        vals.update(
                                            {'product_uom': search_product.uom_id.id})
                                    else:
                                        skipped_line_no[str(
                                            counter)] = " - Unit of Measure not defined for this product. "
                                        counter = counter + 1
                                        continue

                                    if created_picking:
                                        vals.update({
                                            'location_id': created_picking.location_id.id,
                                            'location_dest_id': created_picking.location_dest_id.id,
                                            'picking_id': created_picking.id,
                                            'date_deadline': created_picking.scheduled_date
                                        })
                                        created_stock_move = stock_move_obj.create(
                                            vals)
                                        if created_stock_move:
                                            created_stock_move.onchange_product_id()
                                            if search_uom:
                                                created_stock_move.write(
                                                    {'product_uom': search_uom.id})

                                    else:
                                        skipped_line_no[str(
                                            counter)] = " - Internal Transfer Could not be created. "
                                        counter = counter + 1
                                        continue

                                    counter = counter + 1
                                else:
                                    skipped_line_no[str(
                                        counter)] = " - Product not found or it's not a Stockable or Consumable Product. "
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

                except Exception as e:
                    raise UserError(
                        _("Sorry, Your csv file does not match with our format " + ustr(e)))

                if counter > 1:
                    completed_records = (counter - len(skipped_line_no)) - 2
                    res = self.show_success_msg(
                        completed_records, skipped_line_no)
                    return res

            # For Excel
            if self.import_type == 'excel':
                counter = 1
                skipped_line_no = {}
                try:
                    wb = xlrd.open_workbook(
                        file_contents=base64.decodebytes(self.file))
                    sheet = wb.sheet_by_index(0)
                    skip_header = True
                    created_picking = False
                    search_warehouse = False
                    search_picking_type = False
                    search_warehouse = self.env['stock.warehouse'].search([
                        ('company_id', '=', self.env.company.id)
                    ], limit=1)
                    if search_warehouse:
                        search_picking_type = self.env['stock.picking.type'].search([
                            ('code', '=', 'internal'),
                            ('warehouse_id', '=', search_warehouse.id)
                        ], limit=1)

                    picking_vals = {}
                    if search_picking_type:
                        picking_vals.update({
                            'picking_type_code': 'internal',
                            'location_id': self.location_id.id,
                            'location_dest_id': self.location_dest_id.id,
                            'scheduled_date': self.scheduled_date,
                            'picking_type_id': search_picking_type.id
                        })

                        created_picking = stock_picking_obj.create(
                            picking_vals)
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
                                if search_product and search_product.type in ['product', 'consu']:
                                    search_uom = False
                                    vals.update(
                                        {'product_id': search_product.id})
                                    vals.update({'name': search_product.name})
                                    if sheet.cell(row, 1).value not in (None, ""):
                                        vals.update(
                                            {'quantity_done': sheet.cell(row, 1).value})
                                    else:
                                        vals.update({'quantity_done': 0.0})

                                    if sheet.cell(row, 2).value.strip() not in (None, ""):
                                        search_uom = self.env['uom.uom'].search(
                                            [('name', '=', sheet.cell(row, 2).value.strip())], limit=1)
                                        if search_uom:
                                            vals.update(
                                                {'product_uom': search_uom.id})
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Unit of Measure not found. "
                                            counter = counter + 1
                                            continue
                                    elif search_product.uom_id:
                                        vals.update(
                                            {'product_uom': search_product.uom_id.id})
                                    else:
                                        skipped_line_no[str(
                                            counter)] = " - Unit of Measure not defined for this product. "
                                        counter = counter + 1
                                        continue

                                    if created_picking:
                                        vals.update({
                                            'location_id': created_picking.location_id.id,
                                            'location_dest_id': created_picking.location_dest_id.id,
                                            'picking_id': created_picking.id,
                                            'date_deadline': created_picking.scheduled_date
                                        })
                                        created_stock_move = stock_move_obj.create(
                                            vals)
                                        if created_stock_move:
                                            created_stock_move.onchange_product_id()
                                            if search_uom:
                                                created_stock_move.write(
                                                    {'product_uom': search_uom.id})

                                    else:
                                        skipped_line_no[str(
                                            counter)] = " - Internal Transfer Could not be created. "
                                        counter = counter + 1
                                        continue

                                    counter = counter + 1
                                else:
                                    skipped_line_no[str(
                                        counter)] = " - Product not found or it's not a Stockable or Consumable Product. "
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

                except Exception as e:
                    raise UserError(
                        _("Sorry, Your excel file does not match with our format " + ustr(e)))

                if counter > 1:
                    completed_records = (counter - len(skipped_line_no)) - 2
                    res = self.show_success_msg(
                        completed_records, skipped_line_no)
                    return res
