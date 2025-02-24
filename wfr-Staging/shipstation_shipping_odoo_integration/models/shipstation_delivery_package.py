from odoo import models, fields, api


class ShipstationDeliveryPackage(models.Model):
    _name = "shipstation.delivery.package"
    _description = 'Shipstation Delivery Package'

    name = fields.Char(string='Package Name')
    package_code= fields.Char(string='Package Code')
    service_nature = fields.Selection([('domestic','Domestic'),('international','International')],string='Service Nature')
    delivery_carrier_id = fields.Many2one('shipstation.delivery.carrier',string='Carrier Code')
    height=fields.Float("Height",default=0.0)
    width = fields.Float("Width",default=0.0)
    length = fields.Float("Length",default=0.0)
    supported_domestic = fields.Boolean(string='Domestic')
    supported_international = fields.Boolean(string='International')
    shipstation_configuration_id = fields.Many2one('shipstation.odoo.configuration.vts',
                                                   string='Shipstation Configuration')
