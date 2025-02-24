# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    picking_id = fields.Many2one('stock.picking', string="Transfer")
    order_id = fields.Many2one('sale.order', required=False, ondelete="cascade")

    # @api.depends('partner_id')
    # def _compute_available_carrier(self):
    #     for rec in self:
    #         if rec._context.get('active_model') == 'stock.picking':
    #             carriers = self.env['delivery.carrier'].search(
    #                 ['|', ('company_id', '=', False), ('company_id', '=', rec.picking_id.company_id.id)])
    #             rec.available_carrier_ids = carriers.available_carriers(rec.partner_id) if rec.partner_id else carriers
    #         elif rec._context.get('active_model') == 'freight.freight':
    #             carriers = self.env['delivery.carrier'].search(
    #                 ['|', ('company_id', '=', False), ('company_id', '=', self.env.company.id)])
    #             rec.available_carrier_ids = carriers.available_carriers(rec.partner_id) if rec.partner_id else carriers
    #         else:
    #             carriers = self.env['delivery.carrier'].search(
    #                 ['|', ('company_id', '=', False), ('company_id', '=', rec.order_id.company_id.id)])
    #             rec.available_carrier_ids = carriers.available_carriers(
    #                 rec.order_id.partner_shipping_id) if rec.partner_id else carriers

    def _get_shipment_rate(self):
        self = self.sudo()
        vals = self.carrier_id.picking_rate_shipment(self.order_id or self.picking_id)
        if vals.get('success'):
            self.delivery_message = vals.get('warning_message', False)
            self.delivery_price = vals['price']
            self.display_price = vals['carrier_price']
            return {}
        return {'error_message': vals['error_message']}

    def update_price(self):
        vals = self.with_company(self.order_id.sudo().company_id)._get_shipment_rate()
        if vals.get('error_message'):
            raise UserError(vals.get('error_message'))
        return {
            'name': _('Add a shipping method'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'choose.delivery.carrier',
            'res_id': self.id,
            'target': 'new',
            'context': {'default_company_id': self.order_id.sudo().company_id.id or self.picking_id.sudo().company_id.id}
        }

    @api.depends('partner_id')
    def _compute_available_carrier(self):
        self = self.sudo()
        for rec in self:
            carriers = self.env['delivery.carrier'].search(['|', ('company_id', '=', False), ('company_id', '=', rec.order_id.company_id.id)])
            rec.available_carrier_ids = carriers.available_carriers(rec.order_id.partner_shipping_id) if rec.partner_id else carriers

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ChooseDeliveryCarrier, self.sudo()).create(vals_list)
        return records

    def write(self, vals):
        records = super(ChooseDeliveryCarrier, self.sudo()).write(vals)
        return records

    def button_confirm(self):
        self = self.sudo()
        self.order_id.set_delivery_line(self.carrier_id, self.delivery_price)
        self.order_id.write({
            'recompute_delivery_price': False,
            'delivery_message': self.delivery_message,
        })
