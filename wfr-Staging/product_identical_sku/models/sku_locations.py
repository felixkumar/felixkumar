from odoo import fields, models, api


class IdenticalSKULocations(models.Model):
    _name = 'identical.sku.locations'
    _description = 'SKU Locations'
    _rec_name = 'warehouse_id'

    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', string='Location')
    forecasted_qty = fields.Float(string='Forecasted Quantity', readonly=True)
    shipstation_qty = fields.Float(string='Shipstation Quantity', readonly=True)
    sku_id = fields.Many2one(comodel_name='identical.sku', string='Identical SKU')
