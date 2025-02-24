# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    analytic_account_id = fields.Many2one(comodel_name="account.analytic.account", string="Analytic Account")
