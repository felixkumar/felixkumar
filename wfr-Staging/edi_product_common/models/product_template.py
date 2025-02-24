from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    edi_buyer_part_number = fields.Char('Edi Buyer Part Number',
                                        help='Buyer\'s primary product identifier',
                                        compute='_compute_part_number', store=True)
    edi_vendor_part_number = fields.Char('EDI Vendor Part Number',
                                         help='Vendor\'s primary product identifier',
                                         compute='_compute_part_number', store=True)
    edi_consumer_package_code = fields.Char('EDI Consumer Package Code',
                                            help='Consumer level or customer unit product identification number')
    edi_product_characteristic_code = fields.Char('EDI Product Characteristic Code',
                                                  help='Code defining/classifying the type of description being sent')

    def _compute_part_number(self):
        for product in self:
            product.edi_buyer_part_number = product.barcode or ''
            product.edi_vendor_part_number = product.barcode or ''
