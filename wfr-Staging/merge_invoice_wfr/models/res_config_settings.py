# -*- coding: utf-8 -*-
# Part of WFR.

from odoo import models, fields


class ResCompanyInherit(models.Model):
    _inherit = "res.company"

    sh_inv_sub_merge_qty = fields.Boolean(string=" Subtract Merged Quantity ")


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = "res.config.settings"

    sh_inv_sub_merge_qty = fields.Boolean(
        related="company_id.sh_inv_sub_merge_qty", string=" Subtract Merged Quantity ", readonly=False)
