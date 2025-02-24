from odoo import models, fields, api
from odoo.exceptions import UserError


class DeliveryRate(models.Model):
    _name = 'delivery.rate.ept'
    _description = 'Delivery Rates'

    picking_id = fields.Many2one('stock.picking', string='Picking')
    ept_shipstation_carrier_id = fields.Many2one('shipstation.carrier.ept', string='Shipstation Carrier')
    service_id = fields.Many2one('shipstation.services.ept', string='Shipstation Service')
    shipment_cost = fields.Float(string='Shipment Cost')
    other_cost = fields.Float(string='Other Cost')
    total_cost = fields.Float(compute='_get_total_cost', string='Total Cost', store=False)
    service_name = fields.Char(string="Service Name")
    selected = fields.Boolean(default=False)
    package_code = fields.Char(string="Package Code")

    @api.depends('shipment_cost', 'other_cost')
    def _get_total_cost(self):
        for rec in self:
            rec.update({'total_cost': rec.shipment_cost + rec.other_cost})
        return True

    def set_service(self):
        """
        This method set the service selected from delivery rate lines into the picking.
        @return: If package of picking and selected service's package both are not equal then
        shipstation.package_id is updated else existing flow will work
        """
        self.ensure_one()
        if self.picking_id.is_get_shipping_label or self.picking_id.is_exported_to_shipstation:
            raise UserError('Service can not be changed once the order has been exported to '
                            'the shipstation or the label has been generated!')
        if not self.service_id:
            raise UserError("This service does not exist in your database. "
                            "Try to retrieve services!")

        package_id = self.env['stock.package.type'].search(
            [('shipstation_instance_id', '=', self.service_id.shipstation_instance_id.id),
             ('shipper_package_code', '=', self.package_code)], limit=1)

        dict = {}

        if self.package_code !=  self.picking_id.shipstation_package_id.shipper_package_code:
            dict.update({'shipstation_package_id': package_id.id})
        dict.update({'shipstation_service_id': self.service_id,
                               'shipping_rates': self.total_cost})

        self.picking_id.write(dict)
        self.picking_id.delivery_rate_ids.write({'selected': False})
        self.selected = True
