# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import csv
import base64
import xlrd
from odoo.tools import ustr


class ImportSOWizard(models.TransientModel):
    _name = "import.so.wizard"
    _description = "Import Sale Order Wizard"

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
    is_create_customer = fields.Boolean(string="Create Customer?")
    is_confirm_sale = fields.Boolean(string="Auto Confirm Sale?")
    order_no_type = fields.Selection([
        ('auto', 'Auto'),
        ('as_per_sheet', 'As per sheet')
    ], default="auto", string="Quotation/Order Number", required=True)

    def show_success_msg(self, counter, confirm_rec, skipped_line_no):
        # open the new success message box
        view = self.env.ref('sh_message.sh_message_wizard')
        context = dict(self._context or {})
        dic_msg = str(counter) + " Records imported successfully \n"
        dic_msg = dic_msg + str(confirm_rec) + " Records Confirm"
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

    def import_so_apply(self):
        sol_obj = self.env['sale.order.line']
        sale_order_obj = self.env['sale.order']
        # perform import lead
        if self:
            for rec in self:
                # For CSV
                if rec.import_type == 'csv':
                    counter = 1
                    skipped_line_no = {}
                    try:
                        file = str(base64.decodebytes(
                            rec.file).decode('utf-8'))
                        myreader = csv.reader(file.splitlines())
                        skip_header = True
                        running_so = None
                        created_so = False
                        created_so_list_for_confirm = []
                        created_so_list = []
                        for row in myreader:
                            try:
                                if skip_header:
                                    skip_header = False
                                    counter = counter + 1
                                    continue

                                if row[0] not in (None, "") and row[4] not in (None, ""):
                                    vals = {}

                                    if row[0] != running_so:

                                        running_so = row[0]
                                        so_vals = {}

                                        if row[1] not in (None, ""):
                                            partner_obj = self.env["res.partner"]
                                            partner = partner_obj.search(
                                                [('name', '=', row[1])], limit=1)

                                            if partner:
                                                so_vals.update(
                                                    {'partner_id': partner.id})
                                            elif rec.is_create_customer:
                                                partner = partner_obj.create({'company_type': 'person',
                                                                              'name': row[1],
                                                                              'customer_rank': 1,
                                                                              })
                                                if not partner:
                                                    skipped_line_no[str(
                                                        counter)] = " - Customer not created. "
                                                    counter = counter + 1
                                                    continue
                                                else:
                                                    so_vals.update(
                                                        {'partner_id': partner.id})
                                            else:
                                                skipped_line_no[str(
                                                    counter)] = " - Customer not found. "
                                                counter = counter + 1
                                                continue
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Customer field is empty. "
                                            counter = counter + 1
                                            continue

                                        if row[2] not in (None, ""):
                                            cd = row[2]
                                            cd = str(datetime.strptime(
                                                cd, '%Y-%m-%d').date())
                                            so_vals.update({'date_order': cd})

                                        if row[3] not in (None, ""):
                                            search_user = self.env['res.users'].search(
                                                [('name', '=', row[3])], limit=1)
                                            if search_user:
                                                so_vals.update(
                                                    {'user_id': search_user.id})
                                            else:
                                                skipped_line_no[str(
                                                    counter)] = " - Salesperson not found. "
                                                counter = counter + 1
                                                continue

                                        if rec.order_no_type == 'as_per_sheet':
                                            so_vals.update({"name": row[0]})
                                        created_so = sale_order_obj.create(
                                            so_vals)
                                        created_so_list_for_confirm.append(
                                            created_so.id)
                                        created_so_list.append(created_so.id)

                                    if created_so:

                                        field_nm = 'name'
                                        if rec.product_by == 'name':
                                            field_nm = 'name'
                                        elif rec.product_by == 'int_ref':
                                            field_nm = 'default_code'
                                        elif rec.product_by == 'barcode':
                                            field_nm = 'barcode'

                                        search_product = self.env['product.product'].search(
                                            [(field_nm, '=', row[4])], limit=1)
                                        if search_product:
                                            vals.update(
                                                {'product_id': search_product.id})

                                            if row[5] != '':
                                                vals.update({'name': row[5]})

                                            if row[6] != '':
                                                vals.update(
                                                    {'product_uom_qty': row[6]})
                                            else:
                                                vals.update(
                                                    {'product_uom_qty': 1})

                                            if row[7] in (None, "") and search_product.uom_id:
                                                vals.update(
                                                    {'product_uom': search_product.uom_id.id})
                                            else:
                                                search_uom = self.env['uom.uom'].search(
                                                    [('name', '=', row[7])], limit=1)
                                                if search_uom:
                                                    vals.update(
                                                        {'product_uom': search_uom.id})
                                                else:
                                                    skipped_line_no[str(
                                                        counter)] = " - Unit of Measure not found. "
                                                    counter = counter + 1
                                                    if created_so.id in created_so_list_for_confirm:
                                                        created_so_list_for_confirm.remove(
                                                            created_so.id)
                                                    continue

                                            if row[8] in (None, ""):
                                                vals.update(
                                                    {'price_unit': search_product.lst_price})
                                            else:
                                                vals.update(
                                                    {'price_unit': row[8]})

                                            if row[9].strip() in (None, "") and search_product.taxes_id:
                                                vals.update(
                                                    {'tax_id': [(6, 0, search_product.taxes_id.ids)]})
                                            else:
                                                taxes_list = []
                                                some_taxes_not_found = False
                                                for x in row[9].split(','):
                                                    x = x.strip()
                                                    if x != '':
                                                        search_tax = self.env['account.tax'].search(
                                                            [('name', '=', x)], limit=1)
                                                        if search_tax:
                                                            taxes_list.append(
                                                                search_tax.id)
                                                        else:
                                                            some_taxes_not_found = True
                                                            skipped_line_no[str(
                                                                counter)] = " - Taxes " + x + " not found. "
                                                            break
                                                if some_taxes_not_found:
                                                    counter = counter + 1
                                                    if created_so.id in created_so_list_for_confirm:
                                                        created_so_list_for_confirm.remove(
                                                            created_so.id)
                                                    continue
                                                else:
                                                    vals.update(
                                                        {'tax_id': [(6, 0, taxes_list)]})

                                            vals.update(
                                                {'order_id': created_so.id})
                                            sol_obj.create(vals)
                                            counter = counter + 1

                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Product not found. "
                                            counter = counter + 1
                                            if created_so.id in created_so_list_for_confirm:
                                                created_so_list_for_confirm.remove(
                                                    created_so.id)
                                            continue

                                    else:
                                        skipped_line_no[str(
                                            counter)] = " - Order not created. "
                                        counter = counter + 1
                                        continue

                                else:
                                    skipped_line_no[str(
                                        counter)] = " - Sales Order or Product field is empty. "
                                    counter = counter + 1

                            except Exception as e:
                                skipped_line_no[str(
                                    counter)] = " - Value is not valid " + ustr(e)
                                counter = counter + 1
                                continue
                        if created_so_list_for_confirm and rec.is_confirm_sale:
                            sale_orders = sale_order_obj.search(
                                [('id', 'in', created_so_list_for_confirm)])
                            if sale_orders:
                                for sale_order in sale_orders:
                                    sale_order.action_confirm()
                        else:
                            created_so_list_for_confirm = []

                    except Exception as e:
                        raise UserError(
                            _("Sorry, Your csv file does not match with our format " + ustr(e)))

                    if counter > 1:
                        completed_records = len(created_so_list)
                        confirm_rec = len(created_so_list_for_confirm)
                        res = self.show_success_msg(
                            completed_records, confirm_rec, skipped_line_no)
                        return res

                # For Excel
                if rec.import_type == 'excel':
                    counter = 1
                    skipped_line_no = {}
                    try:
                        wb = xlrd.open_workbook(
                            file_contents=base64.decodebytes(rec.file))
                        sheet = wb.sheet_by_index(0)
                        skip_header = True
                        running_so = None
                        created_so = False
                        created_so_list_for_confirm = []
                        created_so_list = []
                        for row in range(sheet.nrows):
                            try:
                                if skip_header:
                                    skip_header = False
                                    counter = counter + 1
                                    continue

                                if sheet.cell(row, 0).value not in (None, "") and sheet.cell(row, 4).value not in (None, ""):
                                    vals = {}

                                    if sheet.cell(row, 0).value != running_so:

                                        running_so = sheet.cell(row, 0).value
                                        so_vals = {}

                                        if sheet.cell(row, 1).value not in (None, ""):
                                            partner_obj = self.env["res.partner"]
                                            partner = partner_obj.search(
                                                [('name', '=', sheet.cell(row, 1).value)], limit=1)

                                            if partner:
                                                so_vals.update(
                                                    {'partner_id': partner.id})
                                            elif rec.is_create_customer:
                                                partner = partner_obj.create({'company_type': 'person',
                                                                              'name': sheet.cell(row, 1).value,
                                                                              'customer_rank': 1,
                                                                              })
                                                if not partner:
                                                    skipped_line_no[str(
                                                        counter)] = " - Customer not created. "
                                                    counter = counter + 1
                                                    continue
                                                else:
                                                    so_vals.update(
                                                        {'partner_id': partner.id})
                                            else:
                                                skipped_line_no[str(
                                                    counter)] = " - Customer not found. "
                                                counter = counter + 1
                                                continue
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Customer field is empty. "
                                            counter = counter + 1
                                            continue
                                        if sheet.cell(row, 2).value not in (None, ""):
                                            cd = sheet.cell(row, 2).value
                                            cd = str(datetime.strptime(
                                                cd, '%Y-%m-%d').date())
                                            so_vals.update({'date_order': cd})

                                        if sheet.cell(row, 3).value not in (None, ""):
                                            search_user = self.env['res.users'].search(
                                                [('name', '=', sheet.cell(row, 3).value)], limit=1)
                                            if search_user:
                                                so_vals.update(
                                                    {'user_id': search_user.id})
                                            else:
                                                skipped_line_no[str(
                                                    counter)] = " - Salesperson not found. "
                                                counter = counter + 1
                                                continue

                                        if rec.order_no_type == 'as_per_sheet':
                                            so_vals.update(
                                                {"name": sheet.cell(row, 0).value})
                                        created_so = sale_order_obj.create(
                                            so_vals)
                                        created_so_list_for_confirm.append(
                                            created_so.id)
                                        created_so_list.append(created_so.id)

                                    if created_so:

                                        field_nm = 'name'
                                        if rec.product_by == 'name':
                                            field_nm = 'name'
                                        elif rec.product_by == 'int_ref':
                                            field_nm = 'default_code'
                                        elif rec.product_by == 'barcode':
                                            field_nm = 'barcode'

                                        search_product = self.env['product.product'].search(
                                            [(field_nm, '=', sheet.cell(row, 4).value)], limit=1)
                                        if search_product:
                                            vals.update(
                                                {'product_id': search_product.id})

                                            if sheet.cell(row, 5).value != '':
                                                vals.update(
                                                    {'name': sheet.cell(row, 5).value})

                                            if sheet.cell(row, 6).value != '':
                                                vals.update(
                                                    {'product_uom_qty': sheet.cell(row, 6).value})
                                            else:
                                                vals.update(
                                                    {'product_uom_qty': 1})

                                            if sheet.cell(row, 7).value in (None, "") and search_product.uom_id:
                                                vals.update(
                                                    {'product_uom': search_product.uom_id.id})
                                            else:
                                                search_uom = self.env['uom.uom'].search(
                                                    [('name', '=', sheet.cell(row, 7).value)], limit=1)
                                                if search_uom:
                                                    vals.update(
                                                        {'product_uom': search_uom.id})
                                                else:
                                                    skipped_line_no[str(
                                                        counter)] = " - Unit of Measure not found. "
                                                    if created_so.id in created_so_list_for_confirm:
                                                        created_so_list_for_confirm.remove(
                                                            created_so.id)
                                                    counter = counter + 1
                                                    continue

                                            if sheet.cell(row, 8).value in (None, ""):
                                                vals.update(
                                                    {'price_unit': search_product.lst_price})
                                            else:
                                                vals.update(
                                                    {'price_unit': sheet.cell(row, 8).value})

                                            if sheet.cell(row, 9).value in (None, "") and search_product.taxes_id:
                                                vals.update(
                                                    {'tax_id': [(6, 0, search_product.taxes_id.ids)]})
                                            else:
                                                taxes_list = []
                                                some_taxes_not_found = False
                                                for x in sheet.cell(row, 9).value.split(','):
                                                    x = x.strip()
                                                    if x != '':
                                                        search_tax = self.env['account.tax'].search(
                                                            [('name', '=', x)], limit=1)
                                                        if search_tax:
                                                            taxes_list.append(
                                                                search_tax.id)
                                                        else:
                                                            some_taxes_not_found = True
                                                            skipped_line_no[str(
                                                                counter)] = " - Taxes " + x + " not found. "
                                                            break
                                                if some_taxes_not_found:
                                                    counter = counter + 1
                                                    if created_so.id in created_so_list_for_confirm:
                                                        created_so_list_for_confirm.remove(
                                                            created_so.id)
                                                    continue
                                                else:
                                                    vals.update(
                                                        {'tax_id': [(6, 0, taxes_list)]})

                                            vals.update(
                                                {'order_id': created_so.id})
                                            sol_obj.create(vals)
                                            counter = counter + 1

                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Product not found. "
                                            counter = counter + 1
                                            if created_so.id in created_so_list_for_confirm:
                                                created_so_list_for_confirm.remove(
                                                    created_so.id)
                                            continue

                                    else:
                                        skipped_line_no[str(
                                            counter)] = " - Order not created. "
                                        counter = counter + 1
                                        continue

                                else:
                                    skipped_line_no[str(
                                        counter)] = " - Sales Order or Product field is empty. "
                                    counter = counter + 1

                            except Exception as e:
                                skipped_line_no[str(
                                    counter)] = " - Value is not valid " + ustr(e)
                                counter = counter + 1
                                continue

                        if created_so_list_for_confirm and rec.is_confirm_sale:
                            sale_orders = sale_order_obj.search(
                                [('id', 'in', created_so_list_for_confirm)])
                            if sale_orders:
                                for sale_order in sale_orders:
                                    sale_order.action_confirm()
                        else:
                            created_so_list_for_confirm = []

                    except Exception as e:
                        raise UserError(
                            _("Sorry, Your excel file does not match with our format " + ustr(e)))

                    if counter > 1:
                        completed_records = len(created_so_list)
                        confirm_rec = len(created_so_list_for_confirm)
                        res = self.show_success_msg(
                            completed_records, confirm_rec, skipped_line_no)
                        return res
