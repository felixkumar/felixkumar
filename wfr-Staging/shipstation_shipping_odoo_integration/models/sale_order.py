from odoo import fields,models,api,_
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    shipstation_shipping_charge_ids = fields.One2many('shipstation.shipping.charge', 'sale_order_id',
                                                      string='Shipstation Shipping Charge Matrix')
    shipstation_shipping_charge_id = fields.Many2one("shipstation.shipping.charge", string="Shipstation Service",
                                                     help="This Method Is Use Full For Generating The Label",
                                                     copy=False)
    shipstation_order_id = fields.Char(string="Shipstation Order ID",copy=False)
    shipstation_order_number = fields.Char(string="Shipstation Order Number",copy=False)
    shipstation_store = fields.Char(string="Shipstation Store ID",copy=False)
    shipstation_store_id = fields.Many2one('shipstation.store.vts',string='Shipstation Store',copy=False)
    carrierCode = fields.Char(string='CarrierCode',copy=False)
    serviceCode = fields.Char(string='ServiceCode',copy=False)
    orderStatus = fields.Char(string='OrderStatus',copy=False)
    order_custom_data = fields.Char(string='Order Custom Data',copy=False)
    is_return_order = fields.Boolean(string='Return Order',default=False)
    customer_note = fields.Char(string='Customer Note',copy=False)
    gift_note = fields.Char(string='Gift Note',copy=False)
    postal_code = fields.Char(string='Postal Code', copy=False)
    is_exported_to_shipstation = fields.Boolean(string='Order Exported to Shipstation',default=False,copy=False)
    shipstation_configuration_id = fields.Many2one('shipstation.odoo.configuration.vts',
                                                   string='Shipstation Configuration')
    shipstation_ship_date = fields.Datetime(string="Shipstation Ship Date")
    shipstation_warehouse_id = fields.Many2one('stock.warehouse', string="Shipstation Warehouse")
    do_not_confirm = fields.Boolean(string='Do Not Confirm', default=False)
    shipstation_delivery_price = fields.Float("Delivery Price", digits=(8, 2))

    def auto_process_shipstation_orders(self):
        order_ids = self.env['sale.order'].search([('state','=','draft')],order='id',limit=500)
        orders = []
        for order in order_ids:
            order.action_confirm()
            for pick in order.picking_ids:
                for move in pick.move_ids:
                    move.quantity_done = move.product_uom_qty
                pick.action_done()
                _logger.info("Done Order >>>>> :{0}".format(order))
#            order.is_return_order = True
            self._cr.commit()

    def _is_exclude_sku(self, exclude_sku_list=""):
        if not exclude_sku_list:
            return False
        line_sku = self.order_line.product_id.mapped('default_code')
        if any(x in exclude_sku_list for x in line_sku):
            return True
        return False

# class SaleOrderLine(models.Model):
#     _inherit = "sale.order.line"

#     def compute_package_volume(self):
#         for line in self:
#             line.product_volume = line.product_id.width * line.product_id.height * line.product_id.product_length

#     product_volume = fields.Float(compute='compute_package_volume', string='Volume')
