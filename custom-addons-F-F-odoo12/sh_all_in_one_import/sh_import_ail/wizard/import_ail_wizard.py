# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, _
from odoo.exceptions import UserError
import csv
import base64
import xlrd
from odoo.tools import ustr
import logging


_logger = logging.getLogger(__name__)


class ImportAILWizard(models.TransientModel):
    _name = "import.ail.wizard"
    _description = "Import AIL Wizard"

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

    def validate_field_value(self, field_name, field_ttype, field_value, field_required, field_name_m2o):
        """ Validate field value, depending on field type and given value """
        self.ensure_one()

        try:
            checker = getattr(self, 'validate_field_' + field_ttype)
        except AttributeError:
            _logger.warning(
                field_ttype + ": This type of field has no validation method")
            return {}
        else:
            return checker(field_name, field_ttype, field_value, field_required, field_name_m2o)

    def validate_field_many2many(self, field_name, field_ttype, field_value, field_required, field_name_m2o):
        self.ensure_one()
        if field_required and field_value in (None, ""):
            return {"error": " - " + field_name + " is required. "}
        else:
            name_relational_model = self.env['account.move.line'].fields_get()[
                field_name]['relation']

            ids_list = []
            if field_value.strip() not in (None, ""):
                for x in field_value.split(','):
                    x = x.strip()
                    if x != '':
                        record = self.env[name_relational_model].sudo().search([
                            (field_name_m2o, '=', x)
                        ], limit=1)

                        if record:
                            ids_list.append(record.id)
                        else:
                            return {"error": " - " + x + " not found. "}
                            break

            return {field_name: [(6, 0, ids_list)]}

    def validate_field_many2one(self, field_name, field_ttype, field_value, field_required, field_name_m2o):
        self.ensure_one()
        if field_required and field_value in (None, ""):
            return {"error": " - " + field_name + " is required. "}
        else:
            name_relational_model = self.env['account.move.line'].fields_get()[
                field_name]['relation']
            record = self.env[name_relational_model].sudo().search([
                (field_name_m2o, '=', field_value)
            ], limit=1)
            return {field_name: record.id if record else False}

    def validate_field_text(self, field_name, field_ttype, field_value, field_required, field_name_m2o):
        self.ensure_one()
        if field_required and field_value in (None, ""):
            return {"error": " - " + field_name + " is required. "}
        else:
            return {field_name: field_value or False}

    def validate_field_integer(self, field_name, field_ttype, field_value, field_required, field_name_m2o):
        self.ensure_one()
        if field_required and field_value in (None, ""):
            return {"error": " - " + field_name + " is required. "}
        else:
            return {field_name: field_value or False}

    def validate_field_float(self, field_name, field_ttype, field_value, field_required, field_name_m2o):
        self.ensure_one()
        if field_required and field_value in (None, ""):
            return {"error": " - " + field_name + " is required. "}
        else:
            return {field_name: field_value or False}

    def validate_field_char(self, field_name, field_ttype, field_value, field_required, field_name_m2o):
        self.ensure_one()
        if field_required and field_value in (None, ""):
            return {"error": " - " + field_name + " is required. "}
        else:
            return {field_name: field_value or False}

    def validate_field_boolean(self, field_name, field_ttype, field_value, field_required, field_name_m2o):
        self.ensure_one()
        boolean_field_value = False
        if field_value.strip() == 'TRUE':
            boolean_field_value = True

        return {field_name: boolean_field_value}

    def validate_field_selection(self, field_name, field_ttype, field_value, field_required, field_name_m2o):
        self.ensure_one()
        if field_required and field_value in (None, ""):
            return {"error": " - " + field_name + " is required. "}

        #get selection field key and value.
        selection_key_value_list = self.env['account.move.line'].sudo(
        )._fields[field_name].selection
        if selection_key_value_list and field_value not in (None, ""):
            for tuple_item in selection_key_value_list:
                if tuple_item[1] == field_value:
                    return {field_name: tuple_item[0] or False}

            return {"error": " - " + field_name + " given value " + str(field_value) + " does not match for selection. "}

        #finaly return false
        if field_value in (None, ""):
            return {field_name: False}

        return {field_name: field_value or False}

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

    def import_ail_apply(self):
        ir_model_fields_obj = self.env['ir.model.fields']
        #perform import lead
        if self and self.file and self.env.context.get('sh_inv_id', False):
            #For CSV
            if self.import_type == 'csv':
                counter = 1
                skipped_line_no = {}
                row_field_dic = {}
                row_field_error_dic = {}
                active_inv = False
                try:
                    file = str(base64.decodebytes(self.file).decode('utf-8'))
                    myreader = csv.reader(file.splitlines())
                    skip_header = True
                    invoice_line_ids = []
                    for row in myreader:
                        try:
                            if skip_header:
                                skip_header = False

                                for i in range(6, len(row)):
                                    name_field = row[i]
                                    name_m2o = False
                                    if '@' in row[i]:
                                        list_field_str = name_field.split('@')
                                        name_field = list_field_str[0]
                                        name_m2o = list_field_str[1]
                                    search_field = ir_model_fields_obj.sudo().search([
                                        ("model", "=", "account.move.line"),
                                        ("name", "=", name_field),
                                        ("store", "=", True),
                                    ], limit=1)

                                    if search_field:
                                        field_dic = {
                                            'name': name_field,
                                            'ttype': search_field.ttype,
                                            'required': search_field.required,
                                            'name_m2o': name_m2o
                                        }
                                        row_field_dic.update({i: field_dic})
                                    else:
                                        row_field_error_dic.update(
                                            {row[i]: " - field not found"})

                                counter = counter + 1
                                continue

                            if row_field_error_dic:
                                res = self.show_success_msg(
                                    0, row_field_error_dic)
                                return res

                            if row[0] != '':
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
                                active_inv = self.env['account.move'].search(
                                    [('id', '=', self.env.context.get('sh_inv_id'))], limit=1)
                                if search_product and active_inv:
                                    vals.update(
                                        {'product_id': search_product.id})

                                    if row[1] != '':
                                        vals.update({'name': row[1]})
                                    else:
                                        product = None
                                        name = ''
                                        if active_inv and active_inv.partner_id:
                                            if active_inv.partner_id.lang:
                                                product = search_product.with_context(
                                                    lang=active_inv.partner_id.lang)
                                            else:
                                                product = search_product

                                            name = product.partner_ref
                                        if active_inv.move_type in ('in_invoice', 'in_refund') and product:
                                            if product.description_purchase:
                                                name += '\n' + product.description_purchase
                                        elif product:
                                            if product.description_sale:
                                                name += '\n' + product.description_sale
                                        vals.update({'name': name})

                                    accounts = search_product.product_tmpl_id.get_product_accounts(
                                        active_inv.fiscal_position_id)
                                    account = False
                                    if active_inv.move_type in ('out_invoice', 'out_refund'):
                                        account = accounts['income']
                                    else:
                                        account = accounts['expense']
                                    if not account:
                                        skipped_line_no[str(
                                            counter)] = " - Account not found. "
                                        counter = counter + 1
                                        continue
                                    else:
                                        vals.update({'account_id': account.id})

                                    if row[2] != '':
                                        vals.update({'quantity': row[2]})
                                    else:
                                        vals.update({'quantity': 1})

                                    if row[3] in (None, ""):
                                        if active_inv.move_type in ('in_invoice', 'in_refund') and search_product.uom_po_id:
                                            vals.update(
                                                {'product_uom_id': search_product.uom_po_id.id})
                                        elif search_product.uom_id:
                                            vals.update(
                                                {'product_uom_id': search_product.uom_id.id})
                                    else:
                                        search_uom = self.env['uom.uom'].search(
                                            [('name', '=', row[3])], limit=1)
                                        if search_uom:
                                            vals.update(
                                                {'product_uom_id': search_uom.id})
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Unit of Measure not found. "
                                            counter = counter + 1
                                            continue

                                    if row[4] in (None, ""):
                                        if active_inv.move_type in ('in_invoice', 'in_refund'):
                                            vals.update(
                                                {'price_unit': search_product.standard_price})
                                        else:
                                            vals.update(
                                                {'price_unit': search_product.lst_price})
                                    else:
                                        vals.update({'price_unit': row[4]})

                                    if row[5].strip() in (None, ""):
                                        if active_inv.move_type in ('in_invoice', 'in_refund') and search_product.supplier_taxes_id:
                                            vals.update(
                                                {'tax_ids': [(6, 0, search_product.supplier_taxes_id.ids)]})
                                        elif active_inv.move_type in ('out_invoice', 'out_refund') and search_product.taxes_id:
                                            vals.update(
                                                {'tax_ids': [(6, 0, search_product.taxes_id.ids)]})

                                    else:
                                        taxes_list = []
                                        some_taxes_not_found = False
                                        for x in row[5].split(','):
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
                                            continue
                                        else:
                                            vals.update(
                                                {'tax_ids': [(6, 0, taxes_list)]})

                                else:
                                    skipped_line_no[str(
                                        counter)] = " - Product not found. "
                                    counter = counter + 1
                                    continue

                                is_any_error_in_dynamic_field = False
                                for k_row_index, v_field_dic in row_field_dic.items():

                                    field_name = v_field_dic.get("name")
                                    field_ttype = v_field_dic.get("ttype")
                                    field_value = row[k_row_index]
                                    field_required = v_field_dic.get(
                                        "required")
                                    field_name_m2o = v_field_dic.get(
                                        "name_m2o")

                                    dic = self.validate_field_value(
                                        field_name, field_ttype, field_value, field_required, field_name_m2o)
                                    if dic.get("error", False):
                                        skipped_line_no[str(counter)] = dic.get(
                                            "error")
                                        is_any_error_in_dynamic_field = True
                                        break
                                    else:
                                        vals.update(dic)

                                if is_any_error_in_dynamic_field:
                                    counter = counter + 1
                                    continue

                                vals.update(
                                    {'move_id': self.env.context.get('sh_inv_id')})
                                invoice_line_ids.append((0, 0, vals))
                                counter = counter + 1

                            else:
                                skipped_line_no[str(
                                    counter)] = " - Product is empty. "
                                counter = counter + 1

                        except Exception as e:
                            skipped_line_no[str(
                                counter)] = " - Value is not valid " + ustr(e)
                            counter = counter + 1
                            continue

