# -*- coding: utf-8 -*-

import calendar
from odoo import models, fields, api, _


class PalletBatchTus(models.TransientModel):
    """ This model will helps to create invoice from pallet. """
    _name = 'create.pallet.invoice'
    _description = 'Create Pallet Invoice'

    partner_id = fields.Many2one('res.partner', string="Vendor")

    def create_pallet_invoice(self):
        """ This method is used to create pallet invoice.
        :return:
        """
        invoice_line_ids = []
        pallet_batch_id = self.env[self._context.get('active_model')].browse([self._context.get('active_id')])
        # is_invoice_created = pallet_batch_id.is_invoice_created
        # month = (pallet_batch_id.end_date.year - pallet_batch_id.start_date.year) * 12 + (
        #             pallet_batch_id.end_date.month - pallet_batch_id.start_date.month)
        # sdate_m_days = calendar.monthrange(pallet_batch_id.start_date.year, pallet_batch_id.start_date.month)[1]

        # if not is_invoice_created:
        #     for import_cost_line in pallet_batch_id.import_cost_ids:
        #         invoice_line_ids.append((0, 0, {
        #             'name': import_cost_line.name,
        #             'price_unit': import_cost_line.actual_cost + import_cost_line.processing_fee_amt,
        #             'quantity': 1,
        #             'month_qty': 1,
        #             'discount': 0.0,
        #         }))
        #     for vas_cost_line in pallet_batch_id.vas_cost_ids:
        #         price_unit = vas_cost_line.total_cost
        #         qty = 1
        #         invoice_line_ids.append((0, 0, {
        #             'name': vas_cost_line.name,
        #             'price_unit': price_unit,
        #             'month_qty': 1,
        #             'quantity': qty,
        #             'discount': 0.0,
        #         }))
        #         pallet_batch_id.write({'is_invoice_created': True})

        # Storage costs invoice will create every time.
        for storage_cost_line in pallet_batch_id.storage_cost_ids:
            price_unit = storage_cost_line.unit_price
            qty = storage_cost_line.total_pallet or storage_cost_line.total_cubic_feet or 1
            invoice_line_ids.append((0, 0, {
                'name': storage_cost_line.name,
                'price_unit': price_unit,
                'quantity': qty,
                'month_qty': qty,
                'discount': 0.0,
            }))

        # total_pallet_invoices = self.env['account.move'].search_count([('pallet_id', '!=', False)])
        invoice_id = self.env['account.move'].create({
            'partner_id': self.partner_id and self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.date.today(),
            'invoice_line_ids': invoice_line_ids,
            'pallet_id': pallet_batch_id.id,
        })
        # payment = self.env['account.payment'].create({'payment_type': 'outbound',
        #                                               'ref': invoice_id.name,
        #                                               'name': payment_name,
        #                                               'amount': invoice_id.amount_total,
        #                                               'pallet_id': pallet_batch_id.id,
        #                                               'partner_id': self.partner_id and self.partner_id.id,
        #                                               'partner_type': 'customer'})
        # invoice_id.write({'payment_id': payment and payment.id})
        # invoice_id.action_post()
        # payment.action_post()
        if pallet_batch_id.sale_order_id:
            # Assign pallet invoice to selected SO.
            new_invoice = []
            old_invoice = []
            if pallet_batch_id.sale_order_id.service_invoice_ids.ids:
                for inv in pallet_batch_id.sale_order_id.service_invoice_ids.ids:
                    old_invoice.append(inv)
            new_invoice = old_invoice + [invoice_id.id]
            pallet_batch_id.sale_order_id.write({
                'service_invoice_ids': [(6, 0, new_invoice)]
            })
        return invoice_id
