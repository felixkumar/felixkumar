# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
import logging
from odoo.exceptions import UserError
_logger = logging.getLogger("Warehouse Stock Inventory")


class ProductCategory(models.Model):
    _inherit = "stock.warehouse"

    is_use_on_report = fields.Boolean(string="Is Use On Daily Report?")

