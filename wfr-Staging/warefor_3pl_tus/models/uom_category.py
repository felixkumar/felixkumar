# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class UomCategory(models.Model):
    _inherit = "uom.category"

    is_time_category = fields.Boolean(string="Is Time Category")