#                     calculate taxes
                    if active_inv:
                        active_inv._onchange_partner_id()
                        active_inv._onchange_invoice_line_ids()
                    active_inv.write({'invoice_line_ids': invoice_line_ids})
                except Exception as e:
                    raise UserError(
                        _("Sorry, Your csv file does not match with our format" + ustr(e)))

                if counter > 1:
                    completed_records = (counter - len(skipped_line_no)) - 2
                    res = self.show_success_msg(
                        completed_records, skipped_line_no)
                    return res

            #For Excel
            if self.import_type == 'excel':
                counter = 1
                skipped_line_no = {}
                row_field_dic = {}
                row_field_error_dic = {}
                active_inv = False
                try:
                    wb = xlrd.open_workbook(
                        file_contents=base64.decodebytes(self.file))
                    sheet = wb.sheet_by_index(0)
                    skip_header = True
                    invoice_line_ids = []
                    for row in range(sheet.nrows):
                        try:
                            if skip_header:
                                skip_header = False

                                for i in range(6, sheet.ncols):
                                    name_field = sheet.cell(row, i).value
                                    name_m2o = False
                                    if '@' in sheet.cell(row, i).value:
                                        list_field_str = name_field.split('@')
                                        name_field = list_field_str[0]
                                        name_m2o = list_field_str[1]
                                    search_field = ir_model_fields_obj.sudo().search([
                                        ("model", "=", "account.move.line"),
                                        ("name", "=", name_field),
                                        ("store", "=", True),
                                    ], limit=1)
                                    if search_field:
                                        field_dic = {
                                            'name': name_field,
                                            'ttype': search_field.ttype,
                                            'required': search_field.required,
                                            'name_m2o': name_m2o
                                        }
                                        row_field_dic.update({i: field_dic})
                                    else:
                                        row_field_error_dic.update(
                                            {sheet.cell(row, i).value: " - field not found"})

                                counter = counter + 1
                                continue

                            if sheet.cell(row, 0).value != '':
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
                                active_inv = self.env['account.move'].search(
                                    [('id', '=', self.env.context.get('sh_inv_id'))], limit=1)
                                if search_product and active_inv:
                                    vals.update(
                                        {'product_id': search_product.id})

                                    if sheet.cell(row, 1).value != '':
                                        vals.update(
                                            {'name': sheet.cell(row, 1).value})
                                    else:
                                        name = ''
                                        product = None
                                        if active_inv and active_inv.partner_id:
                                            if active_inv.partner_id.lang:
                                                product = search_product.with_context(
                                                    lang=active_inv.partner_id.lang)
                                            else:
                                                product = search_product

                                            name = product.partner_ref
                                        if active_inv.move_type in ('in_invoice', 'in_refund') and product:
                                            if product.description_purchase:
                                                name += '\n' + product.description_purchase
                                        elif product:
                                            if product.description_sale:
                                                name += '\n' + product.description_sale
                                        vals.update({'name': name})

                                    accounts = search_product.product_tmpl_id.get_product_accounts(
                                        active_inv.fiscal_position_id)
                                    account = False
                                    if active_inv.move_type in ('out_invoice', 'out_refund'):
                                        account = accounts['income']
                                    else:
                                        account = accounts['expense']
                                    if not account:
                                        skipped_line_no[str(
                                            counter)] = " - Account not found. "
                                        counter = counter + 1
                                        continue
                                    else:
                                        vals.update({'account_id': account.id})

                                    if sheet.cell(row, 2).value != '':
                                        vals.update(
                                            {'quantity': sheet.cell(row, 2).value})
                                    else:
                                        vals.update({'quantity': 1})
                                    if sheet.cell(row, 3).value in (None, ""):
                                        if active_inv.move_type in ('in_invoice', 'in_refund') and search_product.uom_po_id:
                                            vals.update(
                                                {'product_uom_id': search_product.uom_po_id.id})
                                        elif search_product.uom_id:
                                            vals.update(
                                                {'product_uom_id': search_product.uom_id.id})
                                    else:
                                        search_uom = self.env['uom.uom'].search(
                                            [('name', '=', sheet.cell(row, 3).value)], limit=1)
                                        if search_uom:
                                            vals.update(
                                                {'product_uom_id': search_uom.id})
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Unit of Measure not found. "
                                            counter = counter + 1
                                            continue

                                    if sheet.cell(row, 4).value in (None, ""):
                                        if active_inv.move_type in ('in_invoice', 'in_refund'):
                                            vals.update(
                                                {'price_unit': search_product.standard_price})
                                        else:
                                            vals.update(
                                                {'price_unit': search_product.lst_price})
                                    else:
                                        vals.update(
                                            {'price_unit': sheet.cell(row, 4).value})
                                    if sheet.cell(row, 5).value.strip() in (None, ""):
                                        if active_inv.move_type in ('in_invoice', 'in_refund') and search_product.supplier_taxes_id:
                                            vals.update(
                                                {'tax_ids': [(6, 0, search_product.supplier_taxes_id.ids)]})
                                        elif active_inv.move_type in ('out_invoice', 'out_refund') and search_product.taxes_id:
                                            vals.update(
                                                {'tax_ids': [(6, 0, search_product.taxes_id.ids)]})

                                    else:
                                        taxes_list = []
                                        some_taxes_not_found = False
                                        for x in sheet.cell(row, 5).value.split(','):
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
                                            continue
                                        else:
                                            vals.update(
                                                {'tax_ids': [(6, 0, taxes_list)]})

                                else:
                                    skipped_line_no[str(
                                        counter)] = " - Product not found. "
                                    counter = counter + 1
                                    continue

                                is_any_error_in_dynamic_field = False
                                for k_row_index, v_field_dic in row_field_dic.items():

                                    field_name = v_field_dic.get("name")
                                    field_ttype = v_field_dic.get("ttype")
                                    field_value = sheet.cell(
                                        row, k_row_index).value
                                    field_required = v_field_dic.get(
                                        "required")
                                    field_name_m2o = v_field_dic.get(
                                        "name_m2o")

                                    dic = self.validate_field_value(
                                        field_name, field_ttype, field_value, field_required, field_name_m2o)
                                    if dic.get("error", False):
                                        skipped_line_no[str(counter)] = dic.get(
                                            "error")
                                        is_any_error_in_dynamic_field = True
                                        break
                                    else:
                                        vals.update(dic)

                                if is_any_error_in_dynamic_field:
                                    counter = counter + 1
                                    continue

                                vals.update(
                                    {'move_id': self.env.context.get('sh_inv_id')})
                                invoice_line_ids.append((0, 0, vals))
                                counter = counter + 1

                            else:
                                skipped_line_no[str(
                                    counter)] = " - Product is empty. "
                                counter = counter + 1

                        except Exception as e:
                            skipped_line_no[str(
                                counter)] = " - Value is not valid " + ustr(e)
                            counter = counter + 1
                            continue

#                     calculate taxes
                    if active_inv:
                        active_inv._onchange_partner_id()
                        active_inv._onchange_invoice_line_ids()
                    active_inv.write({'invoice_line_ids': invoice_line_ids})
                except Exception as e:
                    raise UserError(
                        _("Sorry, Your excel file does not match with our format" + ustr(e)))

                if counter > 1:
                    completed_records = (counter - len(skipped_line_no)) - 2
                    res = self.show_success_msg(
                        completed_records, skipped_line_no)
                    return res
