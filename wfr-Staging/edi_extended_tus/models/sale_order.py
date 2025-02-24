from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ship_not_before = fields.Date(string="Ship Not Before")
    ship_not_later_than = fields.Date(string="Ship Not Later Than")
    must_arrive_by = fields.Date(string="Must Arrive By")
