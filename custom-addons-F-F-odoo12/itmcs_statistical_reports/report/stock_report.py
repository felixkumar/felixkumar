from odoo import fields, models


# stock report model
class StockReport(models.Model):
    _name = "stock.report"
    _description = "Stock Report"  

    warehouse_id = fields.Many2one(
        'stock.warehouse', 'Warehouse',
         readonly=True, required=True)
    product_id = fields.Many2one(
        'product.product', 'Product',
         readonly=True, required=True)
    cost = fields.Float('Weighted Avg cost', group_operator='avg')
    qty_opening = fields.Float('Quantity opening')
    qty_in = fields.Float('Quantity in')
    qty_out = fields.Float('Quantity out')
    qty_closing = fields.Float('Quantity closing')
    stock_value = fields.Float('Stock value')
    
# stock report custom model    
class StockReportCustom(models.Model):
    _name = "stock.report.custom"
    _description = "Stock Report"  

    warehouse_id = fields.Many2one(
        'stock.warehouse', 'Warehouse',
         readonly=True, required=True)
    product_id = fields.Many2one(
        'product.product', 'Product',
         readonly=True, required=True)
    cost = fields.Float('Weighted Avg cost', group_operator='avg')
    stock_value = fields.Float('Stock value')    
    qty_closing = fields.Float('Quantity closing')
