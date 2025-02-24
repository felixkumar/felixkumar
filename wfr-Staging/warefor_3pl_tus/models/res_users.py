# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class ResUsers(models.Model):
    _inherit = "res.users"

    user_signature = fields.Binary('Signature', help='Signature received through the portal.', attachment=True)
    allowed_customer_ids = fields.Many2many("res.partner", string="Customers")
    is_select_all_company = fields.Boolean("Select All Allowed Companies By Default?")
