# Copyright 2020 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    outgoing_routing_strategy = fields.Selection(
        [
            # path should be valid for both stock pickings and quants
            ('location_id.removal_prio', 'Location removal priority'),
            ('location_id.name', 'Location name'),
            ('product_id.name', 'Product name'),
        ],
        string='Picking Strategy', default='location_id.name')

    outgoing_routing_order = fields.Selection(
        [
            ('0', 'Ascending (A-Z)'),
            ('1', 'Descending (Z-A)'),
        ],
        string='Picking Order', default='0')

    stock_reservation_strategy = fields.Selection(
        [
            ('base', 'By Picking Strategy'),
            ('quantity', 'By Quantity'),
            ('none', 'Default'),
        ],
        string='Reservation Strategy', default='base')

    routing_module_version = fields.Char(
        string='Routing Module Version',
        compute='_compute_routing_module_version',
        compute_sudo=True,
    )

    def _compute_routing_module_version(self):
        self.env.cr.execute(
            "SELECT latest_version FROM ir_module_module WHERE name='outgoing_routing'"
        )
        result = self.env.cr.fetchone()
        full_version = result and result[0]
        split_value = full_version and full_version.split('.')
        module_version = split_value and '.'.join(split_value[-3:])

        for rec in self:
            rec.routing_module_version = module_version
