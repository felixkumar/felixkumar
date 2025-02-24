from odoo import models, fields

class StockPicking(models.Model):
    _inherit = "stock.picking"

    updated_in_walmart = fields.Boolean(default=False, copy=False)
    walmart_instance_id = fields.Many2one('walmart.marketplace.ept', string="Walmart Marketplace",
                                          help="Walmart Marketplace")

    def mark_sent_walmart(self):
        for picking in self:
            picking.write({'updated_in_walmart': False})
        return True

    def mark_not_sent_walmart(self):
        for picking in self:
            picking.write({'updated_in_walmart': True})
        return True

class StockMove(models.Model):
    _inherit='stock.move'

    def _get_new_picking_values(self):
        """We need this method to set Walmart Instance in Stock Picking"""
        res = super(StockMove, self)._get_new_picking_values()
        order_id = self.sale_line_id.order_id
        if order_id.walmart_marketplace_id:
            res.update({'walmart_instance_id': order_id.walmart_marketplace_id.id,})
        return res
