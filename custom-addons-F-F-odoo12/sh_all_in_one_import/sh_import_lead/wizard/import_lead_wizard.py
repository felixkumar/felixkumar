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


class ImportLeadWizard(models.TransientModel):
    _name = "import.lead.wizard"
    _description = "Import Lead Wizard"

    import_type = fields.Selection([
        ('csv', 'CSV File'),
        ('excel', 'Excel File')
    ], default="csv", string="Import File Type", required=True)
    file = fields.Binary(string="File", required=True)

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
            name_relational_model = self.env['crm.lead'].fields_get()[
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
            name_relational_model = self.env['crm.lead'].fields_get()[
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
        selection_key_value_list = self.env['crm.lead'].sudo(
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
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }

    def import_lead_apply(self):

        crm_lead_obj = self.env['crm.lead']
        ir_model_fields_obj = self.env['ir.model.fields']
        #perform import lead
        if self and self.file:
            #For CSV
            if self.import_type == 'csv':
                for rec in self:
                    counter = 1
                    skipped_line_no = {}
                    row_field_dic = {}
                    row_field_error_dic = {}
                    try:
                        file = str(base64.decodebytes(
                            rec.file).decode('utf-8'))
                        myreader = csv.reader(file.splitlines())
                        skip_header = True

                        for row in myreader:
                            try:
                                if skip_header:
                                    skip_header = False

                                    for i in range(15, len(row)):
                                        name_field = row[i]
                                        name_m2o = False
                                        if '@' in row[i]:
                                            list_field_str = name_field.split(
                                                '@')
                                            name_field = list_field_str[0]
                                            name_m2o = list_field_str[1]
                                        search_field = ir_model_fields_obj.sudo().search([
                                            ("model", "=", "crm.lead"),
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
                                            row_field_dic.update(
                                                {i: field_dic})
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

                                    search_state_id = False
                                    if row[5] != '':
                                        search_state = self.env['res.country.state'].search(
                                            [('name', '=', row[5])], limit=1)
                                        if search_state:
                                            search_state_id = search_state.id
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - State not found. "
                                            counter = counter + 1
                                            continue
                                    search_country_id = False
                                    if row[7] != '':
                                        search_country = self.env["res.country"].search(
                                            [('name', '=', row[7])], limit=1)
                                        if search_country:
                                            search_country_id = search_country.id
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Country not found. "
                                            counter = counter + 1
                                            continue
                                    search_user_id = False
                                    if row[13] != '':
                                        search_user = self.env["res.users"].search(
                                            [('name', '=', row[13])], limit=1)
                                        if search_user:
                                            search_user_id = search_user.id
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Salesperson not found. "
                                            counter = counter + 1
                                            continue

                                    vals = {
                                        'name': row[0],
                                        'partner_name': row[1],
                                        'street': row[2],
                                        'street2': row[3],
                                        'city': row[4],
                                        'state_id': search_state_id,
                                        'zip': row[6],
                                        'country_id': search_country_id,
                                        'email_from': row[8],
                                        'function': row[9],
                                        'phone': row[10],
                                        'mobile': row[11],
                                        'website': row[12],
                                        'user_id': search_user_id,
                                        'description': row[14],
                                        'type': 'lead',
                                    }

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

                                    crm_lead_obj.create(vals)
                                    counter = counter + 1
                                else:
                                    skipped_line_no[str(
                                        counter)] = " - Lead name is empty. "
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
                        completed_lead = (counter - len(skipped_line_no)) - 2
                        res = rec.show_success_msg(
                            completed_lead, skipped_line_no)
                        return res

            #For Excel
            if self.import_type == 'excel':
                for rec in self:
                    counter = 1
                    skipped_line_no = {}
                    ##Add Two Dictionary
                    row_field_dic = {}
                    row_field_error_dic = {}
                    try:
                        wb = xlrd.open_workbook(
                            file_contents=base64.decodebytes(rec.file))
                        sheet = wb.sheet_by_index(0)
                        skip_header = True
                        for row in range(sheet.nrows):
                            try:
                                if skip_header:
                                    skip_header = False

                                    for i in range(15, sheet.ncols):
                                        name_field = sheet.cell(row, i).value
                                        name_m2o = False
                                        if '@' in sheet.cell(row, i).value:
                                            list_field_str = name_field.split(
                                                '@')
                                            name_field = list_field_str[0]
                                            name_m2o = list_field_str[1]
                                        search_field = ir_model_fields_obj.sudo().search([
                                            ("model", "=", "crm.lead"),
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
                                            row_field_dic.update(
                                                {i: field_dic})
                                        else:
                                            row_field_error_dic.update(
                                                {sheet.cell(row, i).value: " - field not found"})

                                    counter = counter + 1
                                    continue

                                if row_field_error_dic:
                                    res = self.show_success_msg(
                                        0, row_field_error_dic)
                                    return res

                                if sheet.cell(row, 0).value != '':

                                    search_state_id = False
                                    if sheet.cell(row, 5).value != '':
                                        search_state = self.env['res.country.state'].search(
                                            [('name', '=', sheet.cell(row, 5).value)], limit=1)
                                        if search_state:
                                            search_state_id = search_state.id
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - State not found. "
                                            counter = counter + 1
                                            continue
                                    search_country_id = False
                                    if sheet.cell(row, 7).value != '':
                                        search_country = self.env["res.country"].search(
                                            [('name', '=', sheet.cell(row, 7).value)], limit=1)
                                        if search_country:
                                            search_country_id = search_country.id
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Country not found. "
                                            counter = counter + 1
                                            continue
                                    search_user_id = False
                                    if sheet.cell(row, 13).value != '':
                                        search_user = self.env["res.users"].search(
                                            [('name', '=', sheet.cell(row, 13).value)], limit=1)
                                        if search_user:
                                            search_user_id = search_user.id
                                        else:
                                            skipped_line_no[str(
                                                counter)] = " - Salesperson not found. "
                                            counter = counter + 1
                                            continue
                                    vals = {
                                        'name': sheet.cell(row, 0).value,
                                        'partner_name': sheet.cell(row, 1).value,
                                        'street': sheet.cell(row, 2).value,
                                        'street2': sheet.cell(row, 3).value,
                                        'city': sheet.cell(row, 4).value,
                                        'state_id': search_state_id,
                                        'zip': sheet.cell(row, 6).value,
                                        'country_id': search_country_id,
                                        'email_from': sheet.cell(row, 8).value,
                                        'function': sheet.cell(row, 9).value,
                                        'phone': sheet.cell(row, 10).value,
                                        'mobile': sheet.cell(row, 11).value,
                                        'website': sheet.cell(row, 12).value,
                                        'user_id': search_user_id,
                                        'description': sheet.cell(row, 14).value,
                                        'type': 'lead',
                                    }

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

                                    crm_lead_obj.create(vals)
                                    counter = counter + 1
                                else:
                                    skipped_line_no[str(
                                        counter)] = " - Lead name is empty. "
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
                        completed_lead = (counter - len(skipped_line_no)) - 2
                        res = rec.show_success_msg(
                            completed_lead, skipped_line_no)
                        return res
