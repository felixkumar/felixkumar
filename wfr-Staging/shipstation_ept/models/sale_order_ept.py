import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _description = 'Sale Order'

    ept_shipstation_store_id = fields.Many2one('shipstation.store.ept', string='Shipstation Store', copy=False)
    shipstation_instance_id = fields.Many2one('shipstation.instance.ept', string='Instance')
    type_of_delivery = fields.Selection(related='carrier_id.delivery_type', store=True, copy=False)
    cheapest_service_id = fields.Many2one('shipstation.services.ept', string='Selected Shipstation Service',
                                          help="Shipstation service to use for the order from this carrier.")
    cheapest_carrier_id = fields.Many2one('shipstation.carrier.ept', string='Selected Shipstation Service',
                                          help="Shipstation Carrier.")

    @api.model
    def create(self, vals):
        if vals.get('team_id'):
            team_id = self.env['crm.team'].browse(vals.get('team_id'))
            ept_shipstation_store_id = vals.get('company_id', False) and team_id.with_company(vals.get('company_id')).\
                store_id or False
            vals.update({
                'ept_shipstation_store_id': ept_shipstation_store_id and ept_shipstation_store_id.id,
                'shipstation_instance_id': ept_shipstation_store_id and ept_shipstation_store_id.shipstation_instance_id.id
            })
        res = super().create(vals)
        if not res.carrier_id and res.team_id.delivery_carrier_id:
            carrier_id = res.team_id.delivery_carrier_id
            _logger.info("Updating delivery carrier '{}' in Sale order {}.".format(carrier_id.name, res.name))
            res.update({'carrier_id': carrier_id.id, 'shipstation_instance_id': carrier_id.shipstation_instance_id.id})
        elif res.carrier_id and res.carrier_id.shipstation_instance_id and not res.shipstation_instance_id:
            res.update({'shipstation_instance_id': res.carrier_id.shipstation_instance_id.id})
        return res

    def write(self, vals):
        """
        Update shipstation instance if delivery carrier update in sale order from code.
        """
        res = super(SaleOrder, self).write(vals)
        if res:
            for order in self:
                if vals.get('carrier_id') and not vals.get('shipstation_instance_id'):
                    new_carrier = self.env['delivery.carrier'].browse(vals.get('carrier_id'))
                    if new_carrier.shipstation_instance_id:
                        order.write({
                            'shipstation_instance_id': new_carrier.shipstation_instance_id.id or False
                        })
                    elif vals.get('team_id'):
                        team_id = self.env['crm.team'].browse(vals.get('team_id'))
                        order.write({
                            'ept_shipstation_store_id': team_id.store_id.id or False,
                            'shipstation_instance_id': team_id.store_id and
                                                       team_id.store_id.shipstation_instance_id.id or False
                        })
                    elif order.team_id:
                        order.write({
                            'ept_shipstation_store_id': order.team_id.store_id.id or False,
                            'shipstation_instance_id': order.team_id.store_id and
                                                       order.team_id.store_id.shipstation_instance_id.id or False
                        })
                    else:
                        order.write({
                            'shipstation_instance_id': False
                        })
        return res

    def set_delivery_line(self, carrier, amount):
        res = super().set_delivery_line(carrier, amount)
        if carrier.shipstation_instance_id.provider == "shipstation_ept":
            self.shipstation_instance_id = carrier.shipstation_instance_id.id
            if not self.ept_shipstation_store_id.shipstation_instance_id == self.shipstation_instance_id:
                self.ept_shipstation_store_id = False
        return res

    @api.onchange('shipstation_instance_id')
    def onchange_instance_id(self):
        if self.team_id.store_id.shipstation_instance_id.id != self.shipstation_instance_id.id:
            self.ept_shipstation_store_id = False

    @api.onchange('team_id')
    def onchange_team_id(self):
        self.write({
            'shipstation_instance_id': self.team_id.store_id.shipstation_instance_id.id,
            'ept_shipstation_store_id': self.team_id.store_id.id
        })

    def action_open_delivery_wizard(self):
        """
        we need this as in case we don't have a service selected on delivery method, we raise a
        warning hence it will throw error without this method as the method get_rates will be
        called onclick of "update shipping cost" on the sale order
        """
        view_id = self.env.ref('delivery.choose_delivery_carrier_view_form').id
        if self.env.context.get('carrier_recompute'):
            name = _('Update shipping cost')
            if not self.carrier_id.delivery_type == 'shipstation_ept':
                carrier = self.carrier_id
            else:
                carrier = self.partner_id.property_delivery_carrier_id
        else:
            name = _('Add a shipping method')
            carrier = self.partner_id.property_delivery_carrier_id
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'choose.delivery.carrier',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_carrier_id': carrier.id,
            }
        }

    def unlink_old_message_and_post_new_message(self, body):
        message_ids = self.env["mail.message"].sudo().search(
            [('model', '=', 'sale.order'), ('res_id', '=', self.id), ('body', '=', body)])
        message_ids.unlink()
        self.message_post(body=body)
