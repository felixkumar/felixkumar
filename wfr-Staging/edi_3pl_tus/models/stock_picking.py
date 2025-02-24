import random

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    edi_store_id = fields.Many2one("edi.customer.store", string="EDI Store ID")
    shipping_serial_id = fields.Char("ShippingSerialID")
    carrier_package_id = fields.Char("CarrierPackageID")
    edi_obl_weight = fields.Float("EDI OBL Weight")
    edi_obl_uom = fields.Char("EDI OBL UOM")
    edi_weight_qualifier = fields.Selection(selection=[('G', 'Gross Weight'), ('N', 'Net Weight')],
                                            string='EDI Weight Qualifier', default='N')
    sscc_18_barcode_char = fields.Char(string="SSCC-18 Barcode Number")

    def _compute_sscc_18_barcode_char(self):
        """
        Generate SSCC barcode from company data
        """
        for rec in self:
            company_id = rec.company_id
            barcode = ""
            if company_id.gs1_prefix and company_id.gs1_company_prefix:
                company_id.gs1_prefix = int(company_id.gs1_prefix or 1) + 1
                serial = "000000000" + str(company_id.gs1_prefix)
                serial_len = 16 - len(company_id.gs1_company_prefix)
                data = "{}{}{}".format(company_id.extension_digit, company_id.gs1_company_prefix,
                                       serial[-serial_len:])
                check_digit = self.calculate_sscc18_check_digit(data)
                barcode = "{}{}{}".format(company_id.application_identification, data, check_digit)
            rec.sscc_18_barcode_char = barcode

    def calculate_sscc18_check_digit(self, sscc_17=None):
        """
        Calculate the check digit for an SSCC-18 barcode from the first 17 digits.

        Args:
        sscc_17 (str): The first 17 digits of the SSCC-18 code as a string.

        Returns:
        str: The check digit as a string.
        """
        if len(sscc_17) != 17 or not sscc_17.isdigit():
            raise ValueError("SSCC-17 must be a string of 17 digits")

        # Convert the 17 digits into a list of integers
        digits = [int(d) for d in sscc_17]

        # Calculate the sum of the digits, with every second digit (from the right) multiplied by 3
        total_sum = 0
        for i in range(len(digits)):
            if (i + 1) % 2 == 0:  # Even position (1-based index)
                total_sum += digits[-(i + 1)]
            else:  # Odd position (1-based index)
                total_sum += digits[-(i + 1)] * 3

        # Calculate the check digit
        check_digit = (10 - (total_sum % 10)) % 10

        return str(check_digit)

    def button_validate(self):
        """
            Generating SSCC-18 barcode for EDI Shipment
        """
        for rec in self:
            if rec.edi_shipment_identifier:
                rec._compute_sscc_18_barcode_char()
        res = super(StockPicking, self).button_validate()
        return res
