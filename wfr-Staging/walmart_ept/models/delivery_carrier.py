from odoo import models, fields

class DeliverCarrier(models.Model):
    _inherit = 'delivery.carrier'
    _description = 'Delivery Carrier'

    walmart_shipping_method_code = fields.Char()
    walmart_carrier_code = fields.Char()
