# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ResCompanyExtend(models.Model):
    _inherit = "res.company"

    is_multi_company_inventory_transfer = fields.Boolean(string="Multi-Company Inventory Transfer")
