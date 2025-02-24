from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sales_channel_id = fields.Many2one('sales.channel', string='Sales Channel', related="team_id.sales_channel_id",
                                       readonly=True, store=True)
