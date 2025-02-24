# -*- coding: utf-8 -*-
from odoo import fields, models, api

class HouseBillOfLadingWizard(models.TransientModel):
    _name = 'house.bol.wizard'
    _description = 'House Bill Of Lading Wizard'

    freight_record = fields.Many2one('freight.freight' ,'Freight ID')
    is_house_fr_prepaid = fields.Boolean('Is Freight Prepaid')
    is_house_fr_collect = fields.Boolean('Is Freight Collect')
    is_house_fr_3rd_party = fields.Boolean('Is Freight 3rd Party')
    house_cod_amount = fields.Char('COD Amount')
    is_house_fee_prepaid = fields.Boolean('Is Fee Prepaid')
    is_house_fee_collect = fields.Boolean('Is Fee Collect')
    is_house_check = fields.Boolean('Is Customer Check Acceptable')
    house_date = fields.Date('Date')
    house_pickup_date = fields.Date('Pickup Date')
    is_house_by_shipper_trai = fields.Boolean('Is By Shipper')
    is_house_by_driver_trai = fields.Boolean('Is By Driver')
    is_house_by_shipper_freight = fields.Boolean('Is By Shipper')
    is_house_by_driver_freight = fields.Boolean('Is By Driver/ Pallets Said to Contain')
    is_house_by_pieces = fields.Boolean('Is By Driver/ Pieces')
    house_shipper_sign = fields.Binary('Signature of Shipper')
    house_carrier_sign = fields.Binary('Signature of Carrier')
    # @api.depends('freight_record')
    # def _compute_freight_id(self):
    #     for rec in self:
    #         freight_id = self.env.context.get('default_freight_record')
    #         if freight_id:
    #             rec.freight_record = self.env['freight.freight'].browse(freight_id)
    #         else:
    #             rec.freight_record = False

    def print_report_house_bol(self):
        freight_id = self.freight_record
        freight_id.sudo().write({
            'is_fr_prepaid_h': self.is_house_fr_prepaid,
            'is_fr_collect_h' : self.is_house_fr_collect,
            'is_fr_3rd_party_h' : self.is_house_fr_3rd_party,
            'cod_amount_h' : self.house_cod_amount,
            'is_fee_prepaid_h' : self.is_house_fee_prepaid,
            'is_fee_collect_h': self.is_house_fee_collect,
            'is_customer_check_h' : self.is_house_check,
            'date_h' : self.house_date,
            'pickup_date_h' : self.house_pickup_date,
            'is_by_shipper_trai_h' : self.is_house_by_shipper_trai,
            'is_by_driver_trai_h' : self.is_house_by_driver_trai,
            'is_by_shipper_freight_h' : self.is_house_by_shipper_freight,
            'is_by_driver_freight_h' : self.is_house_by_driver_freight,
            'is_by_pieces_h' : self.is_house_by_pieces,
            'shipper_sign_h' : self.house_shipper_sign,
            'carrier_sign_h' : self.house_carrier_sign,
        })
        report =  self.env.ref('warefor_reports.house_bol_report_template').report_action(freight_id)
        return report