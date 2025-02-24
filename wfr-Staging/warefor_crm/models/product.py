# -*- coding: utf-8 -*-

import qrcode
import base64

from io import BytesIO
from odoo import api, models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Fields as product development
    ###########################
    # General Page
    date = fields.Date(string="Date", tracking=True)
    item_number = fields.Char(string="Our Item Number", tracking=True)
    upc = fields.Char(string="UPC Code", tracking=True)
    ean_gtin_number = fields.Char(string="EAN-13 / GTIN-13", tracking=True)
    pallet_gtin = fields.Char(string="Pallet GTIN", tracking=True)
    description = fields.Text(string="Description", tracking=True)
    customer_m2m_ids = fields.Many2many("res.partner", string="Customer Name")
    vendor_no = fields.Char("Our Vendor Number")
    department_no = fields.Char("Department Number")
    item_customer_number = fields.Char(string="Customer Item Number", tracking=True)
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')

    qrcode = fields.Binary(string="QR Code", compute="_compute_qrcode")

    brand = fields.Char(string="Brand", tracking=True)
    manufacturer = fields.Many2one(comodel_name="res.partner", string="Manufacturer", required=False, )

    # Product Dimension
    item_size_in = fields.Float("Items Size(In)")
    item_size_cm = fields.Float("Items Size(Cm)")
    item_capacity_cm = fields.Float("Items Capacity(Qt)")
    item_capacity_l = fields.Float("Items Capacity(L)")
    # Unit of Sale Dimensions
    usd_length_in = fields.Float("Length(In)")
    usd_length_cm = fields.Float("Length(cm)")
    usd_width_in = fields.Float("Width(In)")
    usd_width_cm = fields.Float("Width(cm)")
    usd_height_in = fields.Float("Height(In)")
    usd_height_cm = fields.Float("Height(cm)")
    usd_cube_lbs = fields.Float("Cube(Culn)")
    usd_cube_cm = fields.Float("Cube(cm3)")
    # Unit of Sale Weight
    usw_lbs = fields.Float("Unit Of Sale Weight(lbs)")
    usw_kg = fields.Float("Unit Of Sale Weight(Kg)")

    ###########################
    @api.depends('name', 'categ_id', 'default_code', 'barcode', 'date', 'list_price', 'item_number', 'upc',
                 'description', 'vendor_no', 'qty_available')
    def _compute_qrcode(self):
        for product in self:
            input_data = "Product Details\n" + "=" * 15
            input_data += "\nName: " + product.name if product.name else ''
            input_data += "\nCategory: " + product.categ_id.name if product.categ_id else ''
            input_data += "\nSKU: " + product.default_code if product.default_code else ''
            input_data += "\nBarcode: " + product.barcode if product.barcode else ''
            input_data += "\nDate: " + str(product.date) if product.date else ''
            input_data += "\nSales Price: " + str(product.list_price) if product.list_price else ''
            input_data += "\nItem Number: " + str(product.item_number) if product.item_number else ''
            input_data += "\nUPC: " + product.upc if product.upc else ''
            input_data += "\nDescription: " + product.description if product.description else ''
            input_data += "\nVendor No: " + product.vendor_no if product.vendor_no else ''
            input_data += "\nQTY On hand: " + str(product.qty_available) if product.qty_available else ''
            qr = qrcode.QRCode(version=1, box_size=4, border=5)
            qr.add_data(input_data)
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            data = BytesIO()
            img.save(data, optimise=True, format='PNG')
            product.qrcode = base64.b64encode(data.getvalue()).decode()
