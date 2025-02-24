from odoo import models,fields,api

class ShipstationShippingCharge(models.Model):
    _name="shipstation.shipping.charge"
    _description = 'Shipstation Shipping Charge'
    _rec_name="shipstation_service_code"

    shipstation_provider=fields.Char(string="Provider",help="Shipping Provider")
    shipstation_service_code = fields.Char(string="Service Code", help="Shipping service Code.")
    shipstation_service_name=fields.Char(string="Service Name",help="Shipping service name.")
    shipping_cost=fields.Float(string="Shipping Cost",help="Rate given by shippo")
    other_cost = fields.Float(string='Other Cost')
    sale_order_id=fields.Many2one("sale.order",string="Sales Order")

    def set_service(self):
        self.ensure_one()
        carrier = self.sale_order_id.carrier_id
        self.sale_order_id._remove_delivery_line()
        self.sale_order_id.shipstation_shipping_charge_id = self.id
        total_cost = self.shipping_cost + self.other_cost
        self.sale_order_id.set_delivery_line(carrier, total_cost)
        self.sale_order_id.carrier_id = carrier.id

