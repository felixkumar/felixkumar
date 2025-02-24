from odoo import models, fields, api

class PurchaseWeight(models.Model):

   _inherit = 'purchase.order.line'

   po_weight = fields.Float(string='Gross Weight',
                               store=True,
                               related='product_id.display_weight')
   po_volume = fields.Float(string='Volume',
                               store=True,
                               related='product_id.display_volume')
   po_quantity = fields.Float(string='Quantity',
                               store=True,
                               related='product_qty')

class PurchaseWeightOrder(models.Model):
  
    _inherit = 'purchase.order'
    @api.one
    @api.depends('order_line.po_weight')
    @api.depends('order_line.po_quantity')
    def _calcweight(self):
        currentweight = 0
        for order_line in self.order_line:
            currentweight = currentweight + (order_line.po_weight * order_line.po_quantity)

        self.po_weight_total = currentweight

    po_weight_total = fields.Float(compute='_calcweight', string='Total Gross Weight')


class PurchaseVolumeOrder(models.Model):
  
    _inherit = 'purchase.order'
    @api.one
    @api.depends('order_line.po_volume')
    @api.depends('order_line.po_quantity')

    def _calcvolume(self):
        currentvolume = 0
        for order_line in self.mapped('order_line'):
            self.po_volume_total += (order_line.po_volume * order_line.po_quantity)



    po_volume_total = fields.Float(compute='_calcvolume', string='Volume')

    
