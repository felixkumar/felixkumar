from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        if self.sale_line_id:
            vals['shipstation_order_id'] = self.sale_line_id.order_id.shipstation_order_id or ''
            vals['shipstation_sale_order_number'] = self.sale_line_id.order_id.shipstation_order_number or ''
            vals['shipstation_carrier_code'] = self.sale_line_id.order_id.carrierCode or ''
            vals['shipstation_service_code'] = self.sale_line_id.order_id.serviceCode or ''
        return vals