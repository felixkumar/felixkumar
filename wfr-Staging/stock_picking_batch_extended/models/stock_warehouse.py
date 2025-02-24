# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from threading import Thread
import time
import logging

from odoo import api, fields, models, _, registry, SUPERUSER_ID
from odoo.tests import Form

_logger = logging.getLogger(__name__)


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    user_id = fields.Many2one("res.users", string="Responsible")
    number_of_batch_group = fields.Integer("Number Of Batch Group")
