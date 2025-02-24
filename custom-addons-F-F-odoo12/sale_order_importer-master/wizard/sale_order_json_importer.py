# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError

import json
import base64
import pathlib

FISCAL_POSITION_IDS = {
    'NATIONAL': 1,
    'INTRACOMUNITARY': 2
}

class SaleOrderJsonImporter(models.TransientModel):

    _name = "sale.order.json.importer"
    _description = "Sale Order JSON Importer"

    json_file_data = fields.Binary(string='File')
    json_file_name = fields.Char(string='JSON File Name')
    json_file_extension = fields.Char(string='JSON File Name')

    @api.multi
    def action_import(self):
        if self._check_json_file_extension():
            decode_json_file = base64.b64decode(self.json_file_data).decode('utf-8')

            try:
                json_sales_data = json.loads(decode_json_file)
                return self.create_sale_order(json_sales_data)
            except ValueError as e:
                raise UserError(_("Error:Decoding JSON file has failed (Error: %s)" %(e)))
        else:
            raise UserError(_("Error: Invalid file format, pleas use .json format"))

    @api.multi
    def create_sale_order(self, sale_order_dict):
        """
            Create sale order from dictionary data
            :param sale_order_dict: Dictonary with data of new sale_order
            :return:
        """
        sale_partner_customer = self._get_res_partner(sale_order_dict.get("customer"), sale_order_dict.get("fiscal_position"))

        sale_order = self.env['sale.order'].create({
            'partner_id': sale_partner_customer.id
        })
        """ Range order Lines"""
        for so_line in sale_order_dict.get("orderLines"):
            self.create_sale_order_line(so_line, sale_order.id)

        sale_order.write({'state': 'sale'})

    @api.multi
    def create_sale_order_line(self, sale_order_line_data, sale_order_id):
        """
        :param sale_order_line:
        :param sale_order_id:
        :return:
        """
        self.ensure_one()
        product = self._get_product(sale_order_line_data.get("orderProduct"))

        so_line_data = {
            'order_id': sale_order_id,
            'price_unit': sale_order_line_data.get("unitPrice"),
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_uom_qty': sale_order_line_data.get("quantity")
        }

        return self.env['sale.order.line'].create(so_line_data)


    @api.multi
    def _get_res_partner(self, res_partner_data, fiscal_position):
        """
            Search if partner already exists using name, NIF and email.
            Create res_partner if not exists
            :param res_partner_data_dir:
            :param fiscal_position:
            :return: res_partner id
        """
        res_country = False
        if res_partner_data.get("companyName"):
            sale_partner = self.env['res.partner'].search([('name', '=', res_partner_data.get("companyName"))])
        elif res_partner_data.get("NIF"):
            sale_partner = self.env['res.partner'].search([('vat', '=', res_partner_data.get("NIF"))])
        elif res_partner_data.get("email"):
            sale_partner = self.env['res.partner'].search([('email', '=', res_partner_data.get("email"))])

        if not sale_partner:
            if res_partner_data.get("country"):
                res_country = self.env['res.country'].search([('code', '=', res_partner_data.get("country"))])

            new_partner_data = {
                'street2': res_partner_data.get("additionalStreet") if res_partner_data.get("additionalStreet") else None,
                'city': res_partner_data.get("city") if res_partner_data.get("city") else None,
                'name': res_partner_data.get("companyName") if res_partner_data.get("companyName") else "",
                'country_id': res_country.id,
                'is_company': True if res_partner_data.get("customerType") == "COMPANY" else False,
                'email': res_partner_data.get("email") if res_partner_data.get("email") else None,
                'mobile': res_partner_data.get("mobilePhone") if res_partner_data.get("mobilePhone") else None,
                'phone': res_partner_data.get("phone") if res_partner_data.get("phone") else None,
                'zip': res_partner_data.get("postalCode") if res_partner_data.get("postalCode") else None,
                'street': res_partner_data.get("street") if res_partner_data.get("street") else None,
                'vat': res_partner_data.get("NIF") if res_partner_data.get("NIF") else None,
                'property_account_position_id': FISCAL_POSITION_IDS.get(fiscal_position) if fiscal_position else None
            }

            sale_partner = self.env['res.partner'].create(new_partner_data)

        return sale_partner

    @api.multi
    def _get_product(self, product_data_dir):
        """
            Make sure if product already exists create it if not
            :return: product_product id
        """
        if product_data_dir.get("sku"):
            product = self.env['product.product'].search([('default_code', '=', product_data_dir.get("sku"))])

        if not product:
            """Ensure product default_code"""
            if product_data_dir.get("sku"):
                product_default_code = product_data_dir.get("sku")
            else:
                product_default_code = product_data_dir.get("name") + '_' + self.env['product.product'].sequence_id

            product = self.env['product.product'].create({
                'name': product_data_dir.get("name") if product_data_dir.get("name") else None,
                'default_code': product_default_code
            })

            """Set product type on product template"""
            if product_data_dir.get("type") == 'PRODUCT':
                product.product_tmpl_id.write({'type': 'consu'})
            else:
                product.product_tmpl_id.write({'type': 'service'})

        return product

    @api.multi
    def _check_json_file_extension(self):
        """
            Check up on file extension is .json
            :return: True if file extension is .json, False if not
        """
        self.json_file_extension = pathlib.Path(self.json_file_name).suffix
        return str(self.json_file_extension) == '.json'
