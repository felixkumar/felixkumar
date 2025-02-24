# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TrackingWizard(models.TransientModel):
    _name = 'tracking.wizard'
    _description = "Wizard for tracking order"

    freight_id = fields.Many2one('freight.freight', string="Shipping Order")
    port_loading_id = fields.Many2one(related='freight_id.port_loading_id', string="Loading Port")
    port_shipping_id = fields.Many2one(related='freight_id.port_shipping_id', string="Discharging Port")
    transport = fields.Many2one("freight.transport", related='freight_id.freight_transport_id', string="Transport")
    stage_id = fields.Many2one(related='freight_id.stage_id', string="Stage", group_expand='_read_group_stage_ids')
    freight_tracking_ids = fields.One2many(related='freight_id.freight_tracking_ids', string="Tracking")

    def action_track(self):
        view_id = self.env.ref('mc_freight_app.tracking_order_form').id

        return {
            'name': ('Track Order Details'),
            'view_mode': 'form',
            'res_model': 'tracking.wizard',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new'
        }