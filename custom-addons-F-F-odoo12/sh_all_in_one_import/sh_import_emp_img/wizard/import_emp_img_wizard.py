# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, _
from odoo.exceptions import UserError
import csv
import base64
import xlrd
from odoo.tools import ustr
import requests
import codecs


class ImportEmpImgWizard(models.TransientModel):
    _name = "import.emp.img.wizard"
    _description = "Import Employee Image Wizard"

    import_type = fields.Selection([
        ('csv', 'CSV File'),
        ('excel', 'Excel File')
    ], default="csv", string="Import File Type", required=True)
    file = fields.Binary(string="File", required=True)
    emp_by = fields.Selection([
        ('name', 'Name'),
        ('db_id', 'ID'),
        ('id_no', 'Identification No')
    ], default="name", string="Employee By", required=True)

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

    def import_emp_img_apply(self):

        hr_emp_obj = self.env['hr.employee']
        #perform import lead
        if self and self.file:
            #For CSV
            if self.import_type == 'csv':
                for rec in self:
                    counter = 1
                    skipped_line_no = {}
                    try:
                        file = str(base64.decodebytes(
                            rec.file).decode('utf-8'))
                        myreader = csv.reader(file.splitlines())
                        skip_header = True

                        for row in myreader:
                            try:
                                if skip_header:
                                    skip_header = False
                                    counter = counter + 1
                                    continue

                                if row[0] not in (None, "") and row[1].strip() not in (None, ""):
                                    vals = {}
                                    image_path = row[1].strip()
                                    if "http://" in image_path or "https://" in image_path:
                                        try:
                                            r = requests.get(image_path)
                                            if r and r.content:
                                                image_base64 = base64.encodestring(
                                                    r.content)
                                                vals.update(
                                                    {'image_1920': image_base64})
                                            else:
                                                skipped_line_no[str(
                                                    counter)] = " - URL not correct or check your image size. "
                                                counter = counter + 1
                                                continue
                                        except Exception as e:
                                            skipped_line_no[str(
                                                counter)] = " - URL not correct or check your image size " + ustr(e)
                                            counter = counter + 1
                                            continue

                                    else:
                                        try:
                                            with open(image_path, 'rb') as image:
                                                image.seek(0)
                                                binary_data = image.read()
                                                image_base64 = codecs.encode(
                                                    binary_data, 'base64')
                                                if image_base64:
                                                    vals.update(
                                                        {'image_1920': image_base64})
                                                else:
                                                    skipped_line_no[str(
                                                        counter)] = " - Could not find the image or please make sure it is accessible to this app. "
                                                    counter = counter + 1
                                                    continue
                                        except Exception as e:
                                            skipped_line_no[str(
                                                counter)] = " - Could not find the image or please make sure it is accessible to this app. " + ustr(e)
                                            counter = counter + 1
                                            continue

                                    field_nm = 'name'
                                    if rec.emp_by == 'name':
                                        field_nm = 'name'
                                    elif rec.emp_by == 'db_id':
                                        field_nm = 'id'
                                    elif rec.emp_by == 'id_no':
                                        field_nm = 'identification_id'

                                    search_emp = hr_emp_obj.search(
                                        [(field_nm, '=', row[0])], limit=1)
                                    if search_emp:
                                        search_emp.write(vals)
                                    else:
                                        skipped_line_no[str(
                                            counter)] = " - Employee not found. "

                                    counter = counter + 1
                                else:
                                    skipped_line_no[str(
                                        counter)] = " - Employee or URL/Path field is empty. "
                                    counter = counter + 1
                                    continue

                            except Exception as e:
                                skipped_line_no[str(
                                    counter)] = " - Value is not valid. " + ustr(e)
                                counter = counter + 1
                                continue

                    except Exception as e:
                        raise UserError(
                            _("Sorry, Your csv file does not match with our format " + ustr(e)))

                    if counter > 1:
                        completed_records = (
                            counter - len(skipped_line_no)) - 2
                        res = rec.show_success_msg(
                            completed_records, skipped_line_no)
                        return res

            #For Excel
            if self.import_type == 'excel':
                for rec in self:
                    counter = 1
                    skipped_line_no = {}
                    try:
                        wb = xlrd.open_workbook(
                            file_contents=base64.decodebytes(rec.file))
                        sheet = wb.sheet_by_index(0)
                        skip_header = True
                        for row in range(sheet.nrows):
                            try:
                                if skip_header:
                                    skip_header = False
                                    counter = counter + 1
                                    continue

                                if sheet.cell(row, 0).value not in (None, "") and sheet.cell(row, 1).value.strip() not in (None, ""):
                                    vals = {}
                                    image_path = sheet.cell(
                                        row, 1).value.strip()
                                    if "http://" in image_path or "https://" in image_path:
                                        try:
                                            r = requests.get(image_path)
                                            if r and r.content:
                                                image_base64 = base64.encodestring(
                                                    r.content)
                                                vals.update(
                                                    {'image_1920': image_base64})
                                            else:
                                                skipped_line_no[str(
                                                    counter)] = " - URL not correct or check your image size. "
                                                counter = counter + 1
                                                continue
                                        except Exception as e:
                                            skipped_line_no[str(
                                                counter)] = " - URL not correct or check your image size " + ustr(e)
                                            counter = counter + 1
                                            continue

                                    else:
                                        try:
                                            with open(image_path, 'rb') as image:
                                                image.seek(0)
                                                binary_data = image.read()
                                                image_base64 = codecs.encode(
                                                    binary_data, 'base64')
                                                if image_base64:
                                                    vals.update(
                                                        {'image_1920': image_base64})
                                                else:
                                                    skipped_line_no[str(
                                                        counter)] = " - Could not find the image or please make sure it is accessible to this app. "
                                                    counter = counter + 1
                                                    continue
                                        except Exception as e:
                                            skipped_line_no[str(
                                                counter)] = " - Could not find the image or please make sure it is accessible to this app. " + ustr(e)
                                            counter = counter + 1
                                            continue

                                    search_str = sheet.cell(row, 0).value
                                    field_nm = 'name'
                                    if rec.emp_by == 'name':
                                        field_nm = 'name'
                                    elif rec.emp_by == 'db_id':
                                        field_nm = 'id'
                                        str_id = str(sheet.cell(row, 0).value)
                                        str_id = str_id.split('.', 1)[0]
                                        search_str = int(str_id)

                                    elif rec.emp_by == 'id_no':
                                        field_nm = 'identification_id'

                                    search_emp = hr_emp_obj.search(
                                        [(field_nm, '=', search_str)], limit=1)
                                    if search_emp:
                                        search_emp.write(vals)
                                    else:
                                        skipped_line_no[str(
                                            counter)] = " - Employee not found. "

                                    counter = counter + 1
                                else:
                                    skipped_line_no[str(
                                        counter)] = " - Employee or URL/Path field is empty. "
                                    counter = counter + 1
                                    continue

                            except Exception as e:
                                skipped_line_no[str(
                                    counter)] = " - Value is not valid. " + ustr(e)
                                counter = counter + 1
                                continue

                    except Exception as e:
                        raise UserError(
                            _("Sorry, Your excel file does not match with our format " + ustr(e)))

                    if counter > 1:
                        completed_records = (
                            counter - len(skipped_line_no)) - 2
                        res = rec.show_success_msg(
                            completed_records, skipped_line_no)
                        return res
