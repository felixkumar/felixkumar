from odoo import models, fields, api


class ShipstationDeliveryCarrierService(models.Model):
    _name = "shipstation.delivery.carrier.service"
    _description = 'Shipstation Delivery Carrier Service'
    
    name = fields.Char(string='Service Provider Name')
    service_code = fields.Char(string='Service Code')
    service_nature = fields.Selection([('domestic','Domestic'),('international','International')],string='Service Nature')
    delivery_carrier_id = fields.Many2one('shipstation.delivery.carrier',string='Carrier Code')
    residential_address = fields.Boolean(string='Residential Address',default=False)
    supported_domestic = fields.Boolean(string='Domestic')
    supported_international = fields.Boolean(string='International')
    shipstation_configuration_id = fields.Many2one('shipstation.odoo.configuration.vts',
                                                   string='Shipstation Configuration')
