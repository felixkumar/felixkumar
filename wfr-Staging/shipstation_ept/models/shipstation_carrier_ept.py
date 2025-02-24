from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ShipstationCarrier(models.Model):
    """
    Class for ShipStation Carriers.
    """
    _name = 'shipstation.carrier.ept'
    _description = 'Shipstation Carrier'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    shipstation_instance_id = fields.Many2one('shipstation.instance.ept',
                                              string='Instance',
                                              ondelete='cascade')
    shipstation_package_ids = fields.One2many('stock.package.type', 'ept_shipstation_carrier_id',
                                               string='ShipStation Packages', readonly=False)

    shipstation_service_ids = fields.Many2many('shipstation.services.ept',
                                               string='ShipStation Services',
                                               compute='_compute_services',
                                               readonly=True)
    active = fields.Boolean('Active',
                            help="If the active field is set to False, then "
                                 "can not access the Carrier.",
                            default=True)
    delivery_carrier_ids = fields.Many2many('delivery.carrier',
                                            string='Shipping Methods',
                                            compute='_compute_carriers',
                                            readonly=True)
    carrier_rate_currency_id = fields.Many2one('res.currency', string='Carrier Rate Currency',
                                               help="Convert carrier shipping rate from this currency "
                                                    "to order or company currency.")
    company_id = fields.Many2one(related='shipstation_instance_id.company_id', store=True, string='Company')
    tracking_url = fields.Char(string="Tracking URL", help="To enter URL for tracking delivery status")
    shipping_provider_id = fields.Char(readonly=True)

    def get_carrier_shipstation_packages(self):
        """
        This method is used to get package of particular shipstation carrier.
        To get package it will call get_shipstation_packages() of shipstation.instance.ept
        """
        shipstation_instance_obj = self.env['shipstation.instance.ept'].search(
            [('id', '=', self.shipstation_instance_id.id)], limit=1)
        shipstation_instance_obj.with_context(carrier_id=self.id).get_shipstation_packages()
        return True

    def get_carrier_shipstation_services(self):
        """
        This method is used to get service of particular shipstation carrier.
        To get service it will call get_shipstation_packages() of shipstation.instance.ept
        """
        shipstation_instance_obj = self.env['shipstation.instance.ept'].search(
            [('id', '=', self.shipstation_instance_id.id)], limit=1)
        shipstation_instance_obj.with_context(carrier_id=self.id).get_shipstation_services()
        return True

    def _compute_services(self):
        for service in self:
            service.shipstation_service_ids = self.env['shipstation.services.ept'].search(
                [('ept_shipstation_carrier_id', '=', service.id)])

    def _compute_carriers(self):
        for carrier in self:
            carrier.delivery_carrier_ids = self.env['delivery.carrier'].search(
                [('ept_shipstation_carrier_id', '=', self.id)])

    def create_shipping_method(self):
        """This method will create the shipping method"""
        self.ensure_one()
        self.get_carrier_shipstation_services()
        carrier_obj = self.env['delivery.carrier']
        instance = self.shipstation_instance_id
        package_id = self.env["stock.package.type"].search(
            [('shipper_package_code', '=', 'package'), ('shipstation_instance_id', '=', instance.id)], limit=1)
        shipping_methods = []
        for rec in self.shipstation_service_ids:
            carrier = carrier_obj.search(
                [('ept_shipstation_carrier_id', '=', self.id), ('shipstation_service_id', '=', rec.id),
                 ('shipstation_instance_id', '=', instance.id)], limit=1)
            if not carrier:
                # Added by [ES] | Task: 182458 | Dated on 17 Jan, 2022
                product_id = self.env['product.product'].search([('default_code', '=', 'SHIP_SHIPSTATION'),
                                                                 ('company_id', '=', instance.company_id.id)])
                vals = {"name": rec.service_name,
                        "delivery_type": "shipstation_ept",
                        "shipstation_carrier_code": self.code + '-' + rec.service_code,
                        "shipstation_instance_id": rec.shipstation_instance_id.id,
                        "shipstation_weight_uom_id": instance.weight_uom_id.id,
                        "shipstation_weight_uom": instance.shipstation_weight_uom,
                        "product_id": product_id.id,
                        'shipstation_package_id': package_id.id,
                        'ept_shipstation_carrier_id': self.id,
                        'integration_level': 'rate',
                        'shipstation_service_id': rec.id,
                        'prod_environment': instance.prod_environment,
                        "company_id": instance.company_id.id}
                carrier = carrier.create(vals)
                shipping_methods.append(carrier.id)
            _logger.info(
                "Instance: {}, Shipstation Carrier: {}, Shipstation Service: {}, Carrier: {}".format(instance.name,
                                                                                                     self.name,
                                                                                                     rec.service_name,
                                                                                                     carrier.name))
        if shipping_methods:
            return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': 'Shipping method created Successfully. ',
                        'links': [{
                        }],
                        'sticky': False,
                    }
                }
