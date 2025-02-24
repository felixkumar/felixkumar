# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, _
from odoo.exceptions import UserError
import base64
from zipfile import ZipFile
import io
from odoo.tools import ustr
import os
import codecs


class ShImportImgZip(models.TransientModel):
    _name = "sh.iiz.import.img.zip.wizard"
    _description = "Import Images from zip file"

    zip_file = fields.Binary(string="Zip File", required=True)
    img_for = fields.Selection([
        ('product', "Product"),
        ('partner', "Partner"),
        ("employee", "Employee"),
    ], default="product", string="Images For", required=True)

    product_by = fields.Selection([
        ('name', 'Name'),
        ('default_code', 'Internal Reference'),
        ('barcode', 'Barcode'),
        ('id', 'ID'),
    ], default="name", string="Product By")

    product_model = fields.Selection([
        ('pro_tmpl', 'Product Template'),
        ('pro_var', 'Product Variants'),
    ], default="pro_tmpl", string="Product Model")

    partner_by = fields.Selection([
        ('name', 'Name'),
        ('ref', 'Internal Reference'),
        ('id', 'ID')
    ], default="name", string="Partner By")

    employee_by = fields.Selection([
        ('name', 'Name'),
        ('id', 'ID'),
        ('identification_id', 'Identification No')
    ], default="name", string="Employee By")

    def show_success_msg(self, counter, skipped_images_dic):
        #open the new success message box
        view = self.env.ref('sh_message.sh_message_wizard')
        context = dict(self._context or {})
        dic_msg = str(counter) + " Images imported successfully"
        if skipped_images_dic:
            dic_msg = dic_msg + "\nNote:"
        for k, v in skipped_images_dic.items():
            dic_msg = dic_msg + "\nImage name " + k + " " + v + " "
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

    def button_import(self):
        if self and self.zip_file:

            #choose specific model and field name  based on selection.
            model_obj = ""
            field_name = ""
            skipped_images_dic = {}
            if self.img_for == 'partner':
                model_obj = self.env['res.partner']
                field_name = self.partner_by

            elif self.img_for == 'employee':
                model_obj = self.env['hr.employee']
                field_name = self.employee_by

            elif self.img_for == 'product':
                field_name = self.product_by

                if self.product_model == 'pro_var':
                    model_obj = self.env['product.product']
                elif self.product_model == 'pro_tmpl':
                    model_obj = self.env['product.template']

            base64_data_file = base64.b64decode(self.zip_file)
            try:
                with ZipFile(io.BytesIO(base64_data_file), 'r') as archive:
                    folder_inside_zip_name = ""
                    counter = 0
                    for file_name in archive.namelist():
                        try:
                            img_data = archive.read(file_name)
                            if len(img_data) == 0:
                                folder_inside_zip_name = file_name
                                continue
                            if img_data:
                                img_name_with_ext = ""
                                if folder_inside_zip_name != "":
                                    img_name_with_ext = file_name.replace(
                                        folder_inside_zip_name, "")
                                    just_img_name = ""
                                    if img_name_with_ext != "":
                                        just_img_name = os.path.splitext(
                                            img_name_with_ext)[0]
                                        if just_img_name != "" and model_obj != "" and field_name != "":
                                            search_record = model_obj.sudo().search([
                                                (field_name, '=', just_img_name)
                                            ], limit=1)
                                            if search_record:
                                                image_base64 = codecs.encode(
                                                    img_data, 'base64')
                                                search_record.sudo().write({
                                                    'image_1920': image_base64,
                                                })
                                                counter += 1
                                            else:
                                                skipped_images_dic[img_name_with_ext] = " - Record not found for this image " + \
                                                    img_name_with_ext
                                        else:
                                            skipped_images_dic[img_name_with_ext] = " - Record not found for this image " + \
                                                img_name_with_ext
                                    else:
                                        skipped_images_dic[img_name_with_ext] = " - Image name not resolve for this image " + file_name
                                else:
                                    skipped_images_dic[img_name_with_ext] = " - Zip file have no any folder inside it "
                            else:
                                skipped_images_dic[img_name_with_ext] = " - Image data not found for this image " + file_name

                        except Exception as e:
                            skipped_images_dic[file_name] = " - Value is not valid. " + ustr(
                                e)
                            continue

                    #show success message here.
                    res = self.show_success_msg(counter, skipped_images_dic)
                    return res

            except Exception as e:
                msg = "Something went wrong - " + ustr(e)
                raise UserError(_(msg))
