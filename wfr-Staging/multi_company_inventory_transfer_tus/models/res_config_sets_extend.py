# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettingsExtend(models.TransientModel):
    _inherit = 'res.config.settings'

    is_multi_company_inventory_transfer = fields.Boolean(related="company_id.is_multi_company_inventory_transfer",
                                                         readonly=False)
