# -*- coding: utf-8 -*-

from odoo import models, fields
from odoo.exceptions import UserError


class CustomInvoiceWizard(models.TransientModel):
    _name = 'custom.invoice.wizard'
    _description = 'Custom Invoice Wizard'

    invoice_type = fields.Selection([('wfl_inbound', 'WFL Invoice Inbound'),
                                     ('wfl_storage', 'WFL Invoice Storage'),
                                     ('3pl_service', '3PL Service'),
                                     ])
    end_date = fields.Date(string='End Date')

    # ('broker_invoice', 'Broker Invoice'),
    def create_custom_invoice_wizard(self):
        if self._context.get('active_model') == "purchase.order":
            purchase_id = self.env[self._context.get('active_model')].browse([self._context.get('active_id')])
            freight_id = purchase_id.freight_record and purchase_id.freight_record[0]
        else:
            freight_id = self.env[self._context.get('active_model')].browse([self._context.get('active_id')])
        if not freight_id:
            raise UserError("Did not found Logistic record!")
        if self.invoice_type == 'wfl_inbound':
            freight_id.with_context(end_date=self.end_date).generate_invoice()
            # if freight_id.is_outbound:
            #     freight_id.outbound_stage_id = self.env.ref('mc_freight_app.complete_outbound').id
            # else:
            #     freight_id.stage_id = self.env.ref('mc_freight_app.closed').id
            return True
        # if self.invoice_type == 'broker_invoice':
        #     freight_id.generate_broker_invoice()
        if self.invoice_type == 'wfl_storage':
            # freight_id.generate_wfl_invoice()
            freight_id.with_context(end_date=self.end_date).generate_wfl_level_a_invoice()
            # if freight_id.is_outbound:
            #     freight_id.outbound_stage_id = self.env.ref('mc_freight_app.complete_outbound').id
            # else:
            #     freight_id.stage_id = self.env.ref('mc_freight_app.closed').id
            return True
        if self.invoice_type == '3pl_service':
            freight_id.open_wizard_for_storage_invoice()
            # if freight_id.is_outbound:
            #     freight_id.outbound_stage_id = self.env.ref('mc_freight_app.complete_outbound').id
            # else:
            #     freight_id.stage_id = self.env.ref('mc_freight_app.closed').id
            return True
