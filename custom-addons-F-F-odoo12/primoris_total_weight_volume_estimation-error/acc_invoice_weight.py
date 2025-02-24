from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, pycompat

class InvoiceWeight(models.Model):

   _inherit = 'account.invoice.line'

   in_weight = fields.Float(string='Gross Weight',
                               store=True,
                               related='product_id.display_weight')
   in_volume = fields.Float(string='Volume',
                               store=True,
                               related='product_id.display_volume')
   in_quantity = fields.Float(string='Quantity',
                               store=True,
                               related='quantity')

class InvoiceWeightOrder(models.Model):
  
    _inherit = 'account.invoice'
    @api.one
    @api.depends('invoice_line_ids.in_weight')
    @api.depends('invoice_line_ids.in_quantity')

    def _calcweight(self):
        in_weight_total = 0
        for invoice_line_ids in self.mapped('invoice_line_ids') :
           self.in_weight_total += (invoice_line_ids.in_weight * invoice_line_ids.in_quantity)

    in_weight_total = fields.Float(compute='_calcweight', string='Total Gross Weight', index=True)

    
class InvoiceWeightOrder(models.Model):
  
    _inherit = 'account.invoice'
    @api.one
    @api.depends('invoice_line_ids.in_volume')
    @api.depends('invoice_line_ids.in_quantity')
    
    def _calcvolume(self):
        in_volume_total = 0
        for invoice_line_ids in self.mapped('invoice_line_ids') :
           self.in_volume_total += (invoice_line_ids.in_volume * invoice_line_ids.in_quantity)

    in_volume_total = fields.Float(compute='_calcvolume', string='Total Volume', index=True)
    


