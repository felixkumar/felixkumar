# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
import logging
_logger = logging.getLogger("Warehouse Aging Report")


class ProductCategory(models.Model):
    _inherit = "product.category"

    is_use_on_aging_report = fields.Boolean(string="Is Use On Aging Report?")
