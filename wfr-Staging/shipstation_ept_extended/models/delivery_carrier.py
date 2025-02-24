# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    is_lowest_cost = fields.Boolean(string="Is Lowest Cost", copy=False)