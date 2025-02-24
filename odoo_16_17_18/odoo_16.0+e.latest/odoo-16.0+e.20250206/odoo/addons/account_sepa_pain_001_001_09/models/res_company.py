# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    account_sepa_lei = fields.Char(related='partner_id.account_sepa_lei', readonly=False)
