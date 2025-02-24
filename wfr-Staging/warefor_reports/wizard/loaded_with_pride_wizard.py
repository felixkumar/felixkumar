# -*- coding: utf-8 -*-
from odoo import fields, models, api
import base64
from PIL import Image
import io


class LoadedWithPrideWizard(models.TransientModel):
    _name = 'loaded.pride.wizard'
    _description = 'Loaded With Pride Wizard'

    freight_record = fields.Many2one('freight.freight' ,'Freight ID')
    is_quantity_check = fields.Boolean("Quantity Check", default=True)
    is_qc_check = fields.Boolean("QC Check", default=True)
    order_loaded_name = fields.Char('Order Picked and Loaded By')
    order_loaded_sign = fields.Binary('Order Picked and Loaded Signature', required=True)
    duty_supervisor_name = fields.Char('Name of Supervisor')
    duty_supervisor_sign = fields.Binary('Signature of Supervisor', required=True)
    skip_signature = fields.Boolean('Skip Signature', default=True)

    # @api.depends('freight_record')
    # def _compute_freight_id(self):
    #     for rec in self:
    #         freight_id = self.env.context.get('default_freight_record')
    #         if freight_id:
    #             rec.freight_record = self.env['freight.freight'].browse(freight_id)
    #         else:
    #             rec.freight_record = False

    def print_report(self):
        freight_id = self.freight_record
        if self.skip_signature:
            if freight_id.duty_supervisor_name_load:
                freight_id.duty_supervisor_name_load = False
            if freight_id.order_loaded_sign_load:
                freight_id.order_loaded_sign_load = False
        if not self.skip_signature:
            freight_id.sudo().write({
                'is_quantity_check_load': self.is_quantity_check,
                'is_qc_check_load' : self.is_qc_check,
                'order_loaded_name_load' : self.order_loaded_name,
                'order_loaded_sign_load' : self.order_loaded_sign,
                'duty_supervisor_name_load' : self.duty_supervisor_name,
                'duty_supervisor_sign_load' : self.duty_supervisor_sign
            })
        report =  self.env.ref('warefor_reports.pride_report_template_new').report_action(freight_id)
        return report
