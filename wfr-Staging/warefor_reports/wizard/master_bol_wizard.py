# -*- coding: utf-8 -*-
from odoo import fields, models, api

class MasterBillOfLadingWizard(models.TransientModel):
    _name = 'master.bol.wizard'
    _description = 'Master Bill Of Lading Wizard'

    freight_record = fields.Many2one('freight.freight' ,'Freight ID')
    is_master_fr_prepaid = fields.Boolean('Is Freight Prepaid')
    is_master_fr_collect = fields.Boolean('Is Freight Collect')
    is_master_fr_3rd_party = fields.Boolean('Is Freight 3rd Party')
    master_cod_amount = fields.Char('COD Amount')
    is_master_fee_prepaid = fields.Boolean('Is Fee Prepaid')
    is_master_fee_collect = fields.Boolean('Is Fee Collect')
    is_customer_check = fields.Boolean('Is Customer Check Acceptable')
    master_date = fields.Date('Date')
    master_pickup_date = fields.Date('Pickup Date')
    is_master_by_shipper_trai = fields.Boolean('Is By Shipper')
    is_master_by_driver_trai = fields.Boolean('Is By Driver')
    is_master_by_shipper_freight = fields.Boolean('Is By Shipper')
    is_master_by_driver_freight = fields.Boolean('Is By Driver/ Pallets Said to Contain')
    is_master_by_pieces = fields.Boolean('Is By Driver/ Pieces')
    master_shipper_sign = fields.Binary('Signature of Shipper')
    master_carrier_sign = fields.Binary('Signature of Carrier')
    skip_signature = fields.Boolean('Skip Signature', default=True)
    # @api.depends('freight_record')
    # def _compute_freight_id(self):
    #     for rec in self:
    #         freight_id = self.env.context.get('default_freight_record')
    #         if freight_id:
    #             rec.freight_record = self.env['freight.freight'].browse(freight_id)
    #         else:
    #             rec.freight_record = False

    def print_report_master_bol(self):
        freight_id = self.freight_record
        if self.skip_signature:
            if freight_id.shipper_sign:
                freight_id.shipper_sign = False
            if freight_id.carrier_sign:
                freight_id.carrier_sign = False
                freight_id.date = False
            if freight_id.shipper_sign_h:
                freight_id.shipper_sign_h = False
                freight_id.date_h = False
            if freight_id.carrier_sign_h:
                freight_id.carrier_sign_h = False

        if not self.skip_signature:
            freight_id.sudo().write({
                'is_fr_prepaid': self.is_master_fr_prepaid,
                'is_fr_collect' : self.is_master_fr_collect,
                'is_fr_3rd_party' : self.is_master_fr_3rd_party,
                'cod_amount' : self.master_cod_amount,
                'is_fee_prepaid' : self.is_master_fee_prepaid,
                'is_fee_collect': self.is_master_fee_collect,
                'is_customer_check' : self.is_customer_check,
                'date' : self.master_date,
                'pickup_date' : self.master_pickup_date,
                'is_by_shipper_trai' : self.is_master_by_shipper_trai,
                'is_by_driver_trai' : self.is_master_by_driver_trai,
                'is_by_shipper_freight' : self.is_master_by_shipper_freight,
                'is_by_driver_freight' : self.is_master_by_driver_freight,
                'is_by_pieces' : self.is_master_by_pieces,
                'shipper_sign' : self.master_shipper_sign,
                'carrier_sign' : self.master_carrier_sign,

                'is_fr_prepaid_h': self.is_master_fr_prepaid,
                'is_fr_collect_h': self.is_master_fr_collect,
                'is_fr_3rd_party_h': self.is_master_fr_3rd_party,
                'cod_amount_h': self.master_cod_amount,
                'is_fee_prepaid_h': self.is_master_fee_prepaid,
                'is_fee_collect_h': self.is_master_fee_collect,
                'is_customer_check_h': self.is_customer_check,
                'date_h': self.master_date,
                'pickup_date_h': self.master_pickup_date,
                'is_by_shipper_trai_h': self.is_master_by_shipper_trai,
                'is_by_driver_trai_h': self.is_master_by_driver_trai,
                'is_by_shipper_freight_h': self.is_master_by_shipper_freight,
                'is_by_driver_freight_h': self.is_master_by_driver_freight,
                'is_by_pieces_h': self.is_master_by_pieces,
                'shipper_sign_h': self.master_shipper_sign,
                'carrier_sign_h': self.master_carrier_sign,
            })
        report =  freight_id.combine_bill_of_lading()
        return report
