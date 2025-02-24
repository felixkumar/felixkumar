# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import csv
import base64
import xlrd
from odoo.tools import ustr
import logging


_logger = logging.getLogger(__name__)


class ImportPOLWizard(models.TransientModel):
    _name = "import.pol.wizard"
    _description = "Import Purchase Order Line Wizard"

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
            name_relational_model = self.env['purchase.order.line'].fields_get()[
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
            name_relational_model = self.env['purchase.order.line'].fields_get()[
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

        # get selection field key and value.
        selection_key_value_list = self.env['purchase.order.line'].sudo(
        )._fields[field_name].selection
        if selection_key_value_list and field_value not in (None, ""):
            for tuple_item in selection_key_value_list:
                if tuple_item[1] == field_value:
                    return {field_name: tuple_item[0] or False}

            return {"error": " - " + field_name + " given value " + str(field_value) + " does not match for selection. "}

        # finaly return false
        if field_value in (None, ""):
            return {field_name: False}

        return {field_name: field_value or False}

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

    def import_pol_apply(self):
        pol_obj = self.env['purchase.order.line']
        ir_model_fields_obj = self.env['ir.model.fields']

        # perform import lead
        if self and self.file and self.env.context.get('sh_po_id', False):
            # For CSV
            if self.import_type == 'csv':
                counter = 1
                skipped_line_no = {}
                row_field_dic = {}
                row_field_error_dic = {}
                try:
                    file = str(base64.decodebytes(self.file).decode('utf-8'))
                    myreader = csv.reader(file.splitlines())
                    skip_header = True

                    for row in myreader:
                        try:
                            if skip_header:
                                skip_header = False

                                for i in range(7, len(row)):
                                    name_field = row[i]
                                    name_m2o = False
                                    if '@' in row[i]:
                                        list_field_str = name_field.split('@')
                                        name_field = list_field_str[0]
                                        name_m2o = list_field_str[1]
                                    search_field = ir_model_fields_obj.sudo().search([
                                        ("model", "=", "purchase.order.line"),
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
                                if search_product:
                                    vals.update(
                                        {'product_id': search_product.id})

                                    if row[1] != '':
                                        vals.update({'name': row[1]})
                                    else:
                                        vals.update(
                                            {'name': search_product.name})

                                        active_po = self.env['purchase.order'].search(
                                            [('id', '=', self.env.context.get('sh_po_id'))])
                                        if active_po:
                                            product_lang = search_product.with_context({
                                                'lang': active_po.partner_id.lang,
                                                'partner_id': active_po.partner_id.id,
                                            })
                                            pro_desc = product_lang.display_name
                                            if product_lang.description_purchase:
                                                pro_desc += '\n' + product_lang.description_purchase
                                            vals.update({'name': pro_desc})

                                    if row[2] != '':
                                        vals.update({'product_qty': row[2]})
                                    else:
                                        vals.update({'product_qty': 1})

                                    if row[3] in (None, "") and search_product.uom_po_id:
                                        vals.update(
                                            {'product_uom': search_product.uom_po_id.id})
                                    else:
                                        search_uom = self.env['uom.uom'].search(
                                            [('name', '=', row[3])], limit=1)
                                        if search_uom:
                                            vals.update(
                                                {'product_uom': search_uom.id})
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Unit of Measure not found. "
                                            counter = counter + 1
                                            continue

                                    if row[4] in (None, ""):
                                        vals.update(
                                            {'price_unit': search_product.standard_price})
                                    else:
                                        vals.update({'price_unit': row[4]})

                                    if row[5].strip() in (None, "") and search_product.supplier_taxes_id:
                                        vals.update(
                                            {'taxes_id': [(6, 0, search_product.supplier_taxes_id.ids)]})
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
                                                {'taxes_id': [(6, 0, taxes_list)]})

                                    if row[6] in (None, ""):
                                        vals.update(
                                            {'date_planned': datetime.now()})
                                    else:
                                        cd = row[6]
                                        cd = str(datetime.strptime(
                                            cd, '%Y-%m-%d').date())
                                        vals.update({"date_planned": cd})

                                else:
                                    skipped_line_no[str(
                                        counter)] = " - Product not found. "
                                    counter = counter + 1
                                    continue

                                vals.update(
                                    {'order_id': self.env.context.get('sh_po_id')})

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

                                pol_obj.create(vals)
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

                except Exception:
                    raise UserError(
                        _("Sorry, Your csv file does not match with our format"))

                if counter > 1:
                    completed_records = (counter - len(skipped_line_no)) - 2
                    res = self.show_success_msg(
                        completed_records, skipped_line_no)
                    return res

            # For Excel
            if self.import_type == 'excel':
                counter = 1
                skipped_line_no = {}
                row_field_dic = {}
                row_field_error_dic = {}
                try:
                    wb = xlrd.open_workbook(
                        file_contents=base64.decodebytes(self.file))
                    sheet = wb.sheet_by_index(0)
                    skip_header = True
                    for row in range(sheet.nrows):
                        try:
                            if skip_header:
                                skip_header = False

                                for i in range(7, sheet.ncols):
                                    name_field = sheet.cell(row, i).value
                                    name_m2o = False
                                    if '@' in sheet.cell(row, i).value:
                                        list_field_str = name_field.split('@')
                                        name_field = list_field_str[0]
                                        name_m2o = list_field_str[1]
                                    search_field = ir_model_fields_obj.sudo().search([
                                        ("model", "=", "purchase.order.line"),
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
                                if search_product:
                                    vals.update(
                                        {'product_id': search_product.id})

                                    if sheet.cell(row, 1).value != '':
                                        vals.update(
                                            {'name': sheet.cell(row, 1).value})
                                    else:
                                        vals.update(
                                            {'name': search_product.name})

                                        active_po = self.env['purchase.order'].search(
                                            [('id', '=', self.env.context.get('sh_po_id'))])
                                        if active_po:
                                            product_lang = search_product.with_context({
                                                'lang': active_po.partner_id.lang,
                                                'partner_id': active_po.partner_id.id,
                                            })
                                            pro_desc = product_lang.display_name
                                            if product_lang.description_purchase:
                                                pro_desc += '\n' + product_lang.description_purchase
                                            vals.update({'name': pro_desc})

                                    if sheet.cell(row, 2).value != '':
                                        vals.update(
                                            {'product_qty': sheet.cell(row, 2).value})
                                    else:
                                        vals.update({'product_qty': 1})

                                    if sheet.cell(row, 3).value in (None, "") and search_product.uom_po_id:
                                        vals.update(
                                            {'product_uom': search_product.uom_po_id.id})
                                    else:
                                        search_uom = self.env['uom.uom'].search(
                                            [('name', '=', sheet.cell(row, 3).value)], limit=1)
                                        if search_uom:
                                            vals.update(
                                                {'product_uom': search_uom.id})
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Unit of Measure not found. "
                                            counter = counter + 1
                                            continue

                                    if sheet.cell(row, 4).value in (None, ""):
                                        vals.update(
                                            {'price_unit': search_product.standard_price})
                                    else:
                                        vals.update(
                                            {'price_unit': sheet.cell(row, 4).value})

                                    if sheet.cell(row, 5).value.strip() in (None, "") and search_product.supplier_taxes_id:
                                        vals.update(
                                            {'taxes_id': [(6, 0, search_product.supplier_taxes_id.ids)]})
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
                                                {'taxes_id': [(6, 0, taxes_list)]})

                                    if sheet.cell(row, 6).value in (None, ""):
                                        vals.update(
                                            {'date_planned': datetime.now()})
                                    else:
                                        cd = sheet.cell(row, 6).value
                                        cd = str(datetime.strptime(
                                            cd, '%Y-%m-%d').date())
                                        vals.update({"date_planned": cd})

                                else:
                                    skipped_line_no[str(
                                        counter)] = " - Product not found. "
                                    counter = counter + 1
                                    continue

                                vals.update(
                                    {'order_id': self.env.context.get('sh_po_id')})

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

                                pol_obj.create(vals)
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

                except Exception:
                    raise UserError(
                        _("Sorry, Your excel file does not match with our format"))

                if counter > 1:
                    completed_records = (counter - len(skipped_line_no)) - 2
                    res = self.show_success_msg(
                        completed_records, skipped_line_no)
                    return res
