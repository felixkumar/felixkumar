# -*- coding: utf-8 -*-

from odoo import models,fields,api
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError


class SSCC18BarcodeCompany(models.Model):
    _name = 'sscc18.barcode'
    _description = 'store created sscc18 barcode based on company'
    _rec_name = "sscc18_barcode"

    sscc18_barcode = fields.Char('sscc18 Barcode')
    company_id = fields.Many2one('res.company', 'Company')
    gs1_code = fields.Char('GS1 Code')
    serial_no = fields.Char('Serial Number')
    expiry_date = fields.Date('Expiry Date')
    osd_freight_transfer_ids = fields.One2many('osd.freight.transfer.line','sscc_barcode_id',string="Items")

    @api.model
    def create(self, vals):
        vals['expiry_date'] = date.today() + relativedelta(years=1)
        return super(SSCC18BarcodeCompany, self).create(vals)



class PalletBatchTusInherit(models.Model):
    _inherit = 'pallet.batch.tus'


    def generate_sscc_code(self):
        """
        Generate Pallet SSCC barcode
        :return:
        """
        for rec in self:
            """
            Document Reference: for generating pallet SSCC barcodes
            https://www.gs1us.org/DesktopModules/Bring2mind/DMX/Download.aspx?Command=Core_Download&EntryId=177&language=en-US&PortalId=0&TabId=134  
            """
            app_identifier = "(00)"
            extension_digit = '0'
            def calculate_check_digit(number):
                total = sum(int(d) * (3 if (i % 2 == 0) else 1) for i, d in enumerate(reversed(number)))
                return (10 - (total % 10)) % 10
            def extract_serial_no(barcodes,gs1code):
                gs1_length = len(gs1code) + 5
                # start = len(barcodes) - gs1_length
                serial_end = 21
                str_serial_no = str(barcodes[gs1_length:serial_end])
                return str_serial_no
            def generate_new_barcode(barcodes, gs1):
                str_serial_number = extract_serial_no(barcodes,gs1)
                last_serial_number = int(str_serial_number)
                width = 16 - len(gs1)
                new_serial_number = "{:0{width}d}".format(last_serial_number + 1, width=width)
                sscc_not_check_digit = f"{extension_digit}{gs1_code}{new_serial_number}"
                check_digits = calculate_check_digit(sscc_not_check_digit)
                generate_sscc_code = "{app_identifier}{extension_digit}{gs1_code}{serial_number}{check_digit}".format(
                    app_identifier=app_identifier,
                    extension_digit=extension_digit,
                    gs1_code=gs1_code,
                    serial_number=new_serial_number,
                    check_digit=check_digits
                )
                return generate_sscc_code
            gs1_code = rec.picking_id.company_id.gs1_company_prefix or rec.company_id.gs1_company_prefix or "0000000"
            required_serial_length = 16 - len(gs1_code)
            if not (7 <= len(gs1_code) <= 10):
                raise ValidationError("GS1 Company Prefix must be between 7 and 10 digits")
            last_record = rec.env['sscc18.barcode'].search(
                [('company_id', '=', rec.picking_id.company_id.id or rec.company_id.id),
                 ('gs1_code', '=', gs1_code)], order="create_date desc", limit=1)
            if not last_record:
                serial_number = "0" * required_serial_length
                serial_number = serial_number[:-1] + "1"
                sscc_without_check_digit = f"{extension_digit}{gs1_code}{serial_number}"
                check_digit = calculate_check_digit(sscc_without_check_digit)
                generated_sscc_code = "{app_identifier}{extension_digit}{gs1_code}{serial_number}{check_digit}".format(
                    app_identifier=app_identifier,
                    extension_digit=extension_digit,
                    gs1_code = gs1_code,
                    serial_number=serial_number,
                    check_digit=check_digit
                )
                rec.env['sscc18.barcode'].sudo().create({
                    'sscc18_barcode': generated_sscc_code,
                    'company_id': rec.picking_id.company_id.id or rec.company_id.id,
                    'gs1_code': gs1_code,
                    'serial_no': serial_number
                })
                rec.sscc_18_barcode_char = generated_sscc_code
            else:
                rec_serial = last_record.serial_no
                len_rec = len(rec_serial)
                expected_serial_no = '9' * len_rec
                if rec_serial == expected_serial_no:
                    expired_record = rec.env['sscc18.barcode'].search([('expiry_date', '<', date.today()),
                                                                       ('company_id', '=',
                                                                        rec.picking_id.company_id.id or rec.company_id.id),
                                                                       ('gs1_code', '=', gs1_code)]
                                                                      , limit=1)
                    if expired_record:
                        expired_barcode = expired_record.sscc18_barcode
                        rec.env['sscc18.barcode'].sudo().create({
                            'sscc18_barcode': expired_barcode,
                            'company_id': rec.picking_id.company_id.id or rec.company_id.id,
                            'gs1_code': gs1_code,
                            'serial_no': expired_record.serial_no
                        })
                        rec.sscc_18_barcode_char = expired_barcode
                        expired_record.unlink()
                else:
                    last_barcode = last_record.sscc18_barcode
                    if last_record and last_barcode:
                        generated_sscc_code = generate_new_barcode(last_barcode, gs1_code)
                        already_exist = rec.env['sscc18.barcode'].sudo().search([('sscc18_barcode', '=', generated_sscc_code),('company_id', '=', rec.picking_id.company_id.id or rec.company_id.id)])
                        if already_exist:
                            highest_rec = rec.env['sscc18.barcode'].sudo().search([
                                ('company_id', '=', rec.picking_id.company_id.id or rec.company_id.id)
                            ], order="sscc18_barcode desc", limit=1)
                            barcode = highest_rec.sscc18_barcode
                            generated_sscc_code = generate_new_barcode(barcode, gs1_code)
                            str_serial_number = extract_serial_no(generated_sscc_code,gs1_code)
                            rec.env['sscc18.barcode'].sudo().create({
                                    'sscc18_barcode': generated_sscc_code,
                                    'company_id': rec.picking_id.company_id.id or rec.company_id.id,
                                    'gs1_code': gs1_code,
                                    'serial_no': str_serial_number
                            })
                            rec.sscc_18_barcode_char = generated_sscc_code
                        else:
                            last_serial_number = extract_serial_no(generated_sscc_code,gs1_code)
                            rec.env['sscc18.barcode'].sudo().create({
                                    'sscc18_barcode': generated_sscc_code,
                                    'company_id': rec.picking_id.company_id.id or rec.company_id.id,
                                    'gs1_code': gs1_code,
                                    'serial_no': last_serial_number
                            })
                            rec.sscc_18_barcode_char = generated_sscc_code

