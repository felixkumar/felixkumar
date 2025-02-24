# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, _
from odoo.exceptions import UserError
import csv
import base64
import xlrd
from odoo.tools import ustr


class ImportBomWizard(models.TransientModel):
    _name = "import.bom.wizard"
    _description = "Import Bill of Materials Wizard"

    import_type = fields.Selection([
        ('csv', 'CSV File'),
        ('excel', 'Excel File')
    ], default="csv", string="Import File Type", required=True)
    file = fields.Binary(string="File", required=True)

    bom_type = fields.Selection([
        ('mtp', 'Manufacture this product'),
        ('kit', 'Kit')
    ], default="mtp", string="BoM Type", required=True)

    product_by = fields.Selection([
        ('name', 'Name'),
        ('int_ref', 'Internal Reference'),
        ('barcode', 'Barcode')
    ], default="name", string="Product By", required=True)

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
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }

    def import_bom_apply(self):
        bom_obj = self.env['mrp.bom']
        bom_line_obj = self.env['mrp.bom.line']
        # perform import lead
        if self and self.file:
            # For CSV
            if self.import_type == 'csv':
                for rec in self:
                    counter = 1
                    skipped_line_no = {}
                    try:
                        file = str(base64.decodebytes(
                            rec.file).decode('utf-8'))
                        myreader = csv.reader(file.splitlines())
                        skip_header = True
                        running_bom = None
                        created_bom = False
                        created_bom_list = []
                        bom_list_for_unlink = []

                        for row in myreader:
                            try:
                                if skip_header:
                                    skip_header = False
                                    counter = counter + 1
                                    continue

                                if row[0] not in (None, "") and row[5] not in (None, ""):
                                    vals = {}

                                    if row[0] != running_bom:

                                        running_bom = row[0]
                                        bom_vals = {}

                                        if row[1] not in (None, ""):

                                            field_nm = 'name'
                                            if rec.product_by == 'name':
                                                field_nm = 'name'
                                            elif rec.product_by == 'int_ref':
                                                field_nm = 'default_code'
                                            elif rec.product_by == 'barcode':
                                                field_nm = 'barcode'

                                            search_product_tmpl = self.env['product.template'].search(
                                                [(field_nm, '=', row[1])], limit=1)
                                            if search_product_tmpl and search_product_tmpl.type in ['product', 'consu']:
                                                bom_vals.update(
                                                    {'product_tmpl_id': search_product_tmpl.id})

                                                if row[2] not in (None, ""):
                                                    search_product_var = self.env['product.product'].search(
                                                        [(field_nm, '=', row[2])], limit=1)
                                                    if search_product_var and search_product_var.product_tmpl_id.id == search_product_tmpl.id and search_product_var.type in ['product', 'consu']:
                                                        bom_vals.update(
                                                            {'product_id': search_product_var.id})
                                                    else:
                                                        skipped_line_no[str(
                                                            counter)] = " - Product Variant is invalid. "
                                                        counter = counter + 1
                                                        continue
                                                if row[3] not in (None, ""):
                                                    bom_vals.update(
                                                        {'product_qty': row[3]})
                                                else:
                                                    bom_vals.update(
                                                        {'product_qty': 1})

                                                if row[4] not in (None, ""):
                                                    search_uom = self.env['uom.uom'].search(
                                                        [('name', '=', row[4])], limit=1)
                                                    if search_uom:
                                                        bom_vals.update(
                                                            {'product_uom_id': search_uom.id})
                                                    else:
                                                        skipped_line_no[str(
                                                            counter)] = " - Unit of Measure not found. "
                                                        counter = counter + 1
                                                        continue
                                                elif search_product_tmpl.uom_id:
                                                    bom_vals.update(
                                                        {'product_uom_id': search_product_tmpl.uom_id.id})
                                                else:
                                                    skipped_line_no[str(
                                                        counter)] = " - Unit of Measure not defined. "
                                                    counter = counter + 1
                                                    continue

                                                if rec.bom_type == 'mtp':
                                                    bom_vals.update(
                                                        {'type': 'normal'})
                                                else:
                                                    bom_vals.update(
                                                        {'type': 'phantom'})

                                                bom_vals.update(
                                                    {'code': row[0]})
                                                created_bom = bom_obj.create(
                                                    bom_vals)
                                                if created_bom:
                                                    created_bom_list.append(
                                                        created_bom.id)

                                            else:
                                                skipped_line_no[str(
                                                    counter)] = " - Finished Product not found or it's type is invalid. "
                                                counter = counter + 1
                                                continue

                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Finished Product field is empty. "
                                            counter = counter + 1
                                            continue

                                    if created_bom:
                                        field_nm = 'name'
                                        if rec.product_by == 'name':
                                            field_nm = 'name'
                                        elif rec.product_by == 'int_ref':
                                            field_nm = 'default_code'
                                        elif rec.product_by == 'barcode':
                                            field_nm = 'barcode'

                                        search_material_product = self.env['product.product'].search(
                                            [(field_nm, '=', row[5])], limit=1)
                                        if search_material_product:
                                            vals.update(
                                                {'product_id': search_material_product.id})

                                            if row[6] not in (None, ""):
                                                vals.update(
                                                    {'product_qty': row[6]})
                                            else:
                                                vals.update({'product_qty': 1})

                                            if row[7] not in (None, ""):
                                                search_uom = self.env['uom.uom'].search(
                                                    [('name', '=', row[7])], limit=1)
                                                if search_uom:
                                                    vals.update(
                                                        {'product_uom_id': search_uom.id})
                                                else:
                                                    skipped_line_no[str(
                                                        counter)] = " - Material product Unit of Measure not found. "
                                                    counter = counter + 1
                                                    bom_list_for_unlink.append(
                                                        created_bom.id)
                                                    continue
                                            elif search_material_product.uom_id:
                                                vals.update(
                                                    {'product_uom_id': search_material_product.uom_id.id})
                                            else:
                                                skipped_line_no[str(
                                                    counter)] = " - Material product Unit of Measure not defined. "
                                                counter = counter + 1
                                                bom_list_for_unlink.append(
                                                    created_bom.id)
                                                continue

                                            vals.update(
                                                {'bom_id': created_bom.id})
                                            bom_line_obj.create(vals)
                                            counter = counter + 1

                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Material product not found. "
                                            bom_list_for_unlink.append(
                                                created_bom.id)
                                            counter = counter + 1

                                    else:
                                        skipped_line_no[str(
                                            counter)] = " - BoM not created. "
                                        counter = counter + 1

                                else:
                                    if created_bom:
                                        bom_list_for_unlink.append(
                                            created_bom.id)
                                    skipped_line_no[str(
                                        counter)] = " - Reference or Material product is empty. "
                                    counter = counter + 1

                            except Exception as e:
                                if created_bom:
                                    bom_list_for_unlink.append(created_bom.id)
                                skipped_line_no[str(
                                    counter)] = " - Value is not valid " + ustr(e)
                                counter = counter + 1
                                continue

                        if bom_list_for_unlink:
                            search_boms = bom_obj.search(
                                [('id', 'in', bom_list_for_unlink)])
                            if search_boms:
                                search_boms.unlink()

                            for item in bom_list_for_unlink:
                                if item in created_bom_list:
                                    created_bom_list.remove(item)

                    except Exception as e:
                        raise UserError(
                            _("Sorry, Your csv file does not match with our format" + ustr(e)))

                    if counter > 1:
                        completed_records = len(created_bom_list)
                        res = rec.show_success_msg(
                            completed_records, skipped_line_no)
                        return res

            # For Excel
            if self.import_type == 'excel':
                for rec in self:
                    counter = 1
                    skipped_line_no = {}
                    try:
                        wb = xlrd.open_workbook(
                            file_contents=base64.decodebytes(rec.file))
                        sheet = wb.sheet_by_index(0)
                        skip_header = True
                        running_bom = None
                        created_bom = False
                        created_bom_list = []
                        bom_list_for_unlink = []

                        for row in range(sheet.nrows):
                            try:
                                if skip_header:
                                    skip_header = False
                                    counter = counter + 1
                                    continue

                                if sheet.cell(row, 0).value not in (None, "") and sheet.cell(row, 5).value not in (None, ""):
                                    vals = {}

                                    if sheet.cell(row, 0).value != running_bom:

                                        running_bom = sheet.cell(row, 0).value
                                        bom_vals = {}

                                        if sheet.cell(row, 1).value not in (None, ""):

                                            field_nm = 'name'
                                            if rec.product_by == 'name':
                                                field_nm = 'name'
                                            elif rec.product_by == 'int_ref':
                                                field_nm = 'default_code'
                                            elif rec.product_by == 'barcode':
                                                field_nm = 'barcode'

                                            search_product_tmpl = self.env['product.template'].search(
                                                [(field_nm, '=', sheet.cell(row, 1).value)], limit=1)
                                            if search_product_tmpl and search_product_tmpl.type in ['product', 'consu']:
                                                bom_vals.update(
                                                    {'product_tmpl_id': search_product_tmpl.id})

                                                if sheet.cell(row, 2).value not in (None, ""):
                                                    search_product_var = self.env['product.product'].search(
                                                        [(field_nm, '=', sheet.cell(row, 2).value)], limit=1)
                                                    if search_product_var and search_product_var.product_tmpl_id.id == search_product_tmpl.id and search_product_var.type in ['product', 'consu']:
                                                        bom_vals.update(
                                                            {'product_id': search_product_var.id})
                                                    else:
                                                        skipped_line_no[str(
                                                            counter)] = " - Product Variant is invalid. "
                                                        counter = counter + 1
                                                        continue
                                                if sheet.cell(row, 3).value not in (None, ""):
                                                    bom_vals.update(
                                                        {'product_qty': sheet.cell(row, 3).value})
                                                else:
                                                    bom_vals.update(
                                                        {'product_qty': 1})

                                                if sheet.cell(row, 4).value not in (None, ""):
                                                    search_uom = self.env['uom.uom'].search(
                                                        [('name', '=', sheet.cell(row, 4).value)], limit=1)
                                                    if search_uom:
                                                        bom_vals.update(
                                                            {'product_uom_id': search_uom.id})
                                                    else:
                                                        skipped_line_no[str(
                                                            counter)] = " - Unit of Measure not found. "
                                                        counter = counter + 1
                                                        continue
                                                elif search_product_tmpl.uom_id:
                                                    bom_vals.update(
                                                        {'product_uom_id': search_product_tmpl.uom_id.id})
                                                else:
                                                    skipped_line_no[str(
                                                        counter)] = " - Unit of Measure not defined. "
                                                    counter = counter + 1
                                                    continue

                                                if rec.bom_type == 'mtp':
                                                    bom_vals.update(
                                                        {'type': 'normal'})
                                                else:
                                                    bom_vals.update(
                                                        {'type': 'phantom'})

                                                bom_vals.update(
                                                    {'code': sheet.cell(row, 0).value})
                                                created_bom = bom_obj.create(
                                                    bom_vals)
                                                if created_bom:
                                                    created_bom_list.append(
                                                        created_bom.id)

                                            else:
                                                skipped_line_no[str(
                                                    counter)] = " - Finished Product not found or it's type is invalid. "
                                                counter = counter + 1
                                                continue

                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Finished Product field is empty. "
                                            counter = counter + 1
                                            continue

                                    if created_bom:
                                        field_nm = 'name'
                                        if rec.product_by == 'name':
                                            field_nm = 'name'
                                        elif rec.product_by == 'int_ref':
                                            field_nm = 'default_code'
                                        elif rec.product_by == 'barcode':
                                            field_nm = 'barcode'

                                        search_material_product = self.env['product.product'].search(
                                            [(field_nm, '=', sheet.cell(row, 5).value)], limit=1)
                                        if search_material_product:
                                            vals.update(
                                                {'product_id': search_material_product.id})

                                            if sheet.cell(row, 6).value not in (None, ""):
                                                vals.update(
                                                    {'product_qty': sheet.cell(row, 6).value})
                                            else:
                                                vals.update({'product_qty': 1})

                                            if sheet.cell(row, 7).value not in (None, ""):
                                                search_uom = self.env['uom.uom'].search(
                                                    [('name', '=', sheet.cell(row, 7).value)], limit=1)
                                                if search_uom:
                                                    vals.update(
                                                        {'product_uom_id': search_uom.id})
                                                else:
                                                    skipped_line_no[str(
                                                        counter)] = " - Material product Unit of Measure not found. "
                                                    counter = counter + 1
                                                    bom_list_for_unlink.append(
                                                        created_bom.id)
                                                    continue
                                            elif search_material_product.uom_id:
                                                vals.update(
                                                    {'product_uom_id': search_material_product.uom_id.id})
                                            else:
                                                skipped_line_no[str(
                                                    counter)] = " - Material product Unit of Measure not defined. "
                                                counter = counter + 1
                                                bom_list_for_unlink.append(
                                                    created_bom.id)
                                                continue

                                            vals.update(
                                                {'bom_id': created_bom.id})
                                            bom_line_obj.create(vals)
                                            counter = counter + 1

                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Material product not found. "
                                            bom_list_for_unlink.append(
                                                created_bom.id)
                                            counter = counter + 1

                                    else:
                                        skipped_line_no[str(
                                            counter)] = " - BoM not created. "
                                        counter = counter + 1

                                else:
                                    if created_bom:
                                        bom_list_for_unlink.append(
                                            created_bom.id)
                                    skipped_line_no[str(
                                        counter)] = " - Reference or Material product is empty. "
                                    counter = counter + 1

                            except Exception as e:
                                if created_bom:
                                    bom_list_for_unlink.append(created_bom.id)
                                skipped_line_no[str(
                                    counter)] = " - Value is not valid " + ustr(e)
                                counter = counter + 1
                                continue

                        if bom_list_for_unlink:
                            search_boms = bom_obj.search(
                                [('id', 'in', bom_list_for_unlink)])
                            if search_boms:
                                search_boms.unlink()

                            for item in bom_list_for_unlink:
                                if item in created_bom_list:
                                    created_bom_list.remove(item)

                    except Exception as e:
                        raise UserError(
                            _("Sorry, Your excel file does not match with our format" + ustr(e)))

                    if counter > 1:
                        completed_records = len(created_bom_list)
                        res = rec.show_success_msg(
                            completed_records, skipped_line_no)
                        return res
