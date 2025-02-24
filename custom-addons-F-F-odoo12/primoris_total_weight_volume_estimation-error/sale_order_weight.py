from odoo import models, fields, api

class SaleWeight(models.Model):

   _inherit = 'sale.order.line'

   so_weight = fields.Float(string='Gross Weight',
                               store=True,
                               related='product_id.display_weight')
   
   so_volume = fields.Float(string='Volume',
                               store=True,
                               related='product_id.display_volume')
   so_quantity = fields.Float(string='Quantity',
                               store=True,
                               related='product_uom_qty')

class SaleWeightOrder(models.Model):

    _inherit = 'sale.order'
    @api.one
    @api.depends('order_line.so_weight')
    @api.depends('order_line.so_quantity')
    def _calcweight(self):
        currentweight = 0
        for order_line in self.order_line:
            currentweight = currentweight + (order_line.so_weight * order_line.so_quantity)

        self.so_weight_total = currentweight

    so_weight_total = fields.Float(compute='_calcweight', string='Total Gross Weight',index=True)


class SaleVolumeOrder(models.Model):

    _inherit = 'sale.order'
    @api.one
    @api.depends('order_line.so_volume')
    @api.depends('order_line.so_quantity')    
    def _calcvolume(self):
        currentvolume = 0
        for order_line in self.mapped('order_line'):
            self.currentvolume = self.currentvolume + (order_line.so_volume * order_line.so_quantity)

        self.so_volume_total = self.currentvolume

    so_volume_total = fields.Float(compute='_calcvolume', string='Volume',index=True)

    
