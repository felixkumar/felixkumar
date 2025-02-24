from odoo import models, fields, api


class ShipstationDeliveryCarrier(models.Model):
    _name = "shipstation.delivery.carrier"
    _description = 'Shipstation Delivery Carrier'
    
    name = fields.Char(string='Carrier Name')
    code = fields.Char(string='Carrier Code')
    account_number = fields.Char(string='Account Number')
    shipping_provider_id = fields.Char(string='Shipping Provide Id')
    provider_tracking_link = fields.Char(string="Provider Tracking Link",
                                help="Tracking link(URL) useful to track the shipment or package from this URL.",
                                size=256)

    shipstation_configuration_id = fields.Many2one('shipstation.odoo.configuration.vts',
                                                   string='Shipstation Configuration')
