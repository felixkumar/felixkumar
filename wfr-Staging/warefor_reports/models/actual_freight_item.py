from odoo import models, fields


class ActualFreightItems(models.Model):
    _name = 'actual.freight.items'

    product_id = fields.Many2one('product.product')
    case_qty = fields.Float(string="Case Qty")
    quantity = fields.Float(string="Quantity")
    freight_id = fields.Many2one('freight.freight')
    freight_order_line_id = fields.Many2one('freight.order.line')
