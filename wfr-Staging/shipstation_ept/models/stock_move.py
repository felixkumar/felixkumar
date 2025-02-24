from odoo import models, fields
from odoo.exceptions import UserError


class StockMove(models.Model):
    """
    Inheriting stock_move for shipstation implementation.
    """
    _inherit = "stock.move"
    _description = "Stock Move"

    def _get_new_picking_values(self):
        res = super()._get_new_picking_values()
        order_id = self.sale_line_id.order_id
        if order_id.shipstation_instance_id:
            shipstation_warehouse = self.env['shipstation.warehouse.ept'].search(
                ['|', ('odoo_warehouse_id', '=', self.picking_type_id.warehouse_id.id),
                 ('is_default', '=', True),
                 ('shipstation_instance_id', '=', order_id.shipstation_instance_id.id)], limit=1)
            if not shipstation_warehouse:
                raise UserError('No ShipStation Warehouse Mapping available in Odoo.')
            if order_id:
                # update shipstation service details to delivery order
                if order_id.carrier_id.get_cheapest_rates:
                    shipstation_service_id = order_id.cheapest_service_id.id or False
                    ept_shipstation_carrier_id = order_id.cheapest_carrier_id.id or False
                else:
                    shipstation_service_id = order_id.carrier_id.shipstation_service_id.id or False
                    ept_shipstation_carrier_id = order_id.carrier_id.id or False
                res.update({
                    'shipstation_instance_id': order_id.shipstation_instance_id.id or order_id.ept_shipstation_store_id.shipstation_instance_id.id,
                    'confirmation': order_id.carrier_id.confirmation,
                    'shipstation_service_id': shipstation_service_id,
                    'ept_shipstation_store_id': order_id.ept_shipstation_store_id.id or False,
                    'shipstation_package_id': order_id.carrier_id.shipstation_package_id.id or False,
                    'export_order': order_id.team_id.export_order,
                    'ept_shipstation_carrier_id': ept_shipstation_carrier_id
                })
        return res

    shipstation_exported_qty = fields.Float(string="Shipstation Exported Qty")
