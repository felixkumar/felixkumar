# -*- coding: utf-8 -*-

import base64
import math
import os
import xlsxwriter
import qrcode

from io import BytesIO
from PIL import Image
from odoo import api, models, fields, _


class ProductDevelopment(models.Model):
    _name = 'product.development'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Product Development"
    _rec_name = 'product_id'

    # Added new fields
    ###########################
    # General Page
    date = fields.Date(string="Date", tracking=True)
    item_number = fields.Char(string="Our Item Number", tracking=True)
    upc = fields.Char(string="UPC Code", tracking=True)
    description = fields.Text(string="Description", tracking=True)
    customer_m2m_ids = fields.Many2many("res.partner", string="Customer Name")
    vendor_no = fields.Char("Our Vendor Number")
    department_no = fields.Char("Department Number")
    item_customer_number = fields.Integer(string="Customer Item Number", tracking=True)
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')

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

    # Packaging Dimension
    packaging_width_ds = fields.Float(string="Width", help=_("Width(W) in inches for DS - Packaging Dimensions"),
                                      digits=(12, 3), tracking=True)
    packaging_width_ds_cm = fields.Float(string="Width", help=_("Width(W) in centimeter for DS - Packaging Dimensions"),
                                         digits=(12, 3), tracking=True)
    packaging_width_re = fields.Float(string="Width", help=_("Width(W) in inches for RETAIL - Packaging Dimensions"),
                                      digits=(12, 3), tracking=True)
    packaging_width_re_cm = fields.Float(string="Width", help=_("Width(W) in CM for RETAIL - Packaging Dimensions"),
                                         digits=(12, 3), tracking=True)
    packaging_length_ds = fields.Float(string="Length", help=_("Length(L) in inches for DS - Packaging Dimensions"),
                                       digits=(12, 3), tracking=True)
    packaging_length_ds_cm = fields.Float(string="Length",
                                          help=_("Length(L) in centimeter for DS - Packaging Dimensions"),
                                          digits=(12, 3), tracking=True)
    packaging_length_re = fields.Float(string="Length", help=_("Length(L) in inches for RETAIL - Packaging Dimensions"),
                                       digits=(12, 3), tracking=True)
    packaging_length_re_cm = fields.Float(string="Length",
                                          help=_("Length(L) in centimeter for RETAIL - Packaging Dimensions"),
                                          digits=(12, 3), tracking=True)
    packaging_height_ds = fields.Float(string="Height", help=_("Height(H) in inches for DS - Packaging Dimensions"),
                                       digits=(12, 3), tracking=True)
    packaging_height_ds_cm = fields.Float(string="Height",
                                          help=_("Height(H) in centimeter for DS - Packaging Dimensions"),
                                          digits=(12, 3), tracking=True)
    packaging_height_re = fields.Float(string="Height", help=_("Height(H) in inches for RETAIL - Packaging Dimensions"),
                                       digits=(12, 3), tracking=True)
    packaging_height_re_cm = fields.Float(string="Height", help=_("Height(H) in CM for RETAIL - Packaging Dimensions"),
                                          digits=(12, 3), tracking=True)
    packaging_cube_ds = fields.Float(string="Cube", help=_("Cube Feet^3 for DS - Packaging Dimensions"),
                                     digits=(12, 3), tracking=True)
    packaging_cube_ds_m3 = fields.Float(string="Cube", help=_("Cube in m3 for DS - Packaging Dimensions"),
                                        digits=(12, 3), tracking=True)
    packaging_cube_re = fields.Float(string="Cube", help=_("Cubic Inch(CuIn) for RETAIL - Packaging Dimensions"),
                                     digits=(12, 3), tracking=True)
    packaging_cube_re_m3 = fields.Float(string="Cube", help=_("Cube in m^3 for RETAIL - Packaging Dimensions"),
                                        digits=(12, 3), tracking=True)
    packaging_weight_ds = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                                       help="Weight in LBS for DS - Packaging Dimensions")
    packaging_weight_ds_kg = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                                          help="Weight in KG for DS - Packaging Dimensions")
    packaging_weight_re = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                                       help="Weight in Lbs for RETAIL - Packaging Dimensions")
    packaging_weight_re_kg = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                                          help="Weight in KG for RETAIL - Packaging Dimensions")

    case_pack_qty = fields.Float(string="Case Pack Quantity", tracking=True,
                                 help="Units/Case qty for RETAIL - Case Pack  Dimensions")

    case_pack_height = fields.Float(string="Height", help=_("Height(H) in inches for RETAIL - Case Pack  Dimensions"),
                                    digits=(12, 3), tracking=True)
    case_pack_height_cm = fields.Float(string="Height",
                                       help=_("Height(H) in centimeter for RETAIL - Case Pack  Dimensions"),
                                       digits=(12, 3), tracking=True, compute="_compute_case_pack_height_cm")
    case_pack_length = fields.Float(string="Length", help=_("Length(L) in inches for RETAIL - Case Pack  Dimensions"),
                                    digits=(12, 3), tracking=True)
    case_pack_length_cm = fields.Float(string="Length",
                                       help=_("Length(L) in inches for RETAIL - Case Pack  Dimensions"),
                                       digits=(12, 3), tracking=True, compute="_compute_case_pack_length_cm")
    case_pack_width = fields.Float(string="Width", help=_("Width(W) in inches for RETAIL - Case Pack  Dimensions"),
                                   digits=(12, 3), tracking=True)
    case_pack_width_cm = fields.Float(string="Width",
                                      help=_("Width(W) in centimeter for RETAIL - Case Pack  Dimensions"),
                                      digits=(12, 3), tracking=True, compute="_compute_case_pack_width_cm")
    case_pack_cube = fields.Float(string="Cube", help=_("Cube in F^3 for RETAIL - Case Pack  Dimensions"),
                                  digits=(12, 3), tracking=True, compute="_compute_case_pack_cube")
    case_pack_cube_m3 = fields.Float(string="Cube", help=_("Cube in m^3 for RETAIL - Case Pack  Dimensions"),
                                     digits=(12, 3), tracking=True, compute='_compute_case_pack_cube_m3')
    case_pack_weight = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                                    help="Weight in Lbs for RETAIL - Case Pack  Dimensions")
    case_pack_weight_kg = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                                       help="Weight in KG for RETAIL - Case Pack  Dimensions",
                                       compute='_compute_case_pack_weight_kg')

    retail_pallet_length = fields.Float(string="Length", help=_("Length(L) in inches for RETAIL Pallet  Dimensions"),
                                        digits=(12, 3), tracking=True)
    retail_pallet_length_cm = fields.Float(string="Length", help=_("Length(L) in cm for RETAIL Pallet  Dimensions"),
                                           digits=(12, 3), tracking=True)
    retail_pallet_width = fields.Float(string="Width", help=_("Width(W) in inches for RETAIL Pallet  Dimensions"),
                                       digits=(12, 3), tracking=True)
    retail_pallet_width_cm = fields.Float(string="Width", help=_("Width(W) in cm for RETAIL Pallet  Dimensions"),
                                          digits=(12, 3), tracking=True)
    retail_pallet_height = fields.Float(string="Height", help=_("Height(H) in inches for RETAIL Pallet  Dimensions"),
                                        digits=(12, 3), tracking=True)
    retail_pallet_height_cm = fields.Float(string="Height", help=_("Height(H) in cm for RETAIL Pallet  Dimensions"),
                                           digits=(12, 3), tracking=True)
    retail_pallet_cube = fields.Float(string="Cube", help=_("Cube in F^3 for RETAIL Pallet  Dimensions"),
                                      digits=(12, 3), tracking=True)
    retail_pallet_cube_m3 = fields.Float(string="Cube", help=_("Cube in m^3 for RETAIL Pallet  Dimensions"),
                                         digits=(12, 3), tracking=True)
    retail_pallet_weight = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                                        help="Weight in Lbs for RETAIL Pallet  Dimensions")
    retail_pallet_weight_kg = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                                           help="Weight in KG for RETAIL Pallet  Dimensions",
                                           compute='_compute_retail_pallet_weight_kg')

    # Logistics
    vendor_number = fields.Char(string="Vendor No", help="Vendor No. (Logistics)")
    vendor_name = fields.Char(string="Vendor Name", help="Vendor Name")
    vendor_item_number = fields.Char(string="Vendor Item No", help="Vendor Item Number")
    fob_port_export_cost = fields.Float(string="FOB Port of Export Cost", default=0.0)
    country_of_origin = fields.Many2one('res.country', string="Country of Origin")
    hts_code = fields.Char(string="HTS Code")
    duty_rate = fields.Float(string="Duty Rate %")
    duty_cost_calculation = fields.Float(string="Duty Cost Calculation $")
    import_cost_calculation = fields.Float(string="Import Cost Calculation $")
    logistic_cost_calculation = fields.Float(string="Logistic Cost Calculation $")
    minimum_order_qty = fields.Float(string="Minimum Order Quantity")
    vendor_case_pack_qty = fields.Float(string="Vendor Case Pack Quantity")
    vendor_case_pack_height = fields.Float(string="Height",
                                           help=_("Height(H) in inches for RETAIL - Vendor Case Pack  Dimensions"),
                                           digits=(12, 3), tracking=True)
    vendor_case_pack_height_cm = fields.Float(string="Height",
                                              help=_(
                                                  "Height(H) in centimeter for RETAIL - Vendor Case Pack  Dimensions"),
                                              digits=(12, 3), tracking=True)
    vendor_case_pack_length = fields.Float(string="Length",
                                           help=_("Length(L) in inches for RETAIL - Vendor Case Pack  Dimensions"),
                                           digits=(12, 3), tracking=True)
    vendor_case_pack_length_cm = fields.Float(string="Length",
                                              help=_("Length(L) in inches for RETAIL - Vendor Case Pack  Dimensions"),
                                              digits=(12, 3), tracking=True)
    vendor_case_pack_width = fields.Float(string="Width",
                                          help=_("Width(W) in inches for RETAIL - Vendor Case Pack  Dimensions"),
                                          digits=(12, 3), tracking=True)
    vendor_case_pack_width_cm = fields.Float(string="Width",
                                             help=_("Width(W) in centimeter for RETAIL - Vendor Case Pack  Dimensions"),
                                             digits=(12, 3), tracking=True)
    vendor_case_pack_cube = fields.Float(string="Cube", help=_("Cube in F^3 for RETAIL - Vendor Case Pack  Dimensions"),
                                         digits=(12, 3), tracking=True)
    vendor_case_pack_cube_m3 = fields.Float(string="Cube",
                                            help=_("Cube in m^3 for RETAIL - Vendor Case Pack  Dimensions"),
                                            digits=(12, 3), tracking=True)
    vendor_case_pack_weight = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                                           help="Weight in Lbs for RETAIL - Vendor Case Pack  Dimensions")
    vendor_case_pack_weight_kg = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                                              help="Weight in KG for RETAIL - Vendor Case Pack  Dimensions")
    # pap = Put Away Pallet
    pap_qty = fields.Float(string="Put Away Pallet Quantity (Units)")
    pap_length = fields.Float(string="Length", help=_("Length(L) in inches for Put Away Pallet  Dimensions"),
                              digits=(12, 3), tracking=True)
    pap_length_cm = fields.Float(string="Length", help=_("Length(L) in cm for Put Away Pallet  Dimensions"),
                                 digits=(12, 3), tracking=True)
    pap_width = fields.Float(string="Width", help=_("Width(W) in inches for Put Away Pallet  Dimensions"),
                             digits=(12, 3), tracking=True)
    pap_width_cm = fields.Float(string="Width", help=_("Width(W) in cm for Put Away Pallet  Dimensions"),
                                digits=(12, 3), tracking=True)
    pap_height = fields.Float(string="Height", help=_("Height(H) in inches for Put Away Pallet  Dimensions"),
                              digits=(12, 3), tracking=True)
    pap_height_cm = fields.Float(string="Height", help=_("Height(H) in cm for Put Away Pallet  Dimensions"),
                                 digits=(12, 3), tracking=True)
    pap_cube = fields.Float(string="Cube", help=_("Cube in F^3 for Put Away Pallet  Dimensions"),
                            digits=(12, 3), tracking=True)
    pap_cube_m3 = fields.Float(string="Cube", help=_("Cube in m^3 for Put Away Pallet  Dimensions"),
                               digits=(12, 3), tracking=True)
    pap_weight = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                              help="Weight in Lbs for Put Away Pallet  Dimensions")
    pap_weight_kg = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                                 help="Weight in KG for Put Away Pallet  Dimensions")

    # rpl = Retail Pallet Logistic
    rpl_qty = fields.Float(string="Retail Pallet Quantity (Units)")
    rpl_length = fields.Float(string="Length", help=_("Length(L) in inches for Retail Pallet (Logistic)  Dimensions"),
                              digits=(12, 3), tracking=True)
    rpl_length_cm = fields.Float(string="Length", help=_("Length(L) in cm for Retail Pallet (Logistic)  Dimensions"),
                                 digits=(12, 3), tracking=True)
    rpl_width = fields.Float(string="Width", help=_("Width(W) in inches for Retail Pallet (Logistic)  Dimensions"),
                             digits=(12, 3), tracking=True)
    rpl_width_cm = fields.Float(string="Width", help=_("Width(W) in cm for Retail Pallet (Logistic)  Dimensions"),
                                digits=(12, 3), tracking=True)
    rpl_height = fields.Float(string="Height", help=_("Height(H) in inches for Retail Pallet (Logistic)  Dimensions"),
                              digits=(12, 3), tracking=True)
    rpl_height_cm = fields.Float(string="Height", help=_("Height(H) in cm for Retail Pallet (Logistic)  Dimensions"),
                                 digits=(12, 3), tracking=True)
    rpl_cube = fields.Float(string="Cube", help=_("Cube in F^3 for Retail Pallet (Logistic)  Dimensions"),
                            digits=(12, 3), tracking=True)
    rpl_cube_m3 = fields.Float(string="Cube", help=_("Cube in m^3 for Retail Pallet (Logistic)  Dimensions"),
                               digits=(12, 3), tracking=True)
    rpl_weight = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                              help="Weight in Lbs for Retail Pallet (Logistic)  Dimensions")
    rpl_weight_kg = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                                 help="Weight in KG for Retail Pallet (Logistic)  Dimensions")
    # 20 FT Container Load Quantity, c20ft = 20 FT Container
    c20ft_cuft = fields.Float(string="Cube (CuFt)", help=_("Cube(Cuft) Cube & Payload for 20FT Container"),
                              digits=(12, 3), tracking=True)
    c20ft_cuft_m = fields.Float(string="Cube (m3)", help=_("Cube(m3) Cube & Payload for 20FT Container"),
                                digits=(12, 3), tracking=True)
    c20ft_weight_lbs = fields.Float(string="Weight (lbs)", help=_("weight(Lbs) Actual Payload for 20FT Container"),
                                    digits=(12, 3), tracking=True)
    c20ft_weight_kg = fields.Float(string="Weight (kg)", help=_("weight(kg) Actual Payload for 20FT Container"),
                                   digits=(12, 3), tracking=True)
    c20ft_freight_cost_per = fields.Float(digits=(12, 2), string="Ocean Freight Cost %", tracking=True,
                                      help="Ocean Freight Cost for 20 FT Container")
    c20ft_freight_cost = fields.Float(digits=(12, 2), string="Ocean Freight Cost $", tracking=True,
                                      help="Ocean Freight Cost for 20 FT Container")
    # 40 FT Container Load Quantity, c40ft = 40 FT Container
    c40ft_cuft = fields.Float(string="Cube (CuFt)", help=_("Cube(Cuft) Cube & Payload for 40FT Container"),
                              digits=(12, 3), tracking=True)
    c40ft_cuft_m = fields.Float(string="Cube (m3)", help=_("Cube(m3) Cube & Payload for 40FT Container"),
                                digits=(12, 3), tracking=True)
    c40ft_weight_lbs = fields.Float(string="Weight (lbs)", help=_("weight(Lbs) Actual Payload for 40FT Container"),
                                    digits=(12, 3), tracking=True)
    c40ft_weight_kg = fields.Float(string="Weight (kg)", help=_("weight(kg) Actual Payload for 40FT Container"),
                                   digits=(12, 3), tracking=True)
    c40ft_freight_cost_per = fields.Float(digits=(12, 2), string="Ocean Freight Cost %", tracking=True,
                                          help="Ocean Freight Cost for 40 FT Container")
    c40ft_freight_cost = fields.Float(digits=(12, 2), string="Ocean Freight Cost $", tracking=True,
                                      help="Ocean Freight Cost for 40 FT Container")
    # 40 FT HC Container Load Quantity, c40hcft = 40 FT HC Container
    c40hcft_cuft = fields.Float(string="Cube (CuFt)", help=_("Cube(Cuft) Cube & Payload for 40FT HC Container"),
                              digits=(12, 3), tracking=True)
    c40hcft_cuft_m = fields.Float(string="Cube (m3)", help=_("Cube(m3) Cube & Payload for 40FT HC Container"),
                                digits=(12, 3), tracking=True)
    c40hcft_weight_lbs = fields.Float(string="Weight (lbs)", help=_("weight(Lbs) Actual Payload for 40FT HC Container"),
                                    digits=(12, 3), tracking=True)
    c40hcft_weight_kg = fields.Float(string="Weight (kg)", help=_("weight(kg) Actual Payload for 40FT HC Container"),
                                   digits=(12, 3), tracking=True)
    c40hcft_freight_cost_per = fields.Float(digits=(12, 2), string="Ocean Freight Cost %", tracking=True,
                                          help="Ocean Freight Cost for 40 FT HC Container")
    c40hcft_freight_cost = fields.Float(digits=(12, 2), string="Ocean Freight Cost $", tracking=True,
                                      help="Ocean Freight Cost for 40 FT HC Container")
    # 45 FT Container Load Quantity, c45ft = 45 FT Container
    c45ft_cuft = fields.Float(string="Cube (CuFt)", help=_("Cube(Cuft) Cube & Payload for 45FT Container"),
                                digits=(12, 3), tracking=True)
    c45ft_cuft_m = fields.Float(string="Cube (m3)", help=_("Cube(m3) Cube & Payload for 45FT Container"),
                                  digits=(12, 3), tracking=True)
    c45ft_weight_lbs = fields.Float(string="Weight (lbs)", help=_("weight(Lbs) Actual Payload for 45FT Container"),
                                      digits=(12, 3), tracking=True)
    c45ft_weight_kg = fields.Float(string="Weight (kg)", help=_("weight(kg) Actual Payload for 45FT Container"),
                                     digits=(12, 3), tracking=True)
    c45ft_freight_cost_per = fields.Float(digits=(12, 2), string="Ocean Freight Cost %", tracking=True,
                                            help="Ocean Freight Cost for 45 FT Container")
    c45ft_freight_cost = fields.Float(digits=(12, 2), string="Ocean Freight Cost $", tracking=True,
                                        help="Ocean Freight Cost for 45 FT Container")
    # 48 FT Truck (Dry Van ) Load Quantity, t48ft = 48 FT Truck
    t48ft_cuft = fields.Float(string="Cube (CuFt)", help=_("Cube(Cuft) Cube & Payload for 48FT Truck"),
                                digits=(12, 3), tracking=True)
    t48ft_cuft_m = fields.Float(string="Cube (m3)", help=_("Cube(m3) Cube & Payload for 48FT Truck"),
                                  digits=(12, 3), tracking=True)
    t48ft_weight_lbs = fields.Float(string="Weight (lbs)", help=_("weight(Lbs) Actual Payload for 48FT Truck"),
                                      digits=(12, 3), tracking=True)
    t48ft_weight_kg = fields.Float(string="Weight (kg)", help=_("weight(kg) Actual Payload for 48FT Truck"),
                                     digits=(12, 3), tracking=True)
    t48ft_freight_cost_per = fields.Float(digits=(12, 2), string="Domestic Freight Cost %", tracking=True,
                                            help="Domestic Freight Cost for 48FT Truck")
    t48ft_freight_cost = fields.Float(digits=(12, 2), string="Domestic Freight Cost $", tracking=True,
                                        help="Domestic Freight Cost for 48FT Truck")
    # 58 FT Truck (Dry Van ) Load Quantity, t58ft = 58 FT Truck
    t58ft_cuft = fields.Float(string="Cube (CuFt)", help=_("Cube(Cuft) Cube & Payload for 58FT Truck"),
                              digits=(12, 3), tracking=True)
    t58ft_cuft_m = fields.Float(string="Cube (m3)", help=_("Cube(m3) Cube & Payload for 58FT Truck"),
                                digits=(12, 3), tracking=True)
    t58ft_weight_lbs = fields.Float(string="Weight (lbs)", help=_("weight(Lbs) Actual Payload for 58FT Truck"),
                                    digits=(12, 3), tracking=True)
    t58ft_weight_kg = fields.Float(string="Weight (kg)", help=_("weight(kg) Actual Payload for 58FT Truck"),
                                   digits=(12, 3), tracking=True)
    t58ft_freight_cost_per = fields.Float(digits=(12, 2), string="Domestic Freight Cost %", tracking=True,
                                          help="Domestic Freight Cost for 58FT Truck")
    t58ft_freight_cost = fields.Float(digits=(12, 2), string="Domestic Freight Cost $", tracking=True,
                                      help="Domestic Freight Cost for 58FT Truck")

    ###########################

    @api.depends('product_id', 'date', 'stage_id', 'item_number', 'payment_term_id', 'item_customer_number',
                 'department_no', 'vendor_no')
    def _compute_qrcode(self):
        for pd in self:
            input_data = "Product Development Details\n" + "="*27
            input_data += "\nName: " + pd.product_id.name if pd.product_id else ''
            input_data += "\nDate: " + str(pd.date) if pd.date else ''
            input_data += "\nItem Number: " + str(pd.item_number) if pd.item_number else ''
            input_data += "\nUPC: " + pd.upc if pd.upc else ''
            input_data += "\nDescription: " + pd.description if pd.description else ''
            input_data += "\nVendor No: " + pd.vendor_no if pd.vendor_no else ''
            input_data += "\nDepartment No: " + pd.department_no if pd.department_no else ''
            input_data += "\nCustomer Item No: " + str(pd.item_customer_number) if pd.item_customer_number else ''
            input_data += "\nPayment Terms: " + pd.payment_term_id.name if pd.payment_term_id else ''
            qr = qrcode.QRCode(version=1, box_size=4, border=5)
            qr.add_data(input_data)
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            data = BytesIO()
            img.save(data, optimise=True, format='PNG')
            pd.qrcode = base64.b64encode(data.getvalue()).decode()

    product_id = fields.Many2one('product.product', string="Product", tracking=True)
    qrcode = fields.Binary(string="QR Code", compute="_compute_qrcode")
    image = fields.Binary(string="Image", tracking=True)
    prepared_by = fields.Many2one('res.partner', string="Prepared By", tracking=True)
    location_id = fields.Many2one('stock.location', string="Store Location", tracking=True)
    stage_id = fields.Many2one('product.development.state', string='Stage', tracking=True)

    item_mfr_number = fields.Char(string="MFR Item Number", tracking=True)
    item_mfr_name = fields.Char(string="MFR Item Name", tracking=True)
    item_customer_name = fields.Char(string="Customer Item Name", tracking=True)
    item_unit_of_sale = fields.Integer(string="Unit of Sale", tracking=True)
    item_cost = fields.Float(string="Cost", tracking=True)
    item_composition = fields.Binary(string="Composition", tracking=True)
    item_product_specifications = fields.Binary(string="Product Specifications", tracking=True)
    item_review_date = fields.Date(string="Review Date", tracking=True)
    item_approval_date = fields.Date(string="Approval Date", tracking=True)
    item_presentation_date = fields.Date(string="Presentation Date", tracking=True)
    item_minimum_order_qty = fields.Date(string="Minimum Order Quantity", tracking=True)
    production_starting_date = fields.Date(string="Production Starting Date")
    item_etd = fields.Char(string="ETD")
    item_eta = fields.Char(string="ETA")
    item_shipping_date = fields.Date(string="Shipping Date")
    in_store_date = fields.Date(string="In Store Date")

    material = fields.Char(string="Material", tracking=True)
    brand = fields.Char(string="Brand", tracking=True)
    brand_register_type = fields.Selection(
        selection=[('tm', 'Trademark'), ('registered', 'R'), ('copyright', 'Copyright'), ('etc', 'etc')],
        string="Brand Register Type", tracking=True)
    made_by = fields.Many2one('res.partner', string="Made By", tracking=True)
    made_in = fields.Many2one('res.country', string="Made In", tracking=True)
    comments = fields.Char(string="Comments", tracking=True)
    retail_price = fields.Float(string="Retail Price", digits=(12, 3), tracking=True)
    # retail_price = fields.Char(string="Retail Price")
    pc = fields.Integer(string="PC", tracking=True)
    selling_features = fields.Text(string="Selling Features", tracking=True)
    model = fields.Char(string="Model", tracking=True)
    packaging_qty = fields.Float(string="QTY", tracking=True)

    @api.depends('pa_sp_width_unit', 'pa_sp_height_unit', 'pa_sp_length_unit')
    def _compute_pa_sp_total_unit(self):
        self.pa_sp_total_unit = self.pa_sp_height_unit * self.pa_sp_length_unit * self.pa_sp_width_unit

    pa_sp_total_unit = fields.Float(string="Total Units", tracking=True,
                                    help="Total Units for PUT AWAY - Standard Pallet",
                                    compute="_compute_pa_sp_total_unit")
    r_sp_total_unit = fields.Float(string="Total Units", tracking=True, help="Total Units for RETAIL- Standard Pallet")
    r_cp_total_unit = fields.Float(string="Total Units", tracking=True, help="Total Units for RETAIL - CHEP Pallet")

    @api.depends('pa_cp_height_unit', 'pa_cp_length_unit', 'pa_cp_width_unit')
    def _compute_pa_cp_total_unit(self):
        self.pa_cp_total_unit = self.pa_cp_length_unit * self.pa_cp_width_unit * self.pa_cp_height_unit

    pa_cp_total_unit = fields.Float(string="Total Units", tracking=True, help="Total Units for PUT AWAY - CHEP Pallet",
                                    compute="_compute_pa_cp_total_unit")
    packaging_weight = fields.Float(string="Weight", digits=(12, 3), tracking=True)
    packaging_weight_net = fields.Float(string="Net Weight", digits=(12, 3), tracking=True)
    packaging_weight_net_ds = fields.Float(string="Net Weight", digits=(12, 3), tracking=True,
                                           help="Net Weight for DS - Packaging Dimensions")
    packaging_weight_net_ds_kg = fields.Float(string="Net Weight", digits=(12, 3), tracking=True,
                                              help="Net Weight in KG for DS - Packaging Dimensions")
    packaging_weight_net_re = fields.Float(string="Net Weight", digits=(12, 3), tracking=True,
                                           help="Net Weight in Lbs for RETAIL - Packaging Dimensions")
    packaging_weight_net_re_kg = fields.Float(string="Net Weight", digits=(12, 3), tracking=True,
                                              help="Net Weight in KG for RETAIL - Packaging Dimensions")
    pallet_4w_weight = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                                    help="Weight in Lbs for Standard 4-Way Pallet Only")
    pallet_4w_weight_kg = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                                       help="Weight in KG for Standard 4-Way Pallet Only")
    c4wp_weight = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                               help="Weight in Lbs for CHEP 4-Way Pallet Only")
    pa_sp_weight = fields.Float(string="Weight (Product)", digits=(12, 3), tracking=True,
                                help="Weight(Product) in Lbs for PUT AWAY - Standard Pallet.")
    pa_cp_weight = fields.Float(string="Weight (Product)", digits=(12, 3), tracking=True,
                                help="Weight(Product) in Lbs for PUT AWAY - CHEP Pallet.")
    r_sp_weight = fields.Float(string="Weight (Product)", digits=(12, 3), tracking=True,
                               help="Weight(Product) in Lbs for RETAIL- Standard Pallet.")
    r_cp_weight = fields.Float(string="Weight (Product)", digits=(12, 3), tracking=True,
                               help="Weight(Product) in Lbs for RETAIL - CHEP Pallet.")
    pa_cp_weight_kg = fields.Float(string="Weight (Product)", digits=(12, 3), tracking=True,
                                   help="Weight(Product) in KG for PUT AWAY - CHEP Pallet.")
    r_sp_weight_kg = fields.Float(string="Weight (Product)", digits=(12, 3), tracking=True,
                                  help="Weight(Product) in KG for RETAIL- Standard Pallet.")
    r_cp_weight_kg = fields.Float(string="Weight (Product)", digits=(12, 3), tracking=True,
                                  help="Weight(Product) in KG for RETAIL - CHEP Pallet.")
    pa_sp_weight_kg = fields.Float(string="Weight (Product)", digits=(12, 3), tracking=True,
                                   help="Weight(Product) in KG for PUT AWAY - Standard Pallet.")
    pa_sp_total_weight = fields.Float(string="Total Weight (Product)", digits=(12, 3), tracking=True,
                                      help="Total Weight(Product) in Lbs for PUT AWAY - Standard Pallet.")
    pa_cp_total_weight = fields.Float(string="Total Weight (Product)", digits=(12, 3), tracking=True,
                                      help="Total Weight(Product) in Lbs for PUT AWAY - CHEP Pallet.")
    r_sp_total_weight = fields.Float(string="Total Weight (Product)", digits=(12, 3), tracking=True,
                                     help="Total Weight(Product) in Lbs for RETAIL- Standard Pallet.")
    r_cp_total_weight = fields.Float(string="Total Weight (Product)", digits=(12, 3), tracking=True,
                                     help="Total Weight(Product) in Lbs for RETAIL - CHEP Pallet.")
    pa_cp_total_weight_kg = fields.Float(string="Total Weight (Product)", digits=(12, 3), tracking=True,
                                         help="Total Weight(Product) in KG for PUT AWAY - CHEP Pallet.")
    r_sp_total_weight_kg = fields.Float(string="Total Weight (Product)", digits=(12, 3), tracking=True,
                                        help="Total Weight(Product) in KG for RETAIL- Standard Pallet.")
    r_cp_total_weight_kg = fields.Float(string="Total Weight (Product)", digits=(12, 3), tracking=True,
                                        help="Total Weight(Product) in KG for RETAIL - CHEP Pallet.")
    pa_sp_total_weight_kg = fields.Float(string="Total Weight (Product)", digits=(12, 3), tracking=True,
                                         help="Total Weight(Product) in KG for PUT AWAY - Standard Pallet.")
    c4wp_weight_kg = fields.Float(string="Weight", digits=(12, 3), tracking=True,
                                  help="Weight in KG for CHEP 4-Way Pallet Only")

    # 20 FT Container
    cost_per_unit = fields.Float(digits=(12, 2), string="Cost Per Unit", help="Cost Per Unit for 20 FT Container",
                                 tracking=True)
    floor_load_qty = fields.Float(string="Floor Load Quantity", help="Floor Load Quantity for 20FT Container",
                                  tracking=True)
    ocean_freight_cost = fields.Float(digits=(12, 2), string="Ocean Freight Cost", tracking=True,
                                      help="Ocean Freight Cost for 20 FT Container")
    cube_ft_20ftc = fields.Float(string="Cube (Cuft)", help=_("Cube(Cuft) Cube & Payload for 20FT Container"),
                                 digits=(12, 3), tracking=True)
    cube_m_20ftc = fields.Float(string="Cube (CuM)", help=_("Cube(CuM) Cube & Payload for 20FT Container"),
                                digits=(12, 3), tracking=True)
    cube_ap_ft_20ftc = fields.Float(string="Actual Payload Cube (Cuft)",
                                    help=_("Cube(Cuft) Actual Payload for 20FT Container"), digits=(12, 3),
                                    tracking=True)
    weight_ap_lbs_20ftc = fields.Float(string="Actual Payload Weight (Lbs)",
                                       help=_("weight(Lbs) Actual Payload for 20FT Container"), digits=(12, 3),
                                       tracking=True)
    weight_ap_kg_20ftc = fields.Float(string="Actual Payload Weight (Kg)",
                                      help=_("weight(Kg) Actual Payload for 20FT Container"), digits=(12, 3),
                                      tracking=True)
    cube_ap_m_20ftc = fields.Float(string="Actual Payload Cube (CuM)",
                                   help=_("Cube(CuM) Actual Payload for 20FT Container"), digits=(12, 3), tracking=True)
    cube_acnp_ft_20ftc = fields.Float(string="Actual Cube & Payload Cube (Cuft)",
                                      help=_("Cube(Cuft) Actual Cube & Payload for 20FT Container"), digits=(12, 3),
                                      tracking=True)
    cube_acnp_m_20ftc = fields.Float(string="Actual Cube & Payload Cube (CuM)",
                                     help=_("Cube(CuM) Actual Cube & Payload for 20FT Container"), digits=(12, 3),
                                     tracking=True)
    weight_acnp_lbs_20ftc = fields.Float(string="Actual Cube & Payload Weight (Lbs)",
                                         help=_("Weight (Lbs) Actual Cube & Payload for 20FT Container"),
                                         digits=(12, 3), tracking=True)
    weight_acnp_kg_20ftc = fields.Float(string="Actual Cube & Payload Weight (Kg)",
                                        help=_("Weight (Kg) Actual Cube & Payload for 20FT Container"), digits=(12, 3),
                                        tracking=True)
    weight_lbs_20ftc = fields.Float(string="Payload Weight (Lbs)", digits=(12, 3), tracking=True,
                                    help="Weight(Lbs) Cube & Payload for 20FT Container")
    weight_kg_20ftc = fields.Float(string="Payload Weight (Kg)", digits=(12, 3), tracking=True,
                                   help="Weight(Kg) Cube & Payload for 20FT Container")
    pload_qty_20ftc = fields.Integer(string="Pallets", tracking=True,
                                     help="Pallet Load Quantity (Pallets) for 20FT Container")
    pcload_qty_20ftc = fields.Integer(string="Cases", tracking=True,
                                      help="Pallet Load Quantity (Cases) for 20FT Container")

    # 40 FT Container
    cost_per_unit_40ftc = fields.Float(digits=(12, 2), string="Cost Per Unit", help="Cost Per Unit for 40FT Container",
                                       tracking=True)
    floor_load_qty_40ftc = fields.Float(string="Floor Load Quantity", help="Floor Load Quantity for 40FT Container",
                                        tracking=True)
    ocean_freight_cost_40ftc = fields.Float(digits=(12, 2), string="Ocean Freight Cost", tracking=True,
                                            help="Ocean Freight Cost for 40 FT Container")
    cube_ft_40ftc = fields.Float(string="Cube (Cuft)", help=_("Cube(Cuft) Cube & Payload for 40FT Container"),
                                 digits=(12, 3), tracking=True)
    cube_m_40ftc = fields.Float(string="Cube (CuM)", help=_("Cube(CuM) Cube & Payload for 40FT Container"),
                                digits=(12, 3), tracking=True)
    cube_ap_ft_40ftc = fields.Float(string="Actual Payload Cube (Cuft)",
                                    help=_("Cube(Cuft) Actual Payload for 40FT Container"), digits=(12, 3),
                                    tracking=True)
    weight_ap_lbs_40ftc = fields.Float(string="Actual Payload Weight (Lbs)",
                                       help=_("weight(Lbs) Actual Payload for 40FT Container"), digits=(12, 3),
                                       tracking=True)
    weight_ap_kg_40ftc = fields.Float(string="Actual Payload Weight (Kg)",
                                      help=_("weight(Kg) Actual Payload for 40FT Container"), digits=(12, 3),
                                      tracking=True)
    cube_ap_m_40ftc = fields.Float(string="Actual Payload Cube (CuM)",
                                   help=_("Cube(CuM) Actual Payload for 40FT Container"), digits=(12, 3), tracking=True)
    cube_acnp_ft_40ftc = fields.Float(string="Actual Cube & Payload Cube (Cuft)",
                                      help=_("Cube(Cuft) Actual Cube & Payload for 40FT Container"), digits=(12, 3),
                                      tracking=True)
    cube_acnp_m_40ftc = fields.Float(string="Actual Cube & Payload Cube (CuM)",
                                     help=_("Cube(CuM) Actual Cube & Payload for 40FT Container"), digits=(12, 3),
                                     tracking=True)
    weight_acnp_lbs_40ftc = fields.Float(string="Actual Cube & Payload Weight (Lbs)",
                                         help=_("Weight (Lbs) Actual Cube & Payload for 40FT Container"),
                                         digits=(12, 3), tracking=True)
    weight_acnp_kg_40ftc = fields.Float(string="Actual Cube & Payload Weight (Kg)",
                                        help=_("Weight (Kg) Actual Cube & Payload for 40FT Container"), digits=(12, 3),
                                        tracking=True)
    weight_lbs_40ftc = fields.Float(string="Payload Weight (Lbs)", digits=(12, 3), tracking=True,
                                    help="Weight(Lbs) Cube & Payload for 40FT Container")
    weight_kg_40ftc = fields.Float(string="Payload Weight (Kg)", digits=(12, 3), tracking=True,
                                   help="Weight(Kg) Cube & Payload for 40FT Container")
    pload_qty_40ftc = fields.Integer(string="Pallets", tracking=True,
                                     help="Pallet Load Quantity (Pallets) for 40FT Container")
    pcload_qty_40ftc = fields.Integer(string="Cases", tracking=True,
                                      help="Pallet Load Quantity (Cases) for 40FT Container")

    # 40 FT HC Container
    cost_per_unit_40fthc = fields.Float(digits=(12, 2), string="Cost Per Unit",
                                        help="Cost Per Unit for 40FT HC Container",
                                        tracking=True)
    floor_load_qty_40fthc = fields.Float(string="Floor Load Quantity", help="Floor Load Quantity for 40FT HC Container",
                                         tracking=True)
    ocean_freight_cost_40fthc = fields.Float(digits=(12, 2), string="Ocean Freight Cost", tracking=True,
                                             help="Ocean Freight Cost for 40 FT HC Container")
    cube_ft_40fthc = fields.Float(string="Cube (Cuft)", help=_("Cube(Cuft) Cube & Payload for 40FT HC Container"),
                                  digits=(12, 3), tracking=True)
    cube_m_40fthc = fields.Float(string="Cube (CuM)", help=_("Cube(CuM) Cube & Payload for 40FT HC Container"),
                                 digits=(12, 3), tracking=True)
    cube_ap_ft_40fthc = fields.Float(string="Actual Payload Cube (Cuft)",
                                     help=_("Cube(Cuft) Actual Payload for 40FT HC Container"), digits=(12, 3),
                                     tracking=True)
    weight_ap_lbs_40fthc = fields.Float(string="Actual Payload Weight (Lbs)",
                                        help=_("weight(Lbs) Actual Payload for 40FT HC Container"), digits=(12, 3),
                                        tracking=True)
    weight_ap_kg_40fthc = fields.Float(string="Actual Payload Weight (Kg)",
                                       help=_("weight(Kg) Actual Payload for 40FT HC Container"), digits=(12, 3),
                                       tracking=True)
    cube_ap_m_40fthc = fields.Float(string="Actual Payload Cube (CuM)",
                                    help=_("Cube(CuM) Actual Payload for 40FT HC Container"), digits=(12, 3),
                                    tracking=True)
    cube_acnp_ft_40fthc = fields.Float(string="Actual Cube & Payload Cube (Cuft)",
                                       help=_("Cube(Cuft) Actual Cube & Payload for 40FT HC Container"), digits=(12, 3),
                                       tracking=True)
    cube_acnp_m_40fthc = fields.Float(string="Actual Cube & Payload Cube (CuM)",
                                      help=_("Cube(CuM) Actual Cube & Payload for 40FT HC Container"), digits=(12, 3),
                                      tracking=True)
    weight_acnp_lbs_40fthc = fields.Float(string="Actual Cube & Payload Weight (Lbs)",
                                          help=_("Weight (Lbs) Actual Cube & Payload for 40FT HC Container"),
                                          digits=(12, 3), tracking=True)
    weight_acnp_kg_40fthc = fields.Float(string="Actual Cube & Payload Weight (Kg)",
                                         help=_("Weight (Kg) Actual Cube & Payload for 40FT HC Container"),
                                         digits=(12, 3),
                                         tracking=True)
    weight_lbs_40fthc = fields.Float(string="Payload Weight (Lbs)", digits=(12, 3), tracking=True,
                                     help="Weight(Lbs) Cube & Payload for 40FT HC Container")
    weight_kg_40fthc = fields.Float(string="Payload Weight (Kg)", digits=(12, 3), tracking=True,
                                    help="Weight(Kg) Cube & Payload for 40FT HC Container")
    pload_qty_40fthc = fields.Integer(string="Pallets", tracking=True,
                                      help="Pallet Load Quantity (Pallets) for 40FT HC Container")
    pcload_qty_40fthc = fields.Integer(string="Cases", tracking=True,
                                       help="Pallet Load Quantity (Cases) for 40FT HC Container")

    # 53 FT Dry Van Trailer
    cost_per_unit_53ftc = fields.Float(digits=(12, 2), string="Cost Per Unit", help="Cost Per Unit for 53FT Container",
                                       tracking=True)
    floor_load_qty_53ftc = fields.Float(string="Floor Load Quantity", help="Floor Load Quantity for 53FT Container",
                                        tracking=True)
    ocean_freight_cost_53ftc = fields.Float(digits=(12, 2), string="Ocean Freight Cost", tracking=True,
                                            help="Ocean Freight Cost for 53 FT Container")
    cube_ft_53ftc = fields.Float(string="Cube (Cuft)", help=_("Cube(Cuft) Cube & Payload for 53FT Container"),
                                 digits=(12, 3), tracking=True)
    cube_m_53ftc = fields.Float(string="Cube (CuM)", help=_("Cube(CuM) Cube & Payload for 53FT Container"),
                                digits=(12, 3), tracking=True)
    cube_ap_ft_53ftc = fields.Float(string="Actual Payload Cube (Cuft)",
                                    help=_("Cube(Cuft) Actual Payload for 53FT Container"), digits=(12, 3),
                                    tracking=True)
    weight_ap_lbs_53ftc = fields.Float(string="Actual Payload Weight (Lbs)",
                                       help=_("weight(Lbs) Actual Payload for 53FT Container"), digits=(12, 3),
                                       tracking=True)
    weight_ap_kg_53ftc = fields.Float(string="Actual Payload Weight (Kg)",
                                      help=_("weight(Kg) Actual Payload for 53FT Container"), digits=(12, 3),
                                      tracking=True)
    cube_ap_m_53ftc = fields.Float(string="Actual Payload Cube (CuM)",
                                   help=_("Cube(CuM) Actual Payload for 53FT Container"), digits=(12, 3), tracking=True)
    cube_acnp_ft_53ftc = fields.Float(string="Actual Cube & Payload Cube (Cuft)",
                                      help=_("Cube(Cuft) Actual Cube & Payload for 53FT Container"), digits=(12, 3),
                                      tracking=True)
    cube_acnp_m_53ftc = fields.Float(string="Actual Cube & Payload Cube (CuM)",
                                     help=_("Cube(CuM) Actual Cube & Payload for 53FT Container"), digits=(12, 3),
                                     tracking=True)
    weight_acnp_lbs_53ftc = fields.Float(string="Actual Cube & Payload Weight (Lbs)",
                                         help=_("Weight (Lbs) Actual Cube & Payload for 53FT Container"),
                                         digits=(12, 3), tracking=True)
    weight_acnp_kg_53ftc = fields.Float(string="Actual Cube & Payload Weight (Kg)",
                                        help=_("Weight (Kg) Actual Cube & Payload for 53FT Container"), digits=(12, 3),
                                        tracking=True)
    weight_lbs_53ftc = fields.Float(string="Payload Weight (Lbs)", digits=(12, 3), tracking=True,
                                    help="Weight(Lbs) Cube & Payload for 53FT Container")
    weight_kg_53ftc = fields.Float(string="Payload Weight (Kg)", digits=(12, 3), tracking=True,
                                   help="Weight(Kg) Cube & Payload for 53FT Container")
    pload_qty_53ftc = fields.Integer(string="Pallets", tracking=True,
                                     help="Pallet Load Quantity (Pallets) for 53FT Container")
    pcload_qty_53ftc = fields.Integer(string="Cases", tracking=True,
                                      help="Pallet Load Quantity (Cases) for 53FT Container")

    # 48 FT Dry Van Trailer
    cost_per_unit_48ftc = fields.Float(digits=(12, 2), string="Cost Per Unit",
                                       help="Cost Per Unit for 48 FT Dry Van Trailer",
                                       tracking=True)
    floor_load_qty_48ftc = fields.Float(string="Floor Load Quantity",
                                        help="Floor Load Quantity for 48 FT Dry Van Trailer",
                                        tracking=True)
    ocean_freight_cost_48ftc = fields.Float(digits=(12, 2), string="Ocean Freight Cost", tracking=True,
                                            help="Ocean Freight Cost for 48 FT Dry Van Trailer")
    cube_ft_48ftc = fields.Float(string="Cube (Cuft)", help=_("Cube(Cuft) Cube & Payload for 40FT Container"),
                                 digits=(12, 3), tracking=True)
    cube_m_48ftc = fields.Float(string="Cube (CuM)", help=_("Cube(CuM) Cube & Payload for 48 FT Dry Van Trailer"),
                                digits=(12, 3), tracking=True)
    cube_ap_ft_48ftc = fields.Float(string="Actual Payload Cube (Cuft)",
                                    help=_("Cube(Cuft) Actual Payload for 48 FT Dry Van Trailer"), digits=(12, 3),
                                    tracking=True)
    weight_ap_lbs_48ftc = fields.Float(string="Actual Payload Weight (Lbs)",
                                       help=_("weight(Lbs) Actual Payload for 48 FT Dry Van Trailer"), digits=(12, 3),
                                       tracking=True)
    weight_ap_kg_48ftc = fields.Float(string="Actual Payload Weight (Kg)",
                                      help=_("weight(Kg) Actual Payload for 48 FT Dry Van Trailer"), digits=(12, 3),
                                      tracking=True)
    cube_ap_m_48ftc = fields.Float(string="Actual Payload Cube (CuM)",
                                   help=_("Cube(CuM) Actual Payload for 48 FT Dry Van Trailer"), digits=(12, 3),
                                   tracking=True)
    cube_acnp_ft_48ftc = fields.Float(string="Actual Cube & Payload Cube (Cuft)",
                                      help=_("Cube(Cuft) Actual Cube & Payload for 48 FT Dry Van Trailer"),
                                      digits=(12, 3),
                                      tracking=True)
    cube_acnp_m_48ftc = fields.Float(string="Actual Cube & Payload Cube (CuM)",
                                     help=_("Cube(CuM) Actual Cube & Payload for 48 FT Dry Van Trailer"),
                                     digits=(12, 3),
                                     tracking=True)
    weight_acnp_lbs_48ftc = fields.Float(string="Actual Cube & Payload Weight (Lbs)",
                                         help=_("Weight (Lbs) Actual Cube & Payload for 48 FT Dry Van Trailer"),
                                         digits=(12, 3), tracking=True)
    weight_acnp_kg_48ftc = fields.Float(string="Actual Cube & Payload Weight (Kg)",
                                        help=_("Weight (Kg) Actual Cube & Payload for 48 FT Dry Van Trailer"),
                                        digits=(12, 3),
                                        tracking=True)
    weight_lbs_48ftc = fields.Float(string="Payload Weight (Lbs)", digits=(12, 3), tracking=True,
                                    help="Weight(Lbs) Cube & Payload for 48 FT Dry Van Trailer")
    weight_kg_48ftc = fields.Float(string="Payload Weight (Kg)", digits=(12, 3), tracking=True,
                                   help="Weight(Kg) Cube & Payload for 48 FT Dry Van Trailer")
    pload_qty_48ftc = fields.Integer(string="Pallets", tracking=True,
                                     help="Pallet Load Quantity (Pallets) for 48 FT Dry Van Trailer")
    pcload_qty_48ftc = fields.Integer(string="Cases", tracking=True,
                                      help="Pallet Load Quantity (Cases) for 48 FT Dry Van Trailer")

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            rec.image = rec.product_id.image_1920

    @api.depends('case_pack_weight')
    def _compute_case_pack_weight_kg(self):
        self.case_pack_weight_kg = self.case_pack_weight / 2.2046226218

    @api.depends('retail_pallet_weight')
    def _compute_retail_pallet_weight_kg(self):
        self.retail_pallet_weight_kg = self.retail_pallet_weight / 2.2046226218

    case_pack_net_weight = fields.Float(string="Net Weight", digits=(12, 3), tracking=True,
                                        help="Net Weight in Lbs for RETAIL - Case Pack  Dimensions")

    @api.depends('case_pack_net_weight')
    def _compute_case_pack_net_weight_kg(self):
        self.case_pack_net_weight_kg = self.case_pack_net_weight / 2.2046226218

    case_pack_net_weight_kg = fields.Float(string="Net Weight", digits=(12, 3), tracking=True,
                                           help="Net Weight in KG for RETAIL - Case Pack  Dimensions",
                                           compute='_compute_case_pack_net_weight_kg')

    @api.depends('packaging_weight')
    def _compute_packaging_weight_kg(self):
        self.packaging_weight_kg = self.packaging_weight / 2.2046226218

    packaging_weight_kg = fields.Float(string="Weight (kg)", digits=(12, 3), tracking=True,
                                       compute='_compute_packaging_weight_kg')

    @api.depends('packaging_weight_net')
    def _compute_packaging_weight_kg_net(self):
        self.packaging_weight_kg_net = self.packaging_weight_net / 2.2046226218

    packaging_weight_kg_net = fields.Float(string="Net Weight (kg)", digits=(12, 3), tracking=True,
                                           compute='_compute_packaging_weight_kg_net')
    # packaging_w = fields.Float(string="W")
    packaging_width = fields.Float(string="Width", help=_("Width(W) in inches for Packaging Dimensions and Weights"),
                                   digits=(12, 3), tracking=True)
    pallet_4w_width = fields.Float(string="Width", help=_("Width(W) in inches for Standard 4-Way Pallet"),
                                   digits=(12, 3), tracking=True)
    c4wp_width = fields.Float(string="Width", help=_("Width(W) in inches for CHEP 4-Way Pallet Only"),
                              digits=(12, 3), tracking=True)
    c4wp_width_cm = fields.Float(string="Width", help=_("Width(W) in CM for CHEP 4-Way Pallet Only"),
                                 digits=(12, 3), tracking=True)
    pa_sp_width_unit = fields.Integer(string="Width - Units", default=4,
                                      help=_("Width(W) - 40 Max units for PUT AWAY - Standard Pallet."), tracking=True)
    pa_sp_height_unit = fields.Integer(string="Height - Units", default=3,
                                       help=_("Height(H) - 48 Max units for PUT AWAY - Standard Pallet."),
                                       tracking=True)
    r_sp_height_unit = fields.Integer(string="Height - Units", default=3, tracking=True,
                                      help=_("Height(H) - 48 Max units for RETAIL- Standard Pallet."))
    r_cp_height_unit = fields.Integer(string="Height - Units", default=3, tracking=True,
                                      help=_("Height(H) - 48 Max units for RETAIL - CHEP Pallet."))
    pa_sp_length_unit = fields.Integer(string="Length - Units", default=3,
                                       help=_("Length(L) - 48 Max units for PUT AWAY - Standard Pallet."),
                                       tracking=True)
    pa_cp_width_unit = fields.Integer(string="Width - Units", default=4,
                                      help=_("Width(W) - 40 Max units for PUT AWAY - CHEP Pallet."), tracking=True)
    pa_cp_height_unit = fields.Integer(string="Height - Units", default=3,
                                       help=_("Height(H) - 48 Max units for PUT AWAY - CHEP Pallet."),
                                       tracking=True)
    r_sp_width_unit = fields.Integer(string="Width - Units", default=4, tracking=True,
                                     help=_("Width(W) - 40 Max units for RETAIL- Standard Pallet."))
    r_cp_width_unit = fields.Integer(string="Width - Units", default=4, tracking=True,
                                     help=_("Width(W) - 40 Max units for RETAIL - CHEP Pallet."))
    pa_cp_length_unit = fields.Integer(string="Length - Units", default=3,
                                       help=_("Length(L) - 48 Max units for PUT AWAY - CHEP Pallet."),
                                       tracking=True)
    r_sp_length_unit = fields.Integer(string="Length - Units", default=3, tracking=True,
                                      help=_("Length(L) - 48 Max units for RETAIL- Standard Pallet"))
    r_cp_length_unit = fields.Integer(string="Length - Units", default=3, tracking=True,
                                      help=_("Length(L) - 48 Max units for RETAIL - CHEP Pallet"))
    pa_sp_width = fields.Float(string="Width - 40 Max", help=_("Width(W) in inches for PUT AWAY - Standard Pallet."),
                               digits=(12, 3), tracking=True)
    pa_sp_width_cm = fields.Float(string="Width - 40 Max", help=_("Width(W) in CM for PUT AWAY - Standard Pallet."),
                                  digits=(12, 3), tracking=True)
    pa_cp_width = fields.Float(string="Width - 40 Max", help=_("Width(W) 40 Max in Inches for PUT AWAY - CHEP Pallet"),
                               digits=(12, 3), tracking=True)
    r_sp_width = fields.Float(string="Width - 40 Max", help=_("Width(W) 40 Max in Inches for RETAIL- Standard Pallet"),
                              digits=(12, 3), tracking=True)
    r_cp_width = fields.Float(string="Width - 40 Max", help=_("Width(W) 40 Max in Inches for RETAIL - CHEP Pallet"),
                              digits=(12, 3), tracking=True)
    pa_cp_width_cm = fields.Float(string="Width - 40 Max", help=_("Width(W) 40 Max in CM for PUT AWAY - CHEP Pallet"),
                                  digits=(12, 3), tracking=True)
    r_sp_width_cm = fields.Float(string="Width - 40 Max", help=_("Width(W) 40 Max in CM for RETAIL- Standard Pallet"),
                                 digits=(12, 3), tracking=True)
    r_cp_width_cm = fields.Float(string="Width - 40 Max", help=_("Width(W) 40 Max in CM for RETAIL - CHEP Pallet."),
                                 digits=(12, 3), tracking=True)
    pa_cp_height = fields.Float(string="Height - 48 Max",
                                help=_("Height(H) 48 Max in Inches for PUT AWAY - CHEP Pallet."),
                                digits=(12, 3), tracking=True)
    r_sp_height = fields.Float(string="Height - 48 Max", digits=(12, 3), tracking=True,
                               help=_("Height(H) 48 Max in Inches for RETAIL- Standard Pallet."))
    r_cp_height = fields.Float(string="Height - 48 Max", digits=(12, 3), tracking=True,
                               help=_("Height(H) 48 Max in Inches for RETAIL - CHEP Pallet."))
    pa_cp_height_cm = fields.Float(string="Height - 48 Max",
                                   help=_("Height(H) 48 Max in CM for PUT AWAY - CHEP Pallet."),
                                   digits=(12, 3), tracking=True)
    r_sp_height_cm = fields.Float(string="Height - 48 Max", digits=(12, 3), tracking=True,
                                  help=_("Height(H) 48 Max in CM for RETAIL- Standard Pallet."))
    r_cp_height_cm = fields.Float(string="Height - 48 Max", digits=(12, 3), tracking=True,
                                  help=_("Height(H) 48 Max in CM for RETAIL - CHEP Pallet."))
    pa_cp_length = fields.Float(string="Length - 48 Max",
                                help=_("Length(L) 48 Max in Inches for PUT AWAY - CHEP Pallet."),
                                digits=(12, 3), tracking=True)
    r_sp_length = fields.Float(string="Length - 48 Max", digits=(12, 3), tracking=True,
                               help=_("Length(L) 48 Max in Inches for RETAIL- Standard Pallet."))
    r_cp_length = fields.Float(string="Length - 48 Max", digits=(12, 3), tracking=True,
                               help=_("Length(L) 48 Max in Inches for RETAIL - CHEP Pallet."))
    pa_cp_length_cm = fields.Float(string="Length - 48 Max",
                                   help=_("Length(L) 48 Max in CM for PUT AWAY - CHEP Pallet."),
                                   digits=(12, 3), tracking=True)
    r_sp_length_cm = fields.Float(string="Length - 48 Max",
                                  help=_("Length(L) 48 Max in CM for RETAIL- Standard Pallet."),
                                  digits=(12, 3), tracking=True)
    r_cp_length_cm = fields.Float(string="Length - 48 Max", digits=(12, 3), tracking=True,
                                  help=_("Length(L) 48 Max in CM for RETAIL - CHEP Pallet."))
    pa_sp_height = fields.Float(string="Height - 48 Max", help=_("Height(H) in inches for PUT AWAY - Standard Pallet."),
                                digits=(12, 3), tracking=True)
    pa_sp_height_cm = fields.Float(string="Height - 48 Max", help=_("Height(H) in CM for PUT AWAY - Standard Pallet."),
                                   digits=(12, 3), tracking=True)
    pa_sp_length = fields.Float(string="Length - 48 Max", help=_("Length(L) in inches for PUT AWAY - Standard Pallet."),
                                digits=(12, 3), tracking=True)
    pa_sp_length_cm = fields.Float(string="Length - 48 Max", help=_("Length(L) in CM for PUT AWAY - Standard Pallet."),
                                   digits=(12, 3), tracking=True)

    @api.depends('pallet_4w_width')
    def _compute_pallet_4w_width_cm(self):
        self.pallet_4w_width_cm = self.pallet_4w_width * 2.54

    pallet_4w_width_cm = fields.Float(string="Width", help=_("Width(W) in CM for Standard 4-Way Pallet"),
                                      digits=(12, 3), tracking=True, compute="_compute_pallet_4w_width_cm")
    pallet_4w_height = fields.Float(string="Height", help=_("Height(H) in inches for Standard 4-Way Pallet"),
                                    digits=(12, 3), tracking=True)
    c4wp_height = fields.Float(string="Height", help=_("Height(H) in inches for CHEP 4-Way Pallet Only"),
                               digits=(12, 3), tracking=True)
    c4wp_height_cm = fields.Float(string="Height", help=_("Height(H) in CM for CHEP 4-Way Pallet Only"),
                                  digits=(12, 3), tracking=True)
    c4wp_length = fields.Float(string="Length", help=_("Length(L) in inches for CHEP 4-Way Pallet Only"),
                               digits=(12, 3), tracking=True)
    c4wp_length_cm = fields.Float(string="Length", help=_("Length(L) in CM for CHEP 4-Way Pallet Only"),
                                  digits=(12, 3), tracking=True)

    @api.depends('pallet_4w_height')
    def _compute_pallet_4w_height_cm(self):
        self.pallet_4w_height_cm = self.pallet_4w_height * 2.54

    pallet_4w_height_cm = fields.Float(string="Height", help=_("Height(H) in CM for Standard 4-Way Pallet"),
                                       digits=(12, 3), tracking=True, compute='_compute_pallet_4w_height_cm')

    pallet_4w_length = fields.Float(string="Length", help=_("Length(L) in inches for Standard 4-Way Pallet"),
                                    digits=(12, 3), tracking=True)

    @api.depends('pallet_4w_length')
    def _compute_pallet_4w_length_cm(self):
        self.pallet_4w_length_cm = self.pallet_4w_length * 2.54

    pallet_4w_length_cm = fields.Float(string="Length", help=_("Length(L) in CM for Standard 4-Way Pallet"),
                                       digits=(12, 3), tracking=True, compute='_compute_pallet_4w_length_cm')

    @api.depends('case_pack_width')
    def _compute_case_pack_width_cm(self):
        self.case_pack_width_cm = self.case_pack_width * 2.54

    @api.depends('case_pack_height')
    def _compute_case_pack_height_cm(self):
        self.case_pack_height_cm = self.case_pack_height * 2.54

    @api.depends('case_pack_length')
    def _compute_case_pack_length_cm(self):
        self.case_pack_length_cm = self.case_pack_length * 2.54

    @api.depends('packaging_width')
    def _compute_packaging_width_cm(self):
        self.packaging_width_cm = self.packaging_width * 2.54

    packaging_width_cm = fields.Float(string="Width",
                                      help=_("Width(W) in centimetre for Packaging Dimensions and Weights"),
                                      digits=(12, 3), compute="_compute_packaging_width_cm", tracking=True)

    packaging_dimension = fields.Float(string="Dimension", tracking=True)
    packaging_depth = fields.Float(string="Length", help=_("Length(L) in inches for Packaging Dimensions and Weights"),
                                   digits=(12, 3), tracking=True)

    @api.depends('packaging_depth')
    def _compute_packaging_depth_cm(self):
        self.packaging_length_cm = self.packaging_depth * 2.54

    packaging_length_cm = fields.Float(string="Length",
                                       help=_("Length(L) in centimeter for Packaging Dimensions and Weights"),
                                       digits=(12, 3), tracking=True, compute='_compute_packaging_depth_cm')

    packaging_height = fields.Float(string="Height", help=_("Height(H) in inches for Packaging Dimensions and Weights"),
                                    digits=(12, 3), tracking=True)

    @api.depends('packaging_height')
    def _compute_packaging_height_cm(self):
        self.packaging_height_cm = self.packaging_height * 2.54

    packaging_height_cm = fields.Float(string="Height",
                                       help=_("Height(H) in centimeter for Packaging Dimensions and Weights"),
                                       digits=(12, 3), tracking=True, compute='_compute_packaging_height_cm')

    packaging_cuft = fields.Float(string="Cube In.", compute="_compute_packaging_cuft",
                                  help=_("Cubic Inch(CuIn) for Packaging Dimensions and Weights"), digits=(12, 3),
                                  tracking=True)

    @api.depends('pallet_4w_height', 'pallet_4w_length', 'pallet_4w_width')
    def _compute_pallet_4w_cube(self):
        self.pallet_4w_cube = self.pallet_4w_height * self.pallet_4w_length * self.pallet_4w_width / 1728

    pallet_4w_cube = fields.Float(string="Cube", help=_("Cube in f^3 for Standard 4-Way Pallet"),
                                  digits=(12, 3), tracking=True, compute='_compute_pallet_4w_cube')

    @api.depends('c4wp_width', 'c4wp_length', 'c4wp_height')
    def _compute_c4wp_cube(self):
        self.c4wp_cube = self.c4wp_height * self.c4wp_length * self.c4wp_width / 1728

    c4wp_cube = fields.Float(string="Cube", help=_("Cube in f^3 for CHEP 4-Way Pallet Only"),
                             digits=(12, 3), tracking=True, compute='_compute_c4wp_cube')
    pa_sp_cube = fields.Float(string="Cube (Product)", help=_("Cube in Ft3 for PUT AWAY - Standard Pallet"),
                              digits=(12, 3), tracking=True)
    pa_cp_cube = fields.Float(string="Cube (Product)", help=_("Cube in Ft3 for PUT AWAY - CHEP Pallet"),
                              digits=(12, 3), tracking=True)
    r_sp_cube = fields.Float(string="Cube (Product)", help=_("Cube in Ft3 for RETAIL- Standard Pallet."),
                             digits=(12, 3), tracking=True)
    r_cp_cube = fields.Float(string="Cube (Product)", help=_("Cube in Ft3 for RETAIL - CHEP Pallet."),
                             digits=(12, 3), tracking=True)
    pa_cp_cube_m3 = fields.Float(string="Cube (Product)", help=_("Cube in m3 for PUT AWAY - CHEP Pallet"),
                                 digits=(12, 3), tracking=True)
    r_sp_cube_m3 = fields.Float(string="Cube (Product)", help=_("Cube in m3 for RETAIL- Standard Pallet"),
                                digits=(12, 3), tracking=True)
    r_cp_cube_m3 = fields.Float(string="Cube (Product)", help=_("Cube in m3 for RETAIL - CHEP Pallet."), digits=(12, 3),
                                tracking=True)
    pa_sp_cube_m3 = fields.Float(string="Cube (Product)", help=_("Cube in m3 for PUT AWAY - Standard Pallet"),
                                 digits=(12, 3), tracking=True)
    pa_sp_total_cube = fields.Float(string="Total Cube (Product)",
                                    help=_("Total Cube (Product) in ft3 for PUT AWAY - Standard Pallet"),
                                    digits=(12, 3), tracking=True)
    pa_cp_total_cube = fields.Float(string="Total Cube (Product)",
                                    help=_("Total Cube (Product) in ft3 for PUT AWAY - CHEP Pallet"),
                                    digits=(12, 3), tracking=True)
    r_sp_total_cube = fields.Float(string="Total Cube (Product)",
                                   help=_("Total Cube (Product) in ft3 for RETAIL- Standard Pallet."),
                                   digits=(12, 3), tracking=True)
    r_cp_total_cube = fields.Float(string="Total Cube (Product)", digits=(12, 3), tracking=True,
                                   help=_("Total Cube (Product) in ft3 for RETAIL - CHEP Pallet."))
    pa_cp_total_cube_m3 = fields.Float(string="Total Cube (Product)",
                                       help=_("Total Cube (Product) in m3 for PUT AWAY - CHEP Pallet"),
                                       digits=(12, 3), tracking=True)
    r_sp_total_cube_m3 = fields.Float(string="Total Cube (Product)",
                                      help=_("Total Cube (Product) in m3 for RETAIL- Standard Pallet"),
                                      digits=(12, 3), tracking=True)
    r_cp_total_cube_m3 = fields.Float(string="Total Cube (Product)",
                                      help=_("Total Cube (Product) in m3 for RETAIL - CHEP Pallet."),
                                      digits=(12, 3), tracking=True)
    pa_sp_total_cube_m3 = fields.Float(string="Total Cube (Product)",
                                       help=_("Total Cube (Product) in m3 for PUT AWAY - Standard Pallet"),
                                       digits=(12, 3), tracking=True)
    c4wp_cube_m3 = fields.Float(string="Cube", help=_("Cube in m3 for CHEP 4-Way Pallet Only"),
                                digits=(12, 3), tracking=True)

    # @api.depends('pallet_4w_height_cm', 'pallet_4w_length_cm', 'pallet_4w_width_cm')
    # def _compute_pallet_4w_cube_m3(self):
    #     self.pallet_4w_cube = self.pallet_4w_height_cm * self.pallet_4w_length_cm * self.pallet_4w_width_cm / 1728

    pallet_4w_cube_m3 = fields.Float(string="Cube", help=_("Cube in m^3 for Standard 4-Way Pallet"),
                                     digits=(12, 3), tracking=True)

    @api.depends('case_pack_width', 'case_pack_length', 'case_pack_height')
    def _compute_case_pack_cube(self):
        self.case_pack_cube = self.case_pack_width * self.case_pack_length * self.case_pack_height / 1728

    @api.depends('case_pack_length_cm', 'case_pack_height_cm', 'case_pack_width_cm')
    def _compute_case_pack_cube_m3(self):
        self.case_pack_cube_m3 = self.case_pack_length_cm * self.case_pack_height_cm * self.case_pack_width_cm / 1000000

    @api.depends('packaging_cuft')
    def _compute_packaging_cuft_cm(self):
        self.packaging_cuft_cm = self.packaging_height_cm * self.packaging_length_cm * self.packaging_width_cm

    packaging_cuft_cm = fields.Float(string="Cube cm.",
                                     help=_("Cubic Centimeter(CuCm) for Packaging Dimensions and Weights"),
                                     digits=(12, 3),
                                     tracking=True, compute="_compute_packaging_cuft_cm")
    export_mrf_price = fields.Float(digits=(12, 3), string="Exporter / Mfr Price", tracking=True)
    payment_terms_days = fields.Float(digits=(12, 3), string="Payment Terms Days",
                                      help="Payment terms to the exporter US Trading Company", tracking=True)
    payment_terms_per_year = fields.Float(digits=(12, 3), string="Payment Terms Percentage",
                                          help="Payment terms percentage per year", tracking=True)

    # @api.depends('product_id')
    def _get_leads(self):
        for pd in self:
            crm_lead_ids = self.env['crm.lead'].sudo().search([('product_development_id', '=', pd.id)])
            pd.lead_count = len(crm_lead_ids)
            pd.lead_ids = crm_lead_ids

    lead_count = fields.Integer(string='Leads Count', compute='_get_leads', readonly=True)
    lead_ids = fields.Many2many("crm.lead", string='Leads', compute="_get_leads", readonly=True, copy=False)

    def action_view_crm_lead(self):
        """ View created leads from product development.
        return: view of leads """
        lead_ids = self.mapped('lead_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_action_pipeline")  # crm lead form view action
        if len(lead_ids) > 1:
            action['domain'] = [('id', 'in', lead_ids.ids)]
        elif len(lead_ids) == 1:
            form_view = [(self.env.ref('crm.crm_lead_view_form').id, 'form')]  # Form view
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = lead_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def create_lead_pro_dev(self):
        """ Create CRM lead (opportunity) from the product development.
        return: view created record. """
        val = {'name': self.product_id.name if self.product_id else "NIL",
               'partner_id': self.made_by.id if self.made_by else False,
               'product_development_id': self.id,
               'product_id': self.product_id.id if self.product_id else False,
               }
        crm_lead_id = self.env['crm.lead'].sudo().create(val)
        if crm_lead_id:
            crm_lead_id.sudo().write({'description': 'Created from Product Development by ' + str(
                self.env.user.name) + ' at ' + str(crm_lead_id.create_date)})
            action = self.env["ir.actions.actions"]._for_xml_id(
                "crm.crm_lead_action_pipeline")  # crm lead form view action
            form_view = [(self.env.ref('crm.crm_lead_view_form').id, 'form')]  # Form view
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = crm_lead_id.id
        return action

    @api.depends('export_mrf_price', 'payment_terms_per_year', 'payment_terms_days')
    def _compute_payment_terms_cost(self):
        self.payment_terms_cost = ((self.export_mrf_price * (
                0.01 * self.payment_terms_per_year)) / 360) * self.payment_terms_days

    payment_terms_cost = fields.Float(digits=(12, 2), string="Payment Terms Cost",
                                      compute='_compute_payment_terms_cost', tracking=True)

    @api.depends('payment_terms_cost', 'export_mrf_price')
    def _compute_payment_terms_per(self):
        self.payment_terms_per = math.ceil(
            self.payment_terms_cost / (0.01 * self.export_mrf_price)) if self.export_mrf_price > 0.0 else 0.0

    payment_terms_per = fields.Float(digits=(12, 3), string="Payment Terms Cost Percentage",
                                     compute='_compute_payment_terms_per', tracking=True)

    @api.depends('payment_terms_cost', 'export_mrf_price')
    def _compute_export_fob_price(self):
        if self.payment_terms_cost:
            self.export_fob_price = self.export_mrf_price + self.payment_terms_cost
        else:
            self.export_fob_price = 0.0

    export_fob_price = fields.Float(digits=(12, 3), string="Export FOB Price", compute='_compute_export_fob_price',
                                    tracking=True)
    mark_up_per = fields.Float(string="Mark UP/Commission Percentage",
                               help="US Trading Company - Mark Up/Commission default 5% based on the FOB Price.",
                               default=5.0, tracking=True)

    @api.depends('export_fob_price', 'mark_up_per')
    def _compute_mark_up_cost(self):
        if self.mark_up_per:
            self.mark_up_cost = (self.export_fob_price * self.mark_up_per) / 100
        else:
            self.mark_up_cost = 0.0

    mark_up_cost = fields.Float(string="Mark UP/Commission Cost", compute='_compute_mark_up_cost', tracking=True)

    @api.depends('mark_up_cost', 'export_fob_price')
    def _compute_mark_up_cost_per(self):
        self.mark_up_cost_per = round(
            (self.mark_up_cost / self.export_fob_price) * 100) if self.export_fob_price > 0.0 else 0.0

    mark_up_cost_per = fields.Float(string="Mark UP/Commission Cost Percentage", compute="_compute_mark_up_cost_per",
                                    tracking=True)

    @api.depends('export_mrf_price', 'retail_price')
    def _compute_export_factor(self):
        self.export_factor = self.retail_price / self.export_mrf_price if self.export_mrf_price > 0.0 else 0.0

    export_factor = fields.Float(string="Factor", digits=(12, 3), compute='_compute_export_factor', tracking=True)

    @api.depends('packaging_width', 'packaging_depth', 'packaging_height')
    def _compute_packaging_cuft(self):
        self.packaging_cuft = (self.packaging_width * self.packaging_depth * self.packaging_height) / (12 * 12 * 12)

    remailer_qty = fields.Float(string="QTY", tracking=True)
    remailer_weight = fields.Float(string="Weight", tracking=True)
    remailer_w = fields.Float(string="W", tracking=True)
    remailer_dimension = fields.Float(string="Dimension", tracking=True)
    remailer_height = fields.Float(string="Height", tracking=True)
    remailer_cuft = fields.Float(string="CuFt", tracking=True)
    master_qty = fields.Float(string="QTY", tracking=True)
    master_weight = fields.Float(string="Weight", tracking=True)
    master_w = fields.Float(string="W", tracking=True)
    master_dimension = fields.Float(string="Dimension", tracking=True)
    master_height = fields.Float(string="Height", tracking=True)
    master_cuft = fields.Float(string="CuFt", tracking=True)
    # pallet_exclude_qty = fields.Float(string="QTY")
    pallet_exclude_qty = fields.Float(string="QTY", compute="_compute_pallet_qty",
                                      help="Packages on the pallet", digits=(12, 3), tracking=True)

    # pallet_exclude_weight = fields.Float(string="Weight")
    pallet_exclude_weight = fields.Float(string="Weight", digits=(12, 3), compute='_compute_pallet_exclude_weight',
                                         tracking=True)

    @api.depends("pallet_exclude_qty", "packaging_weight")
    def _compute_pallet_exclude_weight(self):
        self.pallet_exclude_weight = self.pallet_exclude_qty * self.packaging_weight

    @api.depends('packaging_width')
    def _compute_pallet_width(self):
        self.pallet_exclude_width = 3 * self.packaging_width
        self.pallet_include_width = float(math.ceil(3 * self.packaging_width))

    # pallet_exclude_w = fields.Float(string="W")
    pallet_exclude_width = fields.Float(string="Width",
                                        help=_("Width for Pallet Dimensions and Weights excluding pallet"),
                                        digits=(12, 3), compute='_compute_pallet_width', tracking=True)

    @api.depends('packaging_depth')
    def _compute_pallet_depth(self):
        self.pallet_exclude_depth = 4 * self.packaging_depth
        self.pallet_include_depth = float(math.ceil(4 * self.packaging_depth))

    # pallet_exclude_dimension = fields.Float(string="Dimension")
    pallet_exclude_depth = fields.Float(string="Depth",
                                        help=_("Depth for Pallet Dimensions and Weights excluding pallet"),
                                        digits=(12, 3), compute='_compute_pallet_depth', tracking=True)

    @api.depends('packaging_height')
    def _compute_pallet_height(self):
        self.pallet_exclude_height = 4 * self.packaging_height
        self.pallet_include_height = float(math.ceil((4 * self.packaging_height) + 5))

    pallet_exclude_height = fields.Float(string="Height",
                                         help=_("Height for Pallet Dimensions and Weights excluding pallet"),
                                         digits=(12, 3), compute='_compute_pallet_height', tracking=True)

    # pallet_exclude_cuft = fields.Float(string="CuFt")
    pallet_exclude_cuft = fields.Float(string="CuFt", compute='_compute_pallet_exclude_cuft', digits=(12, 3),
                                       tracking=True)

    @api.depends('pallet_exclude_height', 'pallet_exclude_depth', 'pallet_exclude_width')
    def _compute_pallet_exclude_cuft(self):
        # TODO: As per requirement calculation should be round off. Round off with higher number.
        self.pallet_exclude_cuft = (float(math.ceil(self.pallet_exclude_height)) * float(
            math.ceil(self.pallet_exclude_depth)) * float(math.ceil(self.pallet_exclude_width))) / (12 * 12 * 12) * (
                                       0.85)

    # pallet_include_qty = fields.Float(string="QTY")
    pallet_include_qty = fields.Float(string="QTY", digits=(12, 3), compute="_compute_pallet_qty",
                                      help=_("Packages on the pallet"), tracking=True)

    @api.depends("packaging_qty")
    def _compute_pallet_qty(self):
        # TODO: as per requirement on the pallet package should be W=3, D=4, H=4. So qty is 48.
        self.pallet_exclude_qty = self.pallet_include_qty = 3 * 4 * 4

    @api.depends('pallet_exclude_weight')
    def _compute_pallet_include_weight(self):
        """ as per requirement pallet weight is 50 so add 50 in the pallet excluding weight. """
        self.pallet_include_weight = self.pallet_exclude_weight + 50

    # pallet_include_weight = fields.Float(string="Weight")
    pallet_include_weight = fields.Float(string="Weight", digits=(12, 3), compute='_compute_pallet_include_weight',
                                         tracking=True)

    # pallet_include_w = fields.Float(string="W")
    pallet_include_width = fields.Float(string="Width",
                                        help=_("Width for Pallet Dimensions and Weights including pallet"),
                                        digits=(12, 3), compute='_compute_pallet_width', tracking=True)

    # pallet_include_dimension = fields.Float(string="Dimension")
    pallet_include_depth = fields.Float(string="Depth",
                                        help=_("Depth for Pallet Dimensions and Weights including pallet"),
                                        digits=(12, 3), compute='_compute_pallet_depth', tracking=True)

    # pallet_include_height = fields.Float(string="Height")
    pallet_include_height = fields.Float(string="Height",
                                         help=_("Height for Pallet Dimensions and Weights including pallet"),
                                         digits=(12, 3), compute='_compute_pallet_height', tracking=True)

    @api.depends('pallet_include_height', 'pallet_include_depth', 'pallet_include_width')
    def _compute_pallet_include_cuft(self):
        """ As per requirement calculation should be round off. Round off with higher number. """
        self.pallet_include_cuft = (float(math.ceil(self.pallet_include_height)) * float(
            math.ceil(self.pallet_include_depth)) * float(math.ceil(self.pallet_include_width))) / (12 * 12 * 12)

    # pallet_include_cuft = fields.Float(string="CuFt")
    pallet_include_cuft = fields.Float(string="CuFt", compute='_compute_pallet_include_cuft', digits=(12, 3),
                                       tracking=True)

    container_load_ids = fields.One2many('container.load.calculation', 'product_development_id',
                                         string='Container Load')
    container_floor_pallet_ids = fields.One2many('container.floor.pallet', 'product_development_id',
                                                 string='Container Floor Pallet')
    imagery_ids = fields.Many2many('ir.attachment', string='Imagery', tracking=True)

    cu_ft_20 = fields.Float(string='20 Ft.', tracking=True)
    cu_ft_40 = fields.Float(string='40 Ft.', tracking=True)
    cu_ft_40_hc = fields.Float(string='40 Ft. HC', tracking=True)
    pay_load_lbs_ft_20 = fields.Float(string='20 Ft.', tracking=True)
    pay_load_lbs_ft_40 = fields.Float(string='40 Ft.', tracking=True)
    pay_load_lbs_ft_40_hc = fields.Float(string='40 Ft. HC', tracking=True)
    cubic_ft_20 = fields.Float(string='20 Ft.', tracking=True)
    cubic_ft_40 = fields.Float(string='40 Ft.', tracking=True)
    cubic_ft_40_hc = fields.Float(string='40 Ft. HC', tracking=True)
    pay_load_kg_ft_20 = fields.Float(string='20 Ft.', tracking=True)
    pay_load_kg_ft_40 = fields.Float(string='40 Ft.', tracking=True)
    pay_load_kg_ft_40_hc = fields.Float(string='40 Ft. HC', tracking=True)

    @api.depends('cu_ft_20', 'packaging_cuft')
    def _compute_floor_total_case_20(self):
        if self.packaging_cuft:
            self.floor_total_case_20 = int(self.cu_ft_20 / self.packaging_cuft)
        else:
            self.floor_total_case_20 = 0.0

    floor_total_case_20 = fields.Float(string="Total Cases", compute="_compute_floor_total_case_20", tracking=True)

    @api.depends('floor_total_case_20', 'packaging_cuft')
    def _compute_floor_cu_ft_20(self):
        if self.floor_total_case_20:
            self.floor_cu_ft_20 = self.floor_total_case_20 * self.packaging_cuft
        else:
            self.floor_cu_ft_20

    floor_cu_ft_20 = fields.Float(string="Cu Ft", compute="_compute_floor_cu_ft_20", tracking=True)

    @api.depends('floor_total_case_20', 'packaging_weight')
    def _compute_floor_weight_20(self):
        self.floor_weight_20 = self.floor_total_case_20 * self.packaging_weight

    floor_weight_20 = fields.Float(string="Weight", compute="_compute_floor_weight_20", tracking=True)

    @api.depends('floor_total_case_20', 'pallet_exclude_qty')
    def _compute_pallet_total_20(self):
        self.pallet_total_20 = math.ceil(
            self.floor_total_case_20 / self.pallet_exclude_qty) if self.pallet_exclude_qty else 0.0

    # pallet_total_20 = fields.Float(string="Total Pallet")
    pallet_total_20 = fields.Float(string="Total Pallet", compute="_compute_pallet_total_20", tracking=True)

    @api.depends('pallet_include_cuft', 'pallet_total_20')
    def _compute_pallet_cu_ft_20(self):
        self.pallet_cu_ft_20 = self.pallet_total_20 * self.pallet_include_cuft

    pallet_cu_ft_20 = fields.Float(string="Cu Ft", compute='_compute_pallet_cu_ft_20', tracking=True)

    # pallet_cu_ft_20 = fields.Float(string="Cu Ft")

    @api.depends('pallet_include_weight', 'pallet_total_20')
    def _compute_pallet_weight_20(self):
        self.pallet_weight_20 = round(self.pallet_include_weight * self.pallet_total_20)

    pallet_weight_20 = fields.Float(string="Weight", compute='_compute_pallet_weight_20', tracking=True)

    # pallet_weight_20 = fields.Float(string="Weight")

    @api.depends('cu_ft_40', 'packaging_cuft')
    def _compute_floor_total_case_40(self):
        if self.packaging_cuft:
            self.floor_total_case_40 = round(self.cu_ft_40 / self.packaging_cuft)
        else:
            self.floor_total_case_40 = 0.0

    floor_total_case_40 = fields.Float(string="Total Cases", compute="_compute_floor_total_case_40", tracking=True)

    @api.depends('floor_total_case_40', 'packaging_cuft')
    def _compute_floor_cu_ft_40(self):
        if self.packaging_cuft:
            self.floor_cu_ft_40 = self.floor_total_case_40 * self.packaging_cuft
        else:
            self.floor_cu_ft_40 = 0.0

    floor_cu_ft_40 = fields.Float(string="Cu Ft", compute="_compute_floor_cu_ft_40", tracking=True)

    @api.depends('floor_total_case_40', 'packaging_weight')
    def _compute_floor_weight_40(self):
        self.floor_weight_40 = self.floor_total_case_40 * self.packaging_weight

    floor_weight_40 = fields.Float(string="Weight", compute="_compute_floor_weight_40", tracking=True)

    @api.depends('floor_total_case_40', 'pallet_exclude_qty')
    def _compute_pallet_total_40(self):
        self.pallet_total_40 = math.ceil(
            self.floor_total_case_40 / self.pallet_exclude_qty) if self.pallet_exclude_qty else 0.0

    pallet_total_40 = fields.Float(string="Total Pallet", compute="_compute_pallet_total_40", tracking=True)

    # pallet_total_40 = fields.Float(string="Total Pallet")

    @api.depends('pallet_include_cuft', 'pallet_total_20')
    def _compute_pallet_cu_ft_40(self):
        self.pallet_cu_ft_40 = self.pallet_total_40 * self.pallet_include_cuft

    pallet_cu_ft_40 = fields.Float(string="Cu Ft", compute='_compute_pallet_cu_ft_40', tracking=True)

    # pallet_cu_ft_40 = fields.Float(string="Cu Ft")

    @api.depends('pallet_include_weight', 'pallet_total_40')
    def _compute_pallet_weight_40(self):
        self.pallet_weight_40 = round(self.pallet_include_weight * self.pallet_total_40)

    pallet_weight_40 = fields.Float(string="Weight", compute='_compute_pallet_weight_40', tracking=True)

    # pallet_weight_40 = fields.Float(string="Weight")

    @api.depends('cu_ft_40_hc', 'packaging_cuft')
    def _compute_floor_total_case_40_hc(self):
        if self.packaging_cuft:
            self.floor_total_case_40_hc = round(self.cu_ft_40_hc / self.packaging_cuft)
        else:
            self.floor_total_case_40_hc = 0.0

    floor_total_case_40_hc = fields.Float(string="Total Cases", compute="_compute_floor_total_case_40_hc",
                                          digits=(12, 3), tracking=True)

    @api.depends('floor_total_case_40_hc', 'packaging_cuft')
    def _compute_floor_cu_ft_40_hc(self):
        if self.packaging_cuft:
            self.floor_cu_ft_40_hc = self.floor_total_case_40_hc * self.packaging_cuft
        else:
            self.floor_cu_ft_40_hc = 0.0

    floor_cu_ft_40_hc = fields.Float(string="Cu Ft", compute="_compute_floor_cu_ft_40_hc", tracking=True)

    @api.depends('floor_total_case_40_hc', 'packaging_weight')
    def _compute_floor_weight_40_hc(self):
        if self.packaging_weight:
            self.floor_weight_40_hc = self.floor_total_case_40_hc * self.packaging_weight
        else:
            self.floor_weight_40_hc = 0.0

    floor_weight_40_hc = fields.Float(string="Weight", compute="_compute_floor_weight_40_hc", tracking=True)

    @api.depends('floor_total_case_40_hc', 'pallet_exclude_qty')
    def _compute_pallet_total_40_hc(self):
        self.pallet_total_40_hc = math.ceil(
            self.floor_total_case_40_hc / self.pallet_exclude_qty) if self.pallet_exclude_qty else 0.0

    pallet_total_40_hc = fields.Float(string="Total Pallet", compute="_compute_pallet_total_40_hc", tracking=True)

    # pallet_total_40_hc = fields.Float(string="Total Pallet")

    @api.depends('pallet_include_cuft', 'pallet_total_40_hc')
    def _compute_pallet_cu_ft_40_hc(self):
        self.pallet_cu_ft_40_hc = self.pallet_total_40_hc * self.pallet_include_cuft

    pallet_cu_ft_40_hc = fields.Float(string="Cu Ft", compute='_compute_pallet_cu_ft_40_hc', tracking=True)

    # pallet_cu_ft_40_hc = fields.Float(string="Cu Ft")

    @api.depends('pallet_include_weight', 'pallet_total_40_hc')
    def _compute_pallet_weight_40_hc(self):
        self.pallet_weight_40_hc = round(self.pallet_include_weight * self.pallet_total_40_hc)

    pallet_weight_40_hc = fields.Float(string="Weight", compute='_compute_pallet_weight_40_hc', tracking=True)
    # pallet_weight_40_hc = fields.Float(string="Weight")

    freight_rate_ft_20 = fields.Float(string='20 Ft.', tracking=True)
    freight_rate_ft_40 = fields.Float(string='40 Ft.', tracking=True)
    freight_rate_ft_40_hc = fields.Float(string='40 Ft. HC', tracking=True)

    @api.depends('pay_load_lbs_ft_40', 'packaging_weight')
    def _compute_floor_load_units(self):
        if self.packaging_weight:
            self.pro_floor_load_units = self.floor_load_units = round(self.pay_load_lbs_ft_40 / self.packaging_weight)
        else:
            self.pro_floor_load_units = 0.0
            self.floor_load_units = 0.0

    floor_load_units = fields.Float(string="Units", compute='_compute_floor_load_units', tracking=True)

    @api.depends('floor_load_units', 'packaging_cuft')
    def _compute_floor_load_cuft(self):
        if self.packaging_cuft:
            self.floor_load_cuft = self.pro_floor_load_cuft = math.ceil(self.floor_load_units * self.packaging_cuft)
        else:
            self.floor_load_cuft = 0.0
            self.pro_floor_load_cuft = 0.0

    floor_load_cuft = fields.Float(string="Cu Ft", compute='_compute_floor_load_cuft', tracking=True)

    # floor_load_cuft = fields.Float(string="Cu Ft")

    @api.depends('floor_load_units', 'packaging_weight')
    def _compute_floor_load_weight(self):
        if self.packaging_weight:
            self.floor_load_weight = self.pro_floor_load_weight = self.floor_load_units * self.packaging_weight
        else:
            self.floor_load_weight = 0.0
            self.pro_floor_load_weight = 0.0

    floor_load_weight = fields.Float(string="Weight", compute='_compute_floor_load_weight', tracking=True)

    # floor_load_weight = fields.Float(string="Weight")

    @api.depends('pallet_exclude_qty', 'packaging_qty')
    def _compute_storage_load_units(self):
        self.storage_load_units = self.pro_storage_load_units = self.pallet_exclude_qty * self.packaging_qty

    storage_load_units = fields.Float(string="Units", compute='_compute_storage_load_units', tracking=True)

    @api.depends('floor_load_units', 'storage_load_units')
    def _compute_storage_pallet_no(self):
        if self.storage_load_units:
            self.pro_storage_pallet_no = self.storage_pallet_no = math.ceil(
                self.floor_load_units / self.storage_load_units)
        else:
            self.pro_storage_pallet_no = 0.0
            self.storage_pallet_no = 0.0

    storage_pallet_no = fields.Float(string="No of Pallets", compute="_compute_storage_pallet_no", tracking=True)

    # storage_pallet_no = fields.Float(string="No of Pallets")

    @api.depends('storage_pallet_no', 'pallet_include_cuft')
    def _compute_storage_load_cuft(self):
        if self.pallet_include_cuft:
            self.pro_storage_load_cuft = self.storage_load_cuft = self.storage_pallet_no * self.pallet_include_cuft
        else:
            self.pro_storage_load_cuft = self.storage_load_cuft = 0.0

    storage_load_cuft = fields.Float(string="Cu Ft", compute="_compute_storage_load_cuft", tracking=True)

    # storage_load_cuft = fields.Float(string="Cu Ft")

    @api.depends('storage_pallet_no', 'pallet_include_weight')
    def _compute_storage_load_weight(self):
        self.pro_storage_load_weight = self.storage_load_weight = math.ceil(
            self.storage_pallet_no * self.pallet_include_weight)

    storage_load_weight = fields.Float(string="Weight", compute='_compute_storage_load_weight', tracking=True)
    # storage_load_weight = fields.Float(string="Weight")

    pro_container_type = fields.Char(string="Container Type", tracking=True)

    pro_floor_load_units = fields.Float(string="Units", compute='_compute_floor_load_units', tracking=True)
    # pro_floor_load_units = fields.Float(string="Units")

    pro_floor_load_cuft = fields.Float(string="Cu Ft", compute="_compute_floor_load_cuft", tracking=True)
    # pro_floor_load_cuft = fields.Float(string="Cu Ft")

    pro_floor_load_weight = fields.Float(string="Weight", compute="_compute_floor_load_weight", tracking=True)
    # pro_floor_load_weight = fields.Float(string="Weight")

    pro_storage_load_units = fields.Float(string="Units", compute="_compute_storage_load_units", tracking=True)
    # pro_storage_load_units = fields.Float(string="Units")
    pro_storage_pallet_no = fields.Float(string="No of Pallets", compute="_compute_storage_pallet_no", tracking=True)
    # pro_storage_pallet_no = fields.Float(string="No of Pallets")
    pro_storage_load_cuft = fields.Float(string="Cu Ft", compute='_compute_storage_load_cuft', tracking=True)
    # pro_storage_load_cuft = fields.Float(string="Cu Ft")
    pro_storage_load_weight = fields.Float(string="Weight", compute='_compute_storage_load_weight', tracking=True)
    # pro_storage_load_weight = fields.Float(string="Weight")

    export_price_ids = fields.One2many('export.fob.price', 'product_development_id', string="Importation Cost List",
                                       tracking=True)
    importation_cost_ids = fields.One2many('importation.cost', 'product_development_id', string="Importation Cost",
                                           tracking=True)
    storage_cost_ids = fields.One2many('storage.cost', 'product_development_id', string="Storage Cost List",
                                       tracking=True)
    material_cost_ids = fields.One2many('material.cost', 'product_development_id', string="Material Cost List",
                                        tracking=True)

    @api.depends('export_price_ids')
    def _compute_importation_cost(self):
        for rec in self:
            rec.importation_cost = rec.export_price_ids and sum(rec.export_price_ids.mapped('cost')) or 0

    importation_cost = fields.Float(string="Cost", compute='_compute_importation_cost', tracking=True)

    @api.depends('export_fob_price', 'importation_cost')
    def _compute_importation_percentage(self):
        self.importation_percentage = round((self.importation_cost / self.export_fob_price) * 100,
                                            1) if self.export_fob_price else 0.0

    importation_percentage = fields.Float(string="Percentage", compute="_compute_importation_percentage", tracking=True)

    @api.depends('mark_up_cost', 'importation_cost', 'processing_cost')
    def _compute_total_importation_cost(self):
        self.total_importation_cost = round(self.mark_up_cost + self.importation_cost + self.processing_cost, 3)

    total_importation_cost = fields.Float(string="Total Importation Cost", digits=(12, 2),
                                          help="Include total cost of Mark up/Commision, Total export FOB Price, Processing Fees",
                                          compute='_compute_total_importation_cost', tracking=True)

    @api.depends('total_importation_cost', 'export_fob_price')
    def _compute_total_importation_percentage(self):
        self.total_importation_percentage = (
                                                    self.total_importation_cost / self.export_fob_price) * 100 if self.export_fob_price else 0.0

    total_importation_percentage = fields.Float(string="Total Importation Percentage", digits=(12, 2),
                                                compute='_compute_total_importation_percentage', tracking=True)

    @api.depends('storage_cost_ids')
    def _compute_storage_cost(self):
        for rec in self:
            rec.storage_cost = rec.storage_cost_ids and sum(rec.storage_cost_ids.mapped('cost')) or 0

    storage_cost = fields.Float(string="Total Storage Fees", compute="_compute_storage_cost", tracking=True)

    @api.depends('storage_cost')
    def _compute_storage_percentage(self):
        self.storage_percentage = (self.storage_cost / self.export_fob_price) * 100 if self.export_fob_price else 0.0

    storage_percentage = fields.Float(string="Total Storage Percentage", compute='_compute_storage_percentage',
                                      tracking=True)

    @api.depends('material_cost_ids')
    def _compute_material_cost(self):
        for rec in self:
            rec.material_cost = rec.material_cost_ids and sum(rec.material_cost_ids.mapped('cost')) or 0

    material_cost = fields.Float(string="Total Material Cost", compute='_compute_material_cost', tracking=True)

    @api.depends('material_cost')
    def _compute_material_percentage(self):
        self.material_percentage = (self.material_cost / self.export_fob_price) * 100 if self.export_fob_price else 0.0

    material_percentage = fields.Float(string="Total Material Percentage", compute='_compute_material_percentage',
                                       tracking=True)

    @api.depends('export_fob_price', 'total_importation_cost', 'storage_cost', 'material_cost')
    def _compute_total_cost(self):
        self.total_cost = self.warefor_cost = self.export_fob_price + self.total_importation_cost + self.storage_cost + self.material_cost

    total_cost = fields.Float(string="Total Cost", compute='_compute_total_cost', tracking=True)

    # total_cost = fields.Float(string="Total Cost")

    @api.depends('importation_cost')
    def _compute_processing_cost(self):
        """ Warefor Logistics Processing Fees @ 10.00 % by default  """
        self.processing_cost = round(0.10 * self.importation_cost, 2) if self.importation_cost else 0.0

    processing_cost = fields.Float(string="Cost", compute="_compute_processing_cost", tracking=True)

    @api.depends('processing_cost')
    def _compute_processing_percentage(self):
        self.processing_percentage = round((self.processing_cost / self.export_fob_price) * 100,
                                           2) if self.export_fob_price else 0.0

    processing_percentage = fields.Float(string="Percentage", compute='_compute_processing_percentage', tracking=True)

    warefor_cost = fields.Float(string="Warefor Cost", compute='_compute_total_cost', tracking=True)

    @api.depends('warefor_cost', 'wholesale_price')
    def _compute_warefor_margin_cost(self):
        if self.wholesale_price > 0.0 and self.warefor_cost > 0.0:
            self.warefor_margin_cost = self.wholesale_price - self.warefor_cost
        else:
            self.warefor_margin_cost = 0.0

    warefor_margin_cost = fields.Float(string="Margin Cost", compute="_compute_warefor_margin_cost", tracking=True)

    @api.depends('wholesale_price', 'warefor_cost')
    def _compute_warefor_margin_per(self):
        self.warefor_margin_per = (1 - (
                self.warefor_cost / self.wholesale_price)) * 100 if self.wholesale_price else 0.0

    warefor_margin_per = fields.Float(string="Margin Percentage", compute='_compute_warefor_margin_per', tracking=True)

    @api.depends('total_cost', 'wholesale_price')
    def _compute_warefor_mark_up(self):
        self.warefor_mark_up = ((self.wholesale_price / self.total_cost) - 1) * 100 if self.total_cost else 0.0

    warefor_mark_up = fields.Float(string="Mark Up", compute='_compute_warefor_mark_up', tracking=True)

    wholesale_price = fields.Float(string="Wholesale price", tracking=True)

    @api.depends('wholesale_price', 'retail_price')
    def _compute_wholesale_margin_cost(self):
        if self.wholesale_price > 0.0 and self.retail_price > 0.0:
            self.wholesale_margin_cost = self.retail_price - self.wholesale_price
        else:
            self.wholesale_margin_cost = 0.0

    wholesale_margin_cost = fields.Float(string="Margin Cost", compute='_compute_wholesale_margin_cost', tracking=True)

    @api.depends('wholesale_price', 'retail_price')
    def _compute_wholesale_margin_per(self):
        if self.wholesale_price > 0.0 and self.retail_price > 0.0:
            self.wholesale_margin_per = (1 - (self.wholesale_price / self.retail_price)) * 100
        else:
            self.wholesale_margin_per = 0.0

    wholesale_margin_per = fields.Float(string="Margin Percentage", compute="_compute_wholesale_margin_per",
                                        tracking=True)

    @api.depends('wholesale_price', 'retail_price')
    def _compute_wholesale_mark_up(self):
        self.wholesale_mark_up = (self.retail_price / self.wholesale_price - 1) * 100 if self.wholesale_price else 0.0

    wholesale_mark_up = fields.Float(string="Mark Up", compute="_compute_wholesale_mark_up", tracking=True)

    country_to_pricesmart = fields.Char(string="Country of Origin that will be delivered to PriceSmart.", tracking=True)
    multi_country_parts = fields.Selection(selection=[('no', 'No'), ('yes', 'Yes'), ('na', 'NA')],
                                           string="Does product contain parts /ingredients from multiple Countries of origin?",
                                           tracking=True)
    is_ocountry_print = fields.Selection(selection=[('no', 'No'), ('yes', 'Yes'), ('na', 'NA')],
                                         string="Is Country of Origin printed on Packaging?", tracking=True)
    packaging_eng_n_spn = fields.Selection(selection=[('no', 'No'), ('yes', 'Yes'), ('na', 'NA')],
                                           string="Is PACKAGING in English and Spanish?", tracking=True)
    is_manual_bilingual = fields.Selection(selection=[('no', 'No'), ('yes', 'Yes'), ('na', 'NA')],
                                           string="Are Manuals Bi-Lingual in English and Spanish?", tracking=True)
    is_label_printed = fields.Selection(selection=[('no', 'No'), ('yes', 'Yes'), ('na', 'NA')],
                                        string="Compliance Labeling pre-printed on product?", tracking=True)
    is_licensed = fields.Selection(selection=[('no', 'No'), ('yes', 'Yes'), ('na', 'NA')],
                                   string="Is the product LICENSED?", tracking=True)
    licensed_applied_country = fields.Char(string="License applicable to which countries?", tracking=True)
    item_lot_num = fields.Selection(selection=[('no', 'No'), ('yes', 'Yes'), ('na', 'NA')],
                                    string="Does item have a Lot number? (Y/N)", tracking=True)
    hazmat_appl = fields.Boolean(string="HAZMAT Applicable", tracking=True)
    hazmat_code = fields.Char(string="HAZMAT Code", tracking=True)
    shipping_config = fields.Char(string="Product Shipping Configuration", tracking=True)
    pallet_protected = fields.Char(string="If palletized how is pallet protected?", tracking=True)
    double_stackable = fields.Selection(selection=[('no', 'No'), ('yes', 'Yes'), ('na', 'NA')],
                                        string="Product Double Stackable (Y/N)", tracking=True)

    uom_case = fields.Char(string="UOM - Ea. Per case", tracking=True)
    uom_layer = fields.Char(string="UOM - Ea. Per layer", tracking=True)
    uom_pallet = fields.Char(string="UOM - Ea. Per Pallet", tracking=True)
    uom_pallet_layer = fields.Char(string="UOM - Pallet - How many layers (High)", tracking=True)

    invoice_uom_id = fields.Many2one('uom.uom', string="Invoice Unit of Measure", tracking=True)
    currency_code_payment = fields.Many2one('res.currency', string="Currency code used for Purchase/Payment",
                                            tracking=True)
    vendor_min_qty = fields.Integer(string="Vendor Minimum production/Order Qty- each", tracking=True)
    shipping_method = fields.Selection(
        selection=[('ocean', 'Ocean'), ('air', 'Air'), ('road', 'Over the Road'), ('rail', 'Rail')],
        string="Preferred Shipping method", tracking=True)
    equipment_type = fields.Selection(
        selection=[('53t_53f_trailer', '53T-53ft Trailer'), ('air_shipment', 'AIR-Air Shipment')],
        string="Equipment type", help="Please provide Supplier Shipping Information//Equipment type value here",
        tracking=True)
    vendor_lead_time = fields.Date(string="Item vendor lead time- 1st shipment Days", tracking=True)

    dimension_height = fields.Float(string="Shipping Product Dimension- Height (Inches)", tracking=True)
    dimension_length = fields.Float(string="Shipping Product Dimension- Length (Inches)", tracking=True)
    dimension_width = fields.Float(string="Shipping Product Dimension- Width (Inches)", tracking=True)

    def print_product_dev_report(self):
        # Get Report Data
        report_data = self.get_report_data()

        # Prepare Excel Report
        report_file_name = self.prepare_excel_report(report_data)

        # Create Attachment
        attachment = self.create_attachment(report_file_name)

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'download',
        }

    def get_report_data(self):
        """
        Execute SQL Query to Get Report Data
        :return: Data -> List of Dict [{}]
        """

        #         sql_query_current_assets = """SELECT
        #                         sum(aml.debit - aml.credit) as balance, ac.account_type as account_type, ac.name as name
        #                         from account_move_line  as aml
        #                          LEFT JOIN account_account as ac ON ac.id = aml.account_id
        #                         where aml.parent_state='posted' group by ac.account_type, ac.name order by ac.name
        #
        #                                  """
        #
        #         self.env.cr.execute(sql_query_current_assets)
        #         query_rec_current_assets = self.env.cr.dictfetchall()
        #
        #         sql_query_current_assets_count = """SELECT
        #                                     count(id), account_type from account_account group by account_type
        #                         """
        #
        #         self.env.cr.execute(sql_query_current_assets_count)
        #         query_rec_current_assets_count = self.env.cr.dictfetchall()
        #         print("query_rec_current_assets_countquery_rec_current_assets_countquery_rec_current_assets_count",query_rec_current_assets_count)
        #         return[query_rec_current_assets,query_rec_current_assets_count]
        return []

    def prepare_excel_report(self, report_data):
        file_name = '/tmp/walmart_report.xlsx'
        workbook = xlsxwriter.Workbook(file_name)
        worksheet = workbook.add_worksheet()
        worksheet.screen_gridlines = False

        worksheet.set_landscape()

        worksheet.fit_to_pages(1, 0)
        worksheet.set_zoom(80)

        worksheet.set_column(0, 0, 2)
        worksheet.set_column(1, 1, 2)
        worksheet.set_column(2, 2, 5)
        worksheet.set_column(3, 3, 2)
        worksheet.set_column(4, 4, 2)
        worksheet.set_column(5, 5, 2)
        worksheet.set_column(6, 6, 2)
        worksheet.set_column(7, 7, 5)
        worksheet.set_column(8, 8, 2)
        worksheet.set_column(9, 9, 2)
        worksheet.set_column(10, 10, 2)
        worksheet.set_column(11, 11, 5)
        worksheet.set_column(12, 12, 2)
        worksheet.set_column(13, 13, 2)
        worksheet.set_column(14, 14, 2)
        worksheet.set_column(15, 15, 2)
        worksheet.set_column(16, 16, 2)
        worksheet.set_column(17, 17, 2)
        worksheet.set_column(18, 18, 2)
        worksheet.set_column(19, 19, 2)
        worksheet.set_column(20, 20, 2)

        worksheet.set_column(21, 21, 2)
        worksheet.set_column(22, 22, 2)
        worksheet.set_column(23, 23, 2)
        worksheet.set_column(24, 24, 2)
        worksheet.set_column(25, 25, 2)
        worksheet.set_column(26, 26, 2)
        worksheet.set_column(27, 27, 2)
        worksheet.set_column(28, 28, 2)
        worksheet.set_column(29, 29, 2)
        worksheet.set_column(30, 30, 2)

        worksheet.set_column(31, 31, 2)
        worksheet.set_column(32, 32, 2)
        worksheet.set_column(33, 33, 2)
        worksheet.set_column(34, 34, 2)
        worksheet.set_column(35, 35, 2)
        worksheet.set_column(36, 36, 2)
        worksheet.set_column(37, 37, 2)
        worksheet.set_column(38, 38, 2)
        worksheet.set_column(39, 39, 2)
        worksheet.set_column(40, 40, 2)

        worksheet.set_column(41, 41, 2)
        worksheet.set_column(42, 42, 2)
        worksheet.set_column(43, 43, 2)
        worksheet.set_column(44, 44, 2)
        worksheet.set_column(45, 45, 2)
        worksheet.set_column(46, 46, 2)
        worksheet.set_column(47, 47, 2)
        worksheet.set_column(48, 48, 2)
        worksheet.set_column(49, 49, 2)
        worksheet.set_column(50, 50, 2)

        worksheet.set_column(51, 51, 2)
        worksheet.set_column(52, 52, 2)
        worksheet.set_column(53, 53, 2)
        worksheet.set_column(54, 54, 2)
        worksheet.set_column(55, 55, 2)
        worksheet.set_column(56, 56, 2)
        worksheet.set_column(57, 57, 2)
        worksheet.set_column(58, 58, 2)
        worksheet.set_column(59, 59, 2)
        worksheet.set_column(60, 60, 2)

        worksheet.set_column(61, 61, 2)
        worksheet.set_column(62, 62, 2)
        worksheet.set_column(63, 63, 2)
        worksheet.set_column(64, 64, 2)

        worksheet.set_row(0, 30)
        worksheet.set_row(1, 30)
        worksheet.set_row(2, 30)
        worksheet.set_row(4, 30)
        worksheet.set_row(5, 25)
        worksheet.set_row(6, 25)
        worksheet.set_row(7, 25)
        worksheet.set_row(8, 25)
        worksheet.set_row(9, 25)
        worksheet.set_row(10, 25)
        worksheet.set_row(11, 25)
        worksheet.set_row(12, 25)
        worksheet.set_row(13, 25)
        worksheet.set_row(14, 25)
        worksheet.set_row(15, 25)
        worksheet.set_row(16, 25)
        worksheet.set_row(17, 25)
        worksheet.set_row(18, 25)
        worksheet.set_row(29, 25)
        worksheet.set_row(30, 25)
        worksheet.set_row(31, 25)
        worksheet.set_row(32, 25)
        worksheet.set_row(33, 25)
        worksheet.set_row(34, 25)
        worksheet.set_row(35, 25)
        worksheet.set_row(36, 25)
        worksheet.set_row(37, 25)
        worksheet.set_row(38, 25)
        worksheet.set_row(39, 25)
        worksheet.set_row(40, 25)
        worksheet.set_row(41, 25)
        worksheet.set_row(42, 25)
        worksheet.set_row(43, 25)
        worksheet.set_row(44, 25)
        worksheet.set_row(45, 25)
        worksheet.set_row(46, 25)
        worksheet.set_row(47, 25)
        worksheet.set_row(48, 25)
        worksheet.set_row(49, 25)
        worksheet.set_row(50, 15)
        worksheet.set_row(51, 15)
        worksheet.set_row(52, 25)
        worksheet.set_row(53, 25)
        worksheet.set_row(54, 25)
        worksheet.set_row(55, 25)
        worksheet.set_row(56, 25)
        worksheet.set_row(57, 25)
        worksheet.set_row(58, 25)
        worksheet.set_row(59, 25)
        worksheet.set_row(60, 25)
        worksheet.set_row(61, 25)
        worksheet.set_row(62, 25)
        worksheet.set_row(63, 25)
        worksheet.set_row(64, 25)
        worksheet.set_row(65, 25)
        worksheet.set_row(66, 25)
        worksheet.set_row(67, 25)
        worksheet.set_row(68, 25)
        worksheet.set_row(69, 25)
        worksheet.set_row(70, 25)
        worksheet.set_row(71, 25)
        worksheet.set_row(72, 25)
        worksheet.set_row(73, 25)
        worksheet.set_row(74, 25)
        worksheet.set_row(75, 25)
        worksheet.set_row(76, 25)
        worksheet.set_row(77, 25)
        worksheet.set_row(78, 25)
        worksheet.set_row(79, 25)
        worksheet.set_row(80, 25)
        worksheet.set_row(81, 25)
        worksheet.set_row(82, 15)
        worksheet.set_row(83, 15)
        worksheet.set_row(84, 15)
        worksheet.set_row(85, 15)
        worksheet.set_row(86, 15)
        worksheet.set_row(87, 15)
        worksheet.set_row(88, 15)
        worksheet.set_row(89, 15)
        worksheet.set_row(90, 15)
        worksheet.set_row(91, 15)
        worksheet.set_row(92, 15)
        worksheet.set_row(93, 15)
        worksheet.set_row(94, 15)
        worksheet.set_row(95, 15)
        worksheet.set_row(96, 25)
        worksheet.set_row(97, 25)
        worksheet.set_row(98, 25)
        worksheet.set_row(99, 25)
        worksheet.set_row(100, 25)
        worksheet.set_row(101, 25)
        worksheet.set_row(102, 25)
        worksheet.set_row(103, 25)
        worksheet.set_row(104, 25)
        worksheet.set_row(105, 25)
        worksheet.set_row(106, 25)
        worksheet.set_row(107, 25)
        worksheet.set_row(108, 25)
        worksheet.set_row(109, 25)
        worksheet.set_row(110, 25)
        worksheet.set_row(111, 25)
        worksheet.set_row(112, 25)
        worksheet.set_row(113, 25)
        worksheet.set_row(114, 25)
        worksheet.set_row(115, 25)
        worksheet.set_row(116, 25)
        worksheet.set_row(117, 25)
        worksheet.set_row(118, 25)
        worksheet.set_row(119, 25)
        worksheet.set_row(120, 25)
        worksheet.set_row(121, 25)
        worksheet.set_row(122, 25)
        worksheet.set_row(123, 25)
        worksheet.set_row(124, 25)
        worksheet.set_row(125, 25)
        worksheet.set_row(126, 25)
        worksheet.set_row(127, 15)
        worksheet.set_row(128, 15)
        worksheet.set_row(129, 15)
        worksheet.set_row(130, 15)
        worksheet.set_row(131, 15)
        worksheet.set_row(132, 15)
        worksheet.set_row(133, 15)
        worksheet.set_row(134, 15)
        worksheet.set_row(135, 25)
        worksheet.set_row(136, 25)
        worksheet.set_row(137, 25)
        worksheet.set_row(138, 25)
        worksheet.set_row(139, 25)
        worksheet.set_row(140, 25)
        worksheet.set_row(141, 25)
        worksheet.set_row(142, 25)
        worksheet.set_row(143, 25)
        worksheet.set_row(144, 25)
        worksheet.set_row(145, 25)
        worksheet.set_row(146, 25)
        worksheet.set_row(147, 25)
        worksheet.set_row(148, 25)
        worksheet.set_row(149, 25)
        worksheet.set_row(150, 25)
        worksheet.set_row(151, 25)
        worksheet.set_row(152, 25)
        worksheet.set_row(153, 25)
        worksheet.set_row(154, 25)
        worksheet.set_row(155, 25)
        worksheet.set_row(156, 25)
        worksheet.set_row(157, 25)
        worksheet.set_row(158, 25)
        worksheet.set_row(159, 25)
        worksheet.set_row(160, 25)

        first_row_format = workbook.add_format(
            {'bold': 1, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFFFF'})
        costs_extra_format = workbook.add_format(
            {'bold': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFFFF'})
        first_row_format_1 = workbook.add_format(
            {'bold': 1, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#696969'})
        data_format = workbook.add_format(
            {'bold': 1, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'color': 'blue'})
        data_format_2 = workbook.add_format(
            {'border': 1, 'align': 'center', 'valign': 'vcenter', 'color': 'blue'})
        data_format_1 = workbook.add_format(
            {'border': 1, 'align': 'center', 'valign': 'vcenter', 'color': 'black'})
        address_format = workbook.add_format(
            {'bold': 1, 'border': 1, 'align': 'left', 'valign': 'vcenter', 'color': 'blue'})
        worksheet.merge_range('B1:BM1', 'COMP SHOP & COST CALCULATION', first_row_format)

        """ 2 to 4 row """
        worksheet.merge_range('B2:G2', 'Date:', first_row_format)
        # worksheet.merge_range('H2:V2', 'February 23, 2021', first_row_format)
        worksheet.merge_range('B3:G4', 'Prepared By:', first_row_format)
        # worksheet.merge_range('H3:V4', 'Warefor Logistics', first_row_format)
        # worksheet.merge_range('W2:AR4', 'Image', first_row_format)
        worksheet.merge_range('AS2:BM2', 'Store Location:', first_row_format)
        # worksheet.merge_range('AS3:BM4', "2727 Dunvale Rd - Houston, TX 77063 Also Available Online",
        #                       first_row_format)

        worksheet.merge_range('B5:P5', 'Item Illustration:', first_row_format_1)
        worksheet.merge_range('Q5:AX5', 'Product Information:', first_row_format_1)
        worksheet.merge_range('AY5:BM5', 'Retail Price:', first_row_format_1)

        """6 to 13 row"""
        # worksheet.merge_range('B6:P13', 'Image', first_row_format)
        worksheet.merge_range('Q6:V6', 'UPC #:', first_row_format)
        # worksheet.merge_range('W6:AX6', '084897427708', first_row_format)
        worksheet.merge_range('Q7:V7', 'Description:', first_row_format)
        # worksheet.merge_range('W7:AX7', '12 Pc Dinnerware Set- AVA Stoneware Collection', first_row_format)
        worksheet.merge_range('Q8:V8', 'Material:', first_row_format)
        # worksheet.merge_range('W8:AX8', 'STONEWARE', first_row_format)
        worksheet.merge_range('Q9:V9', 'Brand:', first_row_format)
        # worksheet.merge_range('W9:AX9', 'THYME & TABLE', first_row_format)
        worksheet.merge_range('Q10:V10', 'Made By:', first_row_format)
        # worksheet.merge_range('W10:AX10', 'DESIGNED BY THYME & TABLE - NEW YORK', first_row_format)
        worksheet.merge_range('Q11:V11', 'Made In:', first_row_format)
        # worksheet.merge_range('W11:AX11', 'China', first_row_format)
        worksheet.merge_range('Q12:V13', 'Comments:', first_row_format)
        # worksheet.merge_range('W12:AX13', 'Dishwasher & Microwave Safe', first_row_format)
        # worksheet.merge_range('AY6:BM9', '$39.92', first_row_format)
        worksheet.merge_range('AY10:BM13', '12 Pc', first_row_format)
        worksheet.merge_range('B14:BM14', '', first_row_format)

        """15 row """
        worksheet.merge_range('B15:BM15', 'Packaging & Pallet Information - Cube & Weight', first_row_format_1)

        """ 17 to 29 row """
        worksheet.merge_range('B16:BM16', '')
        worksheet.merge_range('G17:AD29', 'Image', first_row_format)
        worksheet.merge_range('AK17:BH29', 'Image', first_row_format)

        """ Table  Packaging Dimensions & Weights"""
        """Header"""
        worksheet.merge_range('G30:AD30', 'Packaging Dimensions & Weights', first_row_format_1)
        worksheet.merge_range('G31:AD31', 'Retail Color Packaging', first_row_format_1)
        worksheet.merge_range('G32:J32', 'Qty', first_row_format)
        worksheet.merge_range('K32:N32', 'W', first_row_format)
        worksheet.merge_range('O32:R32', 'D', first_row_format)
        worksheet.merge_range('S32:V32', 'H', first_row_format)
        worksheet.merge_range('W32:Z32', 'CuFt', first_row_format)
        worksheet.merge_range('AA32:AD32', 'Weight', first_row_format)
        """Data Body"""
        # worksheet.merge_range('G33:J33', '1', first_row_format)
        # worksheet.merge_range('K33:N33', '10.875', first_row_format)
        # worksheet.merge_range('O33:R33', '12.500', first_row_format)
        # worksheet.merge_range('S33:V33', '11.125', first_row_format)
        # worksheet.merge_range('W33:Z33', '0.875', first_row_format)
        # worksheet.merge_range('AA33:AD33', '16.700', first_row_format)

        """ Table  Pallet Dimensions & Weights"""
        """Header"""
        worksheet.merge_range('AK30:BH30', 'Pallet Dimensions & Weights', first_row_format_1)
        worksheet.merge_range('AK31:BH31', '(Excluding Pallet)', first_row_format_1)
        worksheet.merge_range('AK32:AN32', 'Qty *', first_row_format)
        worksheet.merge_range('AO32:AP32', 'W', first_row_format)
        worksheet.merge_range('AQ32:AR32', '4', first_row_format)
        worksheet.merge_range('AS32:AT32', 'D', first_row_format)
        worksheet.merge_range('AU32:AV32', '3', first_row_format)
        worksheet.merge_range('AW32:AX32', 'H', first_row_format)
        worksheet.merge_range('AY32:AZ32', '4', first_row_format)
        worksheet.merge_range('BA32:BD32', 'CuFt', first_row_format)
        worksheet.merge_range('BE32:BH32', 'Weight', first_row_format)
        """Data Body"""
        # worksheet.merge_range('AK33:AN33', '48', first_row_format)
        # worksheet.merge_range('AO33:AR33', '43.500', first_row_format)
        # worksheet.merge_range('AS33:AV33', '37.500', first_row_format)
        # worksheet.merge_range('AW33:AZ33', '44.500', first_row_format)
        # worksheet.merge_range('BA33:BD33', '42.008', first_row_format)
        # worksheet.merge_range('BE33:BH33', '801.6', first_row_format)

        """Table  Remailer Packaging"""
        """Header"""
        worksheet.merge_range('B34:BM34', '')
        worksheet.merge_range('G35:AD35', 'Remailer Packaging', first_row_format_1)
        worksheet.merge_range('G36:J36', 'Qty', first_row_format)
        worksheet.merge_range('K36:N36', 'W', first_row_format)
        worksheet.merge_range('O36:R36', 'D', first_row_format)
        worksheet.merge_range('S36:V36', 'H', first_row_format)
        worksheet.merge_range('W36:Z36', 'CuFt', first_row_format)
        worksheet.merge_range('AA36:AD36', 'Weight', first_row_format)
        """Data Body"""
        # worksheet.merge_range('G37:J37', '', first_row_format)
        # worksheet.merge_range('K37:N37', '', first_row_format)
        # worksheet.merge_range('O37:R37', '', first_row_format)
        # worksheet.merge_range('S37:V37', '', first_row_format)
        # worksheet.merge_range('W37:Z37', '0.000', first_row_format)
        # worksheet.merge_range('AA37:AD37', '', first_row_format)

        """Table  (Including Pallet)"""
        """Header"""
        worksheet.merge_range('AK35:BH35', '(Including Pallet)', first_row_format_1)
        worksheet.merge_range('AK36:AN36', 'Qty', first_row_format)
        worksheet.merge_range('AO36:AR36', 'W', first_row_format)
        worksheet.merge_range('AS36:AV36', 'D', first_row_format)
        worksheet.merge_range('AW36:AZ36', 'H', first_row_format)
        worksheet.merge_range('BA36:BD36', 'CuFt', first_row_format)
        worksheet.merge_range('BE36:BH36', 'Weight', first_row_format)
        """Data Body"""
        # worksheet.merge_range('AK37:AN37', '48', first_row_format)
        # worksheet.merge_range('AO37:AR37', '48.000', first_row_format)
        # worksheet.merge_range('AS37:AV37', '40.000', first_row_format)
        # worksheet.merge_range('AW37:AZ37', '50.500', first_row_format)
        # worksheet.merge_range('BA37:BD37', '56.111', first_row_format)
        # worksheet.merge_range('BE37:BH37', '861.6', first_row_format)

        """Table  Master Pack"""
        """Header"""
        worksheet.merge_range('B38:BM38', '')
        worksheet.merge_range('G39:AD39', 'Master Pack', first_row_format_1)
        worksheet.merge_range('G40:J40', 'Qty', first_row_format)
        worksheet.merge_range('K40:N40', 'W', first_row_format)
        worksheet.merge_range('O40:R40', 'D', first_row_format)
        worksheet.merge_range('S40:V40', 'H', first_row_format)
        worksheet.merge_range('W40:Z40', 'CuFt', first_row_format)
        worksheet.merge_range('AA40:AD40', 'Weight', first_row_format)
        """Data Body"""
        # worksheet.merge_range('G41:J41', '', first_row_format)
        # worksheet.merge_range('K41:N41', '', first_row_format)
        # worksheet.merge_range('O41:R41', '', first_row_format)
        # worksheet.merge_range('S41:V41', '', first_row_format)
        # worksheet.merge_range('W41:Z41', '0.000', first_row_format)
        # worksheet.merge_range('AA41:AD41', '', first_row_format)

        """ 42 row Blank"""
        worksheet.merge_range('B42:BM42', '')

        """ 43 row """
        worksheet.merge_range('B43:BM43',
                              'Container Load Calculation  - Cube & Weight   US Legal Cargo Weight Limit: 54,000 lbs',
                              first_row_format_1)

        """ 44 row blank"""
        worksheet.merge_range('B44:BM44', '')

        """Table Container Size"""
        """ Header """
        worksheet.merge_range('F45:K45', 'Container Size', first_row_format_1)
        worksheet.merge_range('L45:O45', '20 Ft.', first_row_format_1)
        worksheet.merge_range('P45:S45', '40 Ft.', first_row_format_1)
        worksheet.merge_range('T45:W45', '40 Ft. HC', first_row_format_1)
        """Data Body"""
        """1 row"""
        worksheet.merge_range('F46:K46', 'Cu Ft', first_row_format)
        # worksheet.merge_range('L46:O46', '', first_row_format)
        # worksheet.merge_range('P46:S46', '', first_row_format)
        # worksheet.merge_range('T46:W46', '', first_row_format)
        """2 row"""
        worksheet.merge_range('F47:K47', 'Pay Load (Lbs)', first_row_format)
        # worksheet.merge_range('L47:O47', '', first_row_format)
        # worksheet.merge_range('P47:S47', '', first_row_format)
        # worksheet.merge_range('T47:W47', '', first_row_format)
        """3 row"""
        worksheet.merge_range('F48:K48', 'Cubic Metric', first_row_format)
        # worksheet.merge_range('L48:O48', '', first_row_format)
        # worksheet.merge_range('P48:S48', '', first_row_format)
        # worksheet.merge_range('T48:W48', '', first_row_format)
        """4 row"""
        worksheet.merge_range('F49:K49', 'Pay Load (Kg)', first_row_format)
        # worksheet.merge_range('L49:O49', '', first_row_format)
        # worksheet.merge_range('P49:S49', '', first_row_format)
        # worksheet.merge_range('T49:W49', '', first_row_format)

        """Table Container Size Right side"""
        """ Header """
        worksheet.merge_range('AB45:AG46', 'Container Size', first_row_format)
        worksheet.merge_range('AH45:AU45', 'Floor Loaded', first_row_format_1)
        worksheet.merge_range('AV45:BI45', 'Pallet Loaded', first_row_format_1)
        worksheet.merge_range('AH46:AM46', 'Total Cases', first_row_format)
        worksheet.merge_range('AN46:AQ46', 'Cu Ft', first_row_format)
        worksheet.merge_range('AR46:AU46', 'Weight', first_row_format)
        worksheet.merge_range('AV46:BA46', 'Total Pallets', first_row_format)
        worksheet.merge_range('BB46:BE46', 'Cu Ft', first_row_format)
        worksheet.merge_range('BF46:BI46', 'Weight', first_row_format)
        """Data Body"""
        """1 row"""
        worksheet.merge_range('AB47:AG47', '20 Ft.', first_row_format)
        # worksheet.merge_range('AH47:AM47', '', first_row_format)
        # worksheet.merge_range('AN47:AQ47', '', first_row_format)
        # worksheet.merge_range('AR47:AU47', '', first_row_format)
        # worksheet.merge_range('AV47:BA47', '', first_row_format)
        # worksheet.merge_range('BB47:BE47', '', first_row_format)
        # worksheet.merge_range('BF47:BI47', '', first_row_format)
        """2 row"""
        worksheet.merge_range('AB48:AG48', '40 Ft.', first_row_format)
        # worksheet.merge_range('AH48:AM48', '', first_row_format)
        # worksheet.merge_range('AN48:AQ48', '', first_row_format)
        # worksheet.merge_range('AR48:AU48', '', first_row_format)
        # worksheet.merge_range('AV48:BA48', '', first_row_format)
        # worksheet.merge_range('BB48:BE48', '', first_row_format)
        # worksheet.merge_range('BF48:BI48', '', first_row_format)
        """3 row"""
        worksheet.merge_range('AB49:AG49', '40 Ft. HC', first_row_format)
        # worksheet.merge_range('AH49:AM49', '', first_row_format)
        # worksheet.merge_range('AN49:AQ49', '', first_row_format)
        # worksheet.merge_range('AR49:AU49', '', first_row_format)
        # worksheet.merge_range('AV49:BA49', '', first_row_format)
        # worksheet.merge_range('BB49:BE49', '', first_row_format)
        # worksheet.merge_range('BF49:BI49', '', first_row_format)

        """ 50 row """
        worksheet.merge_range('G50:N50', 'Chep Pallet  Height:', data_format_2)
        worksheet.merge_range('R50:T50', '6 in', data_format_2)
        worksheet.merge_range('AB50:AK50', 'Costco Chep Pallet Weight:', data_format_2)
        worksheet.merge_range('AT50:BE50', 'Sams Club Standard Pallet Weight:', data_format_2)
        worksheet.merge_range('AN50:AQ50', '50 lbs', data_format_2)

        """ 51 row """
        worksheet.merge_range('G51:N51', 'Product Maximum Height:', data_format_2)
        worksheet.merge_range('R51:T51', '48 in', data_format_2)
        worksheet.merge_range('AB51:AK51', 'Costco Chep Pallet Height:', data_format_2)
        # worksheet.merge_range('AO51:AP51', '6 in', data_format_2)
        worksheet.merge_range('AT51:BE51', 'Sams Club Standard Pallet Height:', data_format_2)
        worksheet.merge_range('AN51:AQ51', '5 in', data_format_2)

        """ 52 row """
        worksheet.merge_range('G52:N52', 'Total Pallet Maximum Height:', data_format_2)
        worksheet.merge_range('R52:T52', '54 in', data_format_2)

        """ 53 row Table  BRAZIL - Estimated Ocean Freight Rates """
        worksheet.merge_range('X53:AQ53', 'BRAZIL - Estimated Ocean Freight Rates', first_row_format)
        """54 row Header """
        worksheet.merge_range('X54:AC54', '20 Ft.', first_row_format_1)
        worksheet.merge_range('AD54:AJ54', '40 Ft.', first_row_format_1)
        worksheet.merge_range('AK54:AQ54', '40 Ft. HC', first_row_format_1)

        """55 row Header """
        # worksheet.merge_range('X55:AC55', '', first_row_format)
        # worksheet.merge_range('AD55:AJ55', '', first_row_format)
        # worksheet.merge_range('AK55:AQ55', '', first_row_format)

        """57 row table Info. To be used for Cost Calculation """
        worksheet.merge_range('O57:AZ57', 'Info. To be used for Cost Calculation', first_row_format)
        """58 row Header """
        worksheet.merge_range('O58:T58', 'Container Type', first_row_format_1)
        worksheet.merge_range('U58:AF58', 'Floor Load', first_row_format_1)
        worksheet.merge_range('AJ58:AZ58', 'Palletization for Storage', first_row_format_1)

        worksheet.merge_range('O59:T59', '40 FT.', data_format)
        worksheet.merge_range('U59:X59', 'Units', first_row_format_1)
        worksheet.merge_range('Y59:AB59', 'Cu Ft', first_row_format_1)
        worksheet.merge_range('AC59:AF59', 'Weight', first_row_format_1)
        worksheet.merge_range('AJ59:AM59', 'Units / Pallet', first_row_format_1)
        worksheet.merge_range('AN59:AR59', 'No. of Pallets', first_row_format_1)
        worksheet.merge_range('AS59:AV59', 'CuFt', first_row_format_1)
        worksheet.merge_range('AW59:AZ59', 'Weight', first_row_format_1)
        """ Data Body """
        worksheet.merge_range('O60:T60', '#NAME?', data_format)
        # worksheet.merge_range('U60:X60', '', first_row_format)
        # worksheet.merge_range('Y60:AB60', '', first_row_format)
        # worksheet.merge_range('AC60:AF60', '', first_row_format)
        # worksheet.merge_range('AJ60:AM60', '', first_row_format)
        # worksheet.merge_range('AN60:AR60', '', first_row_format)
        # worksheet.merge_range('AS60:AV60', '', first_row_format)
        # worksheet.merge_range('AW60:AZ60', '', first_row_format)

        """ 62 row """
        worksheet.merge_range('B62:BM62', 'Product Information:', first_row_format_1)

        """ 63 row """
        worksheet.merge_range('B63:H63', 'Set Composition:')
        worksheet.merge_range('K63:X63', 'Size:')
        worksheet.merge_range('AF63:AS63', 'Specifications:')

        """ 64 row """
        worksheet.merge_range('B64:H64', '4 Pc. Dinner Plates ', data_format_2)
        worksheet.merge_range('K64:X64', '12.75 in - (32.38 cm)', data_format_2)
        worksheet.merge_range('AF64:AS64', 'STONEWARE :', data_format)

        """ 65 row """
        worksheet.merge_range('B65:H65', '4 Pc. Slad Plates ', data_format_2)
        worksheet.merge_range('K65:X65', '9.0 in - (22.86 cm)', data_format_2)
        worksheet.merge_range('AF65:AS65', 'Dishwasher and Microwave Safe', data_format_2)

        """ 66 row """
        worksheet.merge_range('B66:H66', '4 Pc. Bowls', data_format_2)
        worksheet.merge_range('K66:X66', '6.25 in - (15.87 cm)', data_format_2)

        """ 67 row """
        worksheet.merge_range('B67:H67', '4 Pc. Mugs', data_format_2)
        worksheet.merge_range('K67:X67', '13 Oz - (384.4 ml) - 2-tone Reactive Glaze Mugs', data_format_2)

        """70 row table Info. To be used for Cost Calculation """
        worksheet.merge_range('O70:AZ70', 'Info. To be used for Cost Calculation', first_row_format)
        """71 row Header """
        worksheet.merge_range('O71:T71', 'Container Type', first_row_format_1)
        worksheet.merge_range('U71:AF71', 'Floor Load', first_row_format_1)
        worksheet.merge_range('AJ71:AZ71', 'Palletization for Storage', first_row_format_1)

        worksheet.merge_range('O72:T72', '40 FT.', data_format)
        worksheet.merge_range('U72:X72', 'Units', first_row_format_1)
        worksheet.merge_range('Y72:AB72', 'Cu Ft', first_row_format_1)
        worksheet.merge_range('AC72:AF72', 'Weight', first_row_format_1)
        worksheet.merge_range('AJ72:AM72', 'Units / Pallet', first_row_format_1)
        worksheet.merge_range('AN72:AR72', 'No. of Pallets', first_row_format_1)
        worksheet.merge_range('AS72:AV72', 'CuFt', first_row_format_1)
        worksheet.merge_range('AW72:AZ72', 'Weight', first_row_format_1)

        for rec in self:
            image_data = base64.b64decode(rec.image)
            image_data = BytesIO(image_data)
            company = self.env.user.company_id
            logo = base64.b64decode(company.logo)
            logo = BytesIO(logo)
            address = company.street if company.street else '' + company.street2 if company.street2 else '' \
                                                                                                         + company.city if company.city else '' + company.state_id.name if company.state_id.name else '' \
                                                                                                                                                                                                      + company.zip if company.zip else '' + company.country_id.name if company.country_id.name else ''
            worksheet.merge_range('H2:V2', rec.sudo().date and rec.sudo().date.strftime('%m/%d/%Y') or '', data_format)
            worksheet.merge_range('H3:V4', rec.sudo().prepared_by.name or '', data_format)
            # Set fix image size
            company_logo = Image.open(logo).resize((300, 100), Image.ANTIALIAS)
            company_logo.save('/tmp/company_logo.png')
            worksheet.insert_image('W2:AR4', '/tmp/company_logo.png')
            worksheet.merge_range('AS3:BM4', address, address_format)
            # Set fix image size
            img = Image.open(image_data).resize((250, 250), Image.ANTIALIAS)
            img.save('/tmp/new_image.png')
            worksheet.insert_image('B6:P13', '/tmp/new_image.png')
            # worksheet.insert_image('B6:P13', '', options={'x_offset': 0.0, 'y_offset': 50.99, 'image_data': img,
            #                                               'y_scale': 0.400, 'x_scale': 0.4500})
            worksheet.merge_range('W6:AX6', rec.sudo().upc, data_format)
            worksheet.merge_range('W7:AX7', rec.sudo().description, data_format)
            worksheet.merge_range('W8:AX8', rec.sudo().material, data_format)
            worksheet.merge_range('W9:AX9', rec.sudo().brand, data_format)
            worksheet.merge_range('W10:AX10', rec.sudo().made_by.name, data_format)
            worksheet.merge_range('W11:AX11', rec.sudo().made_in.name, data_format)
            worksheet.merge_range('W12:AX13', rec.sudo().comments, data_format)
            worksheet.merge_range('AY6:BM9', '$' + "{:.2f}".format(rec.sudo().retail_price), data_format)
            worksheet.merge_range('AY10:BM13', str(rec.sudo().pc) + " Pc", data_format)
            worksheet.merge_range('G33:J33', rec.sudo().packaging_qty, data_format)
            worksheet.merge_range('K33:N33', rec.sudo().packaging_width, data_format)
            worksheet.merge_range('O33:R33', rec.sudo().packaging_depth, data_format)
            worksheet.merge_range('S33:V33', rec.sudo().packaging_height, data_format)
            worksheet.merge_range('W33:Z33', rec.sudo().packaging_cuft, data_format)
            worksheet.merge_range('AA33:AD33', rec.sudo().packaging_weight, data_format)
            worksheet.merge_range('AK33:AN33', rec.sudo().pallet_exclude_qty, data_format)
            worksheet.merge_range('AO33:AR33', rec.sudo().pallet_exclude_width, data_format)
            worksheet.merge_range('AS33:AV33', rec.sudo().pallet_exclude_depth, data_format)
            worksheet.merge_range('AW33:AZ33', rec.sudo().pallet_exclude_height, data_format)
            worksheet.merge_range('BA33:BD33', rec.sudo().pallet_exclude_cuft, data_format)
            worksheet.merge_range('BE33:BH33', rec.sudo().pallet_exclude_weight, data_format)
            worksheet.merge_range('G37:J37', rec.sudo().remailer_qty, data_format)
            worksheet.merge_range('K37:N37', rec.sudo().remailer_w, data_format)
            worksheet.merge_range('O37:R37', rec.sudo().remailer_dimension, data_format)
            worksheet.merge_range('S37:V37', rec.sudo().remailer_height, data_format)
            worksheet.merge_range('W37:Z37', rec.sudo().remailer_cuft, data_format)
            worksheet.merge_range('AA37:AD37', rec.sudo().remailer_weight, data_format)
            worksheet.merge_range('AK37:AN37', rec.sudo().pallet_include_qty, data_format)
            worksheet.merge_range('AO37:AR37', rec.sudo().pallet_include_width, data_format)
            worksheet.merge_range('AS37:AV37', rec.sudo().pallet_include_depth, data_format)
            worksheet.merge_range('AW37:AZ37', rec.sudo().pallet_include_height, data_format)
            worksheet.merge_range('BA37:BD37', rec.sudo().pallet_include_cuft, data_format)
            worksheet.merge_range('BE37:BH37', rec.sudo().pallet_include_weight, data_format)
            worksheet.merge_range('G41:J41', rec.sudo().master_qty, data_format)
            worksheet.merge_range('K41:N41', rec.sudo().master_w, data_format)
            worksheet.merge_range('O41:R41', rec.sudo().master_dimension, data_format)
            worksheet.merge_range('S41:V41', rec.sudo().master_height, data_format)
            worksheet.merge_range('W41:Z41', rec.sudo().master_cuft, data_format)
            worksheet.merge_range('AA41:AD41', rec.sudo().master_weight, data_format)
            worksheet.merge_range('L46:O46', rec.sudo().cu_ft_20, data_format)
            worksheet.merge_range('P46:S46', rec.sudo().cu_ft_40, data_format)
            worksheet.merge_range('T46:W46', rec.sudo().cu_ft_40_hc, data_format)
            worksheet.merge_range('L47:O47', rec.sudo().pay_load_lbs_ft_20, data_format)
            worksheet.merge_range('P47:S47', rec.sudo().pay_load_lbs_ft_40, data_format)
            worksheet.merge_range('T47:W47', rec.sudo().pay_load_lbs_ft_40_hc, data_format)
            worksheet.merge_range('L48:O48', rec.sudo().cubic_ft_20, data_format)
            worksheet.merge_range('P48:S48', rec.sudo().cubic_ft_40, data_format)
            worksheet.merge_range('T48:W48', rec.sudo().cubic_ft_40_hc, data_format)
            worksheet.merge_range('L49:O49', rec.sudo().pay_load_kg_ft_20, data_format)
            worksheet.merge_range('P49:S49', rec.sudo().pay_load_kg_ft_40, data_format)
            worksheet.merge_range('T49:W49', rec.sudo().pay_load_kg_ft_40_hc, data_format)
            worksheet.merge_range('AH47:AM47', rec.sudo().floor_total_case_20, data_format)
            worksheet.merge_range('AN47:AQ47', rec.sudo().floor_cu_ft_20, data_format)
            worksheet.merge_range('AR47:AU47', rec.sudo().floor_weight_20, data_format)
            worksheet.merge_range('AV47:BA47', rec.sudo().pallet_total_20, data_format)
            worksheet.merge_range('BB47:BE47', rec.sudo().pallet_cu_ft_20, data_format)
            worksheet.merge_range('BF47:BI47', rec.sudo().pallet_weight_20, data_format)
            worksheet.merge_range('AH48:AM48', rec.sudo().floor_total_case_40, data_format)
            worksheet.merge_range('AN48:AQ48', rec.sudo().floor_cu_ft_40, data_format)
            worksheet.merge_range('AR48:AU48', rec.sudo().floor_weight_40, data_format)
            worksheet.merge_range('AV48:BA48', rec.sudo().pallet_total_40, data_format)
            worksheet.merge_range('BB48:BE48', rec.sudo().pallet_cu_ft_40, data_format)
            worksheet.merge_range('BF48:BI48', rec.sudo().pallet_weight_40, data_format)
            worksheet.merge_range('AH49:AM49', rec.sudo().floor_total_case_40_hc, data_format)
            worksheet.merge_range('AN49:AQ49', rec.sudo().floor_cu_ft_40_hc, data_format)
            worksheet.merge_range('AR49:AU49', rec.sudo().floor_weight_40_hc, data_format)
            worksheet.merge_range('AV49:BA49', rec.sudo().pallet_total_40_hc, data_format)
            worksheet.merge_range('BB49:BE49', rec.sudo().pallet_cu_ft_40_hc, data_format)
            worksheet.merge_range('BF49:BI49', rec.sudo().pallet_weight_40_hc, data_format)
            worksheet.merge_range('X55:AC55', '$' + "{:.2f}".format(rec.sudo().freight_rate_ft_20), data_format)
            worksheet.merge_range('AD55:AJ55', '$' + "{:.2f}".format(rec.sudo().freight_rate_ft_40), data_format)
            worksheet.merge_range('AK55:AQ55', '$' + "{:.2f}".format(rec.sudo().freight_rate_ft_40_hc), data_format)
            worksheet.merge_range('U60:X60', rec.sudo().floor_load_units, data_format)
            worksheet.merge_range('Y60:AB60', rec.sudo().floor_load_cuft, data_format)
            worksheet.merge_range('AC60:AF60', rec.sudo().floor_load_weight, data_format)
            worksheet.merge_range('AJ60:AM60', rec.sudo().storage_load_units, data_format)
            worksheet.merge_range('AN60:AR60', rec.sudo().storage_pallet_no, data_format)
            worksheet.merge_range('AS60:AV60', "{:.2f}".format(rec.sudo().storage_load_cuft), data_format)
            worksheet.merge_range('AW60:AZ60', rec.sudo().storage_load_weight, data_format)
            worksheet.merge_range('O73:T73', rec.sudo().pro_container_type, data_format)
            worksheet.merge_range('U73:X73', rec.sudo().pro_floor_load_units, data_format)
            worksheet.merge_range('Y73:AB73', rec.sudo().pro_floor_load_cuft, data_format)
            worksheet.merge_range('AC73:AF73', rec.sudo().pro_floor_load_weight, data_format)
            worksheet.merge_range('AJ73:AM73', rec.sudo().pro_storage_load_units, data_format)
            worksheet.merge_range('AN73:AR73', rec.sudo().pro_storage_pallet_no, data_format)
            worksheet.merge_range('AS73:AV73', "{:.2f}".format(rec.sudo().pro_storage_load_cuft), data_format)
            worksheet.merge_range('AW73:AZ73', rec.sudo().pro_storage_load_weight, data_format)

        """ Data Body """
        # worksheet.merge_range('O73:T73', '', first_row_format)
        # worksheet.merge_range('U73:X73', '', first_row_format)
        # worksheet.merge_range('Y73:AB73', '', first_row_format)
        # worksheet.merge_range('AC73:AF73', '', first_row_format)
        # worksheet.merge_range('AJ73:AM73', '', first_row_format)
        # worksheet.merge_range('AN73:AR73', '', first_row_format)
        # worksheet.merge_range('AS73:AV73', '', first_row_format)
        # worksheet.merge_range('AW73:AZ73', '', first_row_format)

        """ 75 row """
        worksheet.merge_range('C75:G75', "$" + str(self.export_mrf_price))
        worksheet.merge_range('L75:R75', 'Exporter/Mfr Price')
        worksheet.merge_range('V75:X75', 'Factor:', first_row_format)
        worksheet.merge_range('Y75:AA75', self.export_factor, first_row_format)

        """ 77 row """
        worksheet.merge_range('C77:G77', '$' + str(self.payment_terms_cost))
        worksheet.merge_range('H77:K77', str(self.payment_terms_per) + "%")
        worksheet.merge_range('L77:AA77', 'Payment terms to the exporter US Trading Company')
        worksheet.merge_range('AF77:AH77', self.payment_terms_days, first_row_format)
        worksheet.merge_range('AI77:AL77', 'Days at')
        worksheet.merge_range('AM77:AO77', str(self.payment_terms_per_year) + "%", first_row_format)
        worksheet.merge_range('AP77:AS77', 'Per year')

        """ 79 row """
        worksheet.merge_range('C79:G79', '$' + "{:.2f}".format(self.export_fob_price), first_row_format_1)
        worksheet.merge_range('H79:K79', '', first_row_format_1)
        worksheet.merge_range('L79:T79', 'EXPORT FOB PRICE', first_row_format_1)
        worksheet.merge_range('U79:BM79', '', first_row_format_1)

        """81 row """
        worksheet.merge_range('C81:G81', '$' + "{:.2f}".format(self.mark_up_cost))
        worksheet.merge_range('H81:K81', str(self.mark_up_per) + '%')
        worksheet.merge_range('L81:Z81', 'US Trading Company - Mark Up/Commission')
        worksheet.merge_range('AD81:AF81', str(self.mark_up_cost_per) + '%')
        worksheet.merge_range('AG81:AO81', 'Based on the FOB Price')

        row = 82
        column = 2

        for exp in self.export_price_ids:
            worksheet.write(row, column, '$' + "{:.2f}".format(exp.sudo().cost))
            worksheet.write(row, column + 5, "{:.2f}".format(exp.sudo().percentage) + '%')
            worksheet.write(row, column + 9, '$' + "{:.2f}".format(exp.sudo().fob_amount))
            worksheet.write(row, column + 16, exp.sudo().commission)
            row += 1
        row_1 = row + 2
        """ 97 row """
        for rec in self:
            worksheet.write(row_1, column, '$' + "{:.2f}".format(rec.sudo().importation_cost), costs_extra_format)
            worksheet.write(row_1, column + 5, "{:.2f}".format(rec.sudo().importation_percentage) + '%',
                            costs_extra_format)
            worksheet.write(row_1, column + 12, 'Importation Cost:', costs_extra_format)
            row_1 = row_1 + 2
            """ 99 row """
            worksheet.write(row_1, column, '$' + "{:.2f}".format(rec.sudo().processing_cost), costs_extra_format)
            worksheet.write(row_1, column + 5, "{:.2f}".format(rec.sudo().processing_percentage) + '%',
                            costs_extra_format)
            worksheet.write(row_1, column + 12, 'Warefor Logistics Processing Fees @', costs_extra_format)
            row_2 = row_1 + 2
            """ 101 row """
            worksheet.merge_range(row_2, column, row_2, column + 4,
                                  '$' + "{:.2f}".format(rec.sudo().total_importation_cost), first_row_format_1)
            worksheet.merge_range(row_2, column + 5, row_2, column + 8,
                                  str(rec.sudo().total_importation_percentage) + '%', first_row_format_1)
            worksheet.merge_range(row_2, column + 9, row_2, column + 20, 'TOTAL IMPORTATION COST', first_row_format_1)
            worksheet.merge_range(row_2, column + 21, row_2, column + 60, '', first_row_format_1)
        row_3 = row_2 + 2
        for importation in self.storage_cost_ids:
            worksheet.write(row_3, column, '$' + "{:.2f}".format(importation.sudo().cost))
            worksheet.write(row_3, column + 5, "{:.2f}".format(importation.sudo().percentage) + '%')
            worksheet.write(row_3, column + 9, '$' + "{:.2f}".format(importation.sudo().amount))
            worksheet.write(row_3, column + 12,
                            dict(importation._fields['price_per_1'].selection).get(importation.price_per_1))
            worksheet.write(row_3, column + 17, importation.sudo().commission)
            row_3 += 1
        row_4 = row_3 + 1
        """ 109 row """
        for rec in self:
            worksheet.merge_range(row_4, column, row_4, column + 4, '$' + "{:.2f}".format(rec.sudo().storage_cost),
                                  first_row_format_1)
            worksheet.merge_range(row_4, column + 5, row_4, column + 8,
                                  "{:.2f}".format(rec.sudo().storage_percentage) + '%', first_row_format_1)
            worksheet.merge_range(row_4, column + 9, row_4, column + 20, 'TOTAL STORAGE COST', first_row_format_1)
            worksheet.merge_range(row_4, column + 21, row_4, column + 60, '', first_row_format_1)
            row_4 = row_4 + 2
        row_5 = 0
        for storage in self.material_cost_ids:
            worksheet.write(row_4, column, '$' + "{:.2f}".format(storage.sudo().cost))
            worksheet.write(row_4, column + 5, "{:.2f}".format(storage.sudo().percentage) + '%')
            worksheet.write(row_4, column + 9, '$' + "{:.2f}".format(storage.sudo().material_amount))
            worksheet.write(row_4, column + 12, dict(storage._fields['price_per'].selection).get(storage.price_per))
            worksheet.write(row_4, column + 17, storage.sudo().commission)
            row_4 += 1
            row_5 = row_4 + 1
        # """ 111 row """
        # worksheet.merge_range('C111:G111', '$0.25')
        # worksheet.merge_range('H111:K111', '1.37%')
        # worksheet.merge_range('L111:O111', '$6.75', first_row_format)
        # worksheet.merge_range('Q111:S111', 'Per Pallet')
        # """ Table  Header"""
        # worksheet.merge_range('U111:Y111', 'Pallet Type', first_row_format)
        # worksheet.merge_range('Z111:AC111', 'Grade A', first_row_format)
        # worksheet.merge_range('AD111:AG111', 'Grade B', first_row_format)
        # worksheet.merge_range('AH111:AK111', 'Heat Treat', first_row_format)
        # """ 112 row """
        # """ Data body """
        # worksheet.merge_range('U112:Y112', 'Cost / Pallet', first_row_format)
        # worksheet.merge_range('Z112:AC112', '$6.75', first_row_format)
        # worksheet.merge_range('AD112:AG112', '$6.00', first_row_format)
        # worksheet.merge_range('AH112:AK112', '$21.75', first_row_format)
        # """ 114 row """
        # worksheet.merge_range('C114:G114', '$0.11')
        # worksheet.merge_range('H114:K114', '0.61%')
        # worksheet.merge_range('L114:O114', '$0.75')
        # worksheet.merge_range('Q114:S114', 'Per Each')
        # worksheet.merge_range('U114:X114', 'Corner Board')
        # worksheet.merge_range('Z114:AA114', '4', first_row_format)
        # worksheet.merge_range('AC114:AL114', '  Units Each when Applicable')
        # """ 116 row """
        # worksheet.merge_range('C116:G116', '$0.10')
        # worksheet.merge_range('H116:K116', '0.57%')
        # worksheet.merge_range('L116:O116', '$0.70')
        # worksheet.merge_range('Q116:S116', 'Slip Sheet')
        # worksheet.merge_range('U116:X116', 'Corner Board')
        # worksheet.merge_range('Z116:AA116', '4', first_row_format)
        # worksheet.merge_range('AC116:AL116', '  Units Each when Applicable')
        # """ 118 row """
        # worksheet.merge_range('C118:G118', '$0.04')
        # worksheet.merge_range('H118:K118', '0.24%')
        # worksheet.merge_range('L118:O118', '$1.20')
        # worksheet.merge_range('Q118:S118', 'Per Pallet')
        # worksheet.merge_range('U118:X118', 'Stretch Wrap')
        for rec in self:
            """ 120 row """
            worksheet.merge_range(row_5, column, row_5, column + 4, '$' + "{:.2f}".format(rec.sudo().material_cost),
                                  first_row_format_1)
            worksheet.merge_range(row_5, column + 5, row_5, column + 8,
                                  "{:.2f}".format(rec.sudo().material_percentage) + '%', first_row_format_1)
            worksheet.merge_range(row_5, column + 9, row_5, column + 20, 'TOTAL MATERIALS COST', first_row_format_1)
            worksheet.merge_range(row_5, column + 21, row_5, column + 60, '', first_row_format_1)
            row_5 = row_5 + 2
            """ 122 row """
            worksheet.merge_range(row_5, column, row_5, column + 4, '$' + "{:.2f}".format(rec.sudo().total_cost),
                                  first_row_format_1)
            worksheet.merge_range(row_5, column + 5, row_5, column + 8, '', first_row_format_1)
            worksheet.merge_range(row_5, column + 9, row_5, column + 20, 'TOTAL COST', first_row_format_1)
            worksheet.merge_range(row_5, column + 21, row_5, column + 60, '', first_row_format_1)
            row_5 = row_5 + 2
            """ 124 row """
            worksheet.merge_range(row_5, column, row_5, column + 4, '$' + "{:.2f}".format(rec.sudo().warefor_cost),
                                  first_row_format_1)
            worksheet.merge_range(row_5, column + 5, row_5, column + 8, '', first_row_format_1)
            worksheet.merge_range(row_5, column + 9, row_5, column + 20, 'WAREFOR SOLUTIONS COST', first_row_format_1)
            worksheet.merge_range(row_5, column + 21, row_5, column + 60, '', first_row_format_1)
            row_5 = row_5 + 2
            """ 126 row """
            worksheet.merge_range(row_5, column, row_5, column + 4,
                                  '$' + "{:.2f}".format(rec.sudo().warefor_margin_cost), data_format_1)
            worksheet.merge_range(row_5, column + 5, row_5, column + 8,
                                  "{:.2f}".format(rec.sudo().warefor_margin_per) + "%", data_format_1)
            worksheet.merge_range(row_5, column + 9, row_5, column + 14, "Margin", data_format_1)
            worksheet.merge_range(row_5, column + 15, row_5, column + 20,
                                  "{:.2f}".format(rec.sudo().warefor_mark_up) + '%', data_format_1)
            worksheet.merge_range(row_5, column + 21, row_5, column + 30, "Mark Up", data_format_1)
            worksheet.merge_range(row_5, column + 31, row_5, column + 60, "", data_format_1)
            row_6 = row_5 + 2
            # """ 128 row """
            # worksheet.write(row_5, column, 'Included')
            # worksheet.write(row_5, column + 10, 'Administration')
            # """ 129 row """
            # worksheet.write(row_5 + 1, column, 'Included')
            # worksheet.write(row_5 + 1, column + 10, 'Product Development')
            # """ 130 row """
            # worksheet.write(row_5 + 2, column, 'Included')
            # worksheet.write(row_5 + 2, column + 10, 'Sales & Marketing')
            # """ 131 row """
            # worksheet.write(row_5 + 3, column, 'Included')
            # worksheet.write(row_5 + 3, column + 10, 'Distribution')
            # """ 132 row """
            # worksheet.write(row_5 + 4, column, 'Included')
            # worksheet.write(row_5 + 4, column + 10, 'Online Sales & Fulfillment')
            # """ 133 row """
            # worksheet.write(row_5 + 5, column, 'Included')
            # worksheet.write(row_5 + 5, column + 10, 'Product Liability Insurance')
            # """ 134 row """
            # worksheet.write(row_5 + 6, column, 'Included')
            # worksheet.write(row_5 + 6, column + 10, 'Product Warranty')
            # """ 135 row """
            # worksheet.write(row_5 + 7, column, 'Included')
            # worksheet.write(row_5 + 7, column + 10, 'Customer Service')
            # row_6 = row_5 + 9
            """ 137 row """
            worksheet.merge_range(row_6, column, row_6, column + 4, '$' + "{:.2f}".format(rec.sudo().wholesale_price),
                                  first_row_format_1)
            worksheet.merge_range(row_6, column + 5, row_6, column + 8, '', first_row_format_1)
            worksheet.merge_range(row_6, column + 9, row_6, column + 20, 'WHOLESALE PRICE', first_row_format_1)
            worksheet.merge_range(row_6, column + 21, row_6, column + 60, '', first_row_format_1)
            row_6 = row_6 + 2
            """ 125 row """
            worksheet.merge_range(row_6, column, row_6, column + 4,
                                  '$' + "{:.2f}".format(rec.sudo().wholesale_margin_cost), data_format_1)
            worksheet.merge_range(row_6, column + 5, row_6, column + 8,
                                  "{:.2f}".format(rec.sudo().wholesale_margin_per) + '%', data_format_1)
            worksheet.merge_range(row_6, column + 9, row_6, column + 14, "Margin", data_format_1)
            worksheet.merge_range(row_6, column + 15, row_6, column + 20,
                                  "{:.2f}".format(rec.sudo().wholesale_mark_up) + '%', data_format_1)
            worksheet.merge_range(row_6, column + 21, row_6, column + 30, 'Mark Up', data_format_1)
            worksheet.merge_range(row_6, column + 31, row_6, column + 60, '', data_format_1)
            row_6 = row_6 + 2
            """ 143 row """
            # worksheet.merge_range(row_6, column, row_6, column + 7, rec.sudo().retail_price, first_row_format_1)
            worksheet.merge_range(row_6, column, row_6, column + 4, '$' + "{:.2f}".format(rec.sudo().retail_price),
                                  first_row_format_1)
            worksheet.merge_range(row_6, column + 5, row_6, column + 8, '', first_row_format_1)
            worksheet.merge_range(row_6, column + 9, row_6, column + 20, 'RETAIL PRICE', first_row_format_1)
            worksheet.merge_range(row_6, column + 21, row_6, column + 60, '', first_row_format_1)

        #         row = 4
        #         column = 0
        #         worksheet.write(1, column, 'ASSETS', column_titles)
        #         """ Current Assets """
        #         worksheet.write(3, column, 'Current Assets', column_1)
        #         balance = 0.00
        #         total_assets = 0.00
        #         for rec in report_data[0]:
        #             if rec.get('account_type') == 'current_assets':
        #                 worksheet.write(row, column, rec.get('name'), data_format)
        #                 worksheet.write(row, column + 1, rec.get('balance'), float_format)
        #                 row += 1
        #                 balance += rec.get('balance')
        #
        #         worksheet.write(row + 1, column, 'Total Current Assets', column_1)
        #         worksheet.write(row + 1, column + 2, balance, data_format)
        #         total_assets += balance
        #
        #         """ Property and Equipment """
        #         row += 3
        #         balance_one = 0.00
        #         worksheet.write(row, column, 'Property and Equipment', column_1)
        #         for rec in report_data[0]:
        #             if rec.get('account_type') == 'property_equipment':
        #                 worksheet.write(row + 1, column, rec.get('name'), data_format)
        #                 worksheet.write(row + 1, column + 1, rec.get('balance'), float_format)
        #                 row += 1
        #                 balance_one += rec.get('balance')
        #
        #         worksheet.write(row + 2, column, 'Total Property and Equipment', column_1)
        #         worksheet.write(row + 2, column + 2, balance_one, data_format)
        #         total_assets += balance_one
        #
        #         """ Other Assets """
        #         row += 4
        #         balance_two = 0.00
        #         worksheet.write(row, column, 'Other Assets', column_1)
        #         for rec in report_data[0]:
        #             if rec.get('account_type') == 'other_assets':
        #                 worksheet.write(row + 1, column, rec.get('name'), data_format)
        #                 worksheet.write(row + 1, column + 1, rec.get('balance'), float_format)
        #                 row += 1
        #                 balance_two += rec.get('balance')
        #
        #         worksheet.write(row + 2, column, 'Total Other Assets', column_1)
        #         worksheet.write(row + 2, column + 2, balance_two, data_format)
        #         total_assets += balance_two
        #
        #         """ Total Assets """
        #         row += 2
        #         worksheet.write(row + 2, column, 'Total Assets', column_1)
        #         worksheet.write(row + 2, column + 2, total_assets, data_format)
        #
        #         """ LIABILITIES AND CAPITAL """
        #         total_liabilities = 0.00
        #         row += 3
        #         worksheet.write(row + 2, column, 'LIABILITIES AND CAPITAL', column_titles)
        #
        #         """ Current Liabilities """
        #         row += 4
        #         balance_three = 0.00
        #         worksheet.write(row, column, 'Current Liabilities', column_1)
        #         for rec in report_data[0]:
        #             if rec.get('account_type') == 'current_liabilities':
        #                 worksheet.write(row + 1, column, rec.get('name'), data_format)
        #                 worksheet.write(row + 1, column + 1, rec.get('balance'), float_format)
        #                 row += 1
        #                 balance_three += rec.get('balance')
        #
        #         worksheet.write(row + 2, column, 'Total Current Liabilities', column_1)
        #         worksheet.write(row + 2, column + 2, balance_three, data_format)
        #         total_liabilities += balance_three
        #
        #         """ Long-Term Liabilities """
        #         row += 4
        #         balance_four = 0.00
        #         worksheet.write(row, column, 'Long - Term Liabilities', column_1)
        #         for rec in report_data[0]:
        #             if rec.get('account_type') == 'long_term_liabilities':
        #                 worksheet.write(row + 1, column, rec.get('name'), data_format)
        #                 worksheet.write(row + 1, column + 1, rec.get('balance'), float_format)
        #                 row += 1
        #                 balance_four += rec.get('balance')
        #
        #         worksheet.write(row + 2, column, 'Total Long - Term Liabilities', column_1)
        #         worksheet.write(row + 2, column + 2, balance_four, data_format)
        #         total_liabilities += balance_four
        #
        #         """ Total Liabilities """
        #         total_liabilities_and_capital = 0.00
        #         row += 3
        #         worksheet.write(row + 2, column, 'Total Liabilities', column_1)
        #         worksheet.write(row + 2, column + 2, total_liabilities, data_format)
        #         total_liabilities_and_capital += total_liabilities
        #
        #         """ Capital """
        #         row += 4
        #         balance_five = 0.00
        #         worksheet.write(row, column, 'Capital', column_1)
        #         for rec in report_data[0]:
        #             if rec.get('account_type') == 'capital':
        #                 worksheet.write(row + 1, column, rec.get('name'), data_format)
        #                 worksheet.write(row + 1, column + 1, rec.get('balance'), float_format)
        #                 row += 1
        #                 balance_five += rec.get('balance')
        #
        #         worksheet.write(row + 2, column, 'Total Capital', column_1)
        #         worksheet.write(row + 2, column + 2, balance_five, data_format)
        #         total_liabilities_and_capital += balance_five
        #
        #         """ Total Liabilities & Capital """
        #         row += 3
        #         worksheet.write(row + 2, column, 'Total Liabilities & Capital', column_1)
        #         worksheet.write(row + 2, column + 2, total_liabilities_and_capital, data_format)
        # #         worksheet.set_column('A:B', 12)
        # #
        # #         merge_format = workbook.add_format({
        # #             'bold': 1,
        # #             'border': 1,
        # #             'align': 'center',
        # #             'valign': 'vcenter',
        # #             'fg_color': 'yellow'})
        # #
        # #         worksheet.merge_range('A51:B53', 'Merged Range', merge_format)
        # #         worksheet.write(50, 2,'Merged Range', merge_format)
        # #         worksheet.write(51, 2,'Merged Range', merge_format)
        # #         worksheet.write(52, 2,'Merged Range', merge_format)
        # # #         report_date = datetime.datetime.now().strftime("%m/%d/%Y")
        # # #         worksheet.merge_range('K1:L1', "sssssssssssss", data_format)

        workbook.close()
        return file_name

    def create_attachment(self, file_name):
        """
        Delete file created in tmp dir, Delete old attachment and create attachment for download report
        :param file_name: file name string
        :return: attachment ir.attachment object
        """
        ir_attachment_obj = self.env['ir.attachment']

        # Read File data
        with open(file_name, "rb+") as file:
            file_data = base64.encodebytes(file.read())
            file.close()

        # Remove tmp file
        os.remove(file_name)

        # Delete Old Attachment
        attachments = ir_attachment_obj.search([('name', '=ilike', 'Product Development Report.xlsx'),
                                                ('res_model', '=', 'walmart.report')])
        attachments and attachments.unlink()

        return ir_attachment_obj.create({
            'name': 'Product Development Report.xlsx',
            'datas': file_data,
            'res_model': 'walmart.report',
            'type': 'binary'
        })


class ContainerLoadCalculation(models.Model):
    _name = 'container.load.calculation'
    _description = 'Container Load Calculation'

    product_development_id = fields.Many2one('product.development', string="Product Development")
    container_size_id = fields.Many2one('container.size', string="Container Size")
    ft_20 = fields.Char(string='20 Ft.')
    ft_40 = fields.Char(string='40 Ft.')
    ft_40_hc = fields.Char(string='40 Ft. HC')


class ContainerSize(models.Model):
    _name = 'container.size'
    _description = 'Container Size'

    name = fields.Char(string='Name')


class ContainerFloorPallet(models.Model):
    _name = 'container.floor.pallet'
    _description = 'Container Floor Pallet'

    product_development_id = fields.Many2one('product.development', string="Product Development")
    container_size_id = fields.Many2one('container.size', string="Container Size")
    floor_total_case = fields.Char(string="Total Cases")
    floor_cu_ft = fields.Char(string="Cu Ft")
    floor_weight = fields.Char(string="Weight")
    pallet_total = fields.Char(string="Total Pallet")
    pallet_cu_ft = fields.Char(string="Cu Ft")
    pallet_weight = fields.Char(string="Weight")


class ProductDevelopmentState(models.Model):
    _name = 'product.development.state'
    _description = 'Product Development State'

    name = fields.Char(string='name')
    sequence = fields.Integer(string='Sequence')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    type = fields.Selection([
        ('consu', 'Consumable'),
        ('service', 'Service'),
        ('product', 'Storable Product')], string='Product Type', default='product', required=True,
        help='A storable product is a product for which you manage stock. The Inventory app has to be installed.\n'
             'A consumable product is a product for which stock is not managed.\n'
             'A service is a non-material product you provide.')
