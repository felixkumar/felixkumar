# Copyright 2020 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import models, fields


class StockConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    outgoing_routing_strategy = fields.Selection(
        string='Picking Strategy',
        related='company_id.outgoing_routing_strategy',
        readonly=False)

    outgoing_routing_order = fields.Selection(
        string='Picking Order',
        related='company_id.outgoing_routing_order',
        readonly=False)

    stock_reservation_strategy = fields.Selection(
        string='Reservation Strategy',
        related='company_id.stock_reservation_strategy',
        readonly=False)
