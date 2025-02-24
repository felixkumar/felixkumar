from odoo import models, fields, _


class ShipstationService(models.Model):
    """
    Added shipstation service model to add shipstation fields.
    """
    _name = 'shipstation.services.ept'
    _description = 'Shipstation Service'
    _rec_name = 'service_name'

    shipstation_instance_id = fields.Many2one('shipstation.instance.ept',
                                              string="Shipstation Services",
                                              ondelete="cascade",
                                              help="to choose Shipstation instance")
    ept_shipstation_carrier_id = fields.Many2one('shipstation.carrier.ept',
                                             string='Shipstation Carrier',
                                             ondelete='cascade')
    service_type = fields.Selection([('domestic', 'Domestic'),
                                     ('international', 'International'),
                                     ('both', 'Both')],
                                    string="Service Type")
    service_code = fields.Char(string="Service Code", help="Hold service code string")
    service_name = fields.Char(string="Service Name", help="Hold service name string")
    company_id = fields.Many2one('res.company', string="Company", required=True)
    active = fields.Boolean('Active',
                            help="If the active field is set to False, then "
                                 "can not access the Shipstation Service.",
                            default=True)

    def add_new_shipstation_service(self):
        """
        Create new create delivery method from the selection shipstation service
        @return: action window to the carrier create Form.
        """
        self.ensure_one()
        shipstation_instance_obj = self.env['shipstation.instance.ept']
        context = dict(self.env.context or {})
        view = self.env.ref('delivery.view_delivery_carrier_form')
        product_id = self.env['product.product'].search(
            [('default_code', '=', 'SHIP_SHIPSTATION'),
             ('company_id', '=', self.shipstation_instance_id.company_id.id)])
        if not product_id:
            product_id = self.env.ref('shipstation_ept.ship_product_shipstation')
        if view:
            context.update({
                'default_name': "{0} - {1}".format(self.service_name, self.ept_shipstation_carrier_id.name),
                'default_ept_shipstation_carrier_id': self.ept_shipstation_carrier_id.id or False,
                'default_shipstation_service_id': self.id or False,
                'default_product_id': product_id.id,
                'default_delivery_type': 'shipstation_ept',
                'default_prod_environment': self.shipstation_instance_id.prod_environment,
                'default_shipstation_instance_id': self.shipstation_instance_id.id
            })
            if hasattr(
                    shipstation_instance_obj,
                    '%s_quick_add_shipstation_services' % self.shipstation_instance_id.provider) and self.service_code:
                context.update(getattr(shipstation_instance_obj,
                                       '%s_quick_add_shipstation_services' % self.shipstation_instance_id.provider)(
                    self.service_code, self.service_name))
            return {
                'name': _('Add Delivery Method'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'delivery.carrier',
                'view_id': view.id,
                'type': 'ir.actions.act_window',
                'context': context,
                'target': 'current'
            }
