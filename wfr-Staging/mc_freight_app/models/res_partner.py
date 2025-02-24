# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_3pl_customer = fields.Boolean("Is 3PL Customer?")

    @api.model
    def default_get(self, fields):
        is_3pl_customer = self.env.context.get('is_3pl_customer')
        is_3pl_customer = is_3pl_customer or self.env.context.get('is_outbound')
        vals = super(ResPartner, self).default_get(fields)
        vals['is_3pl_customer'] = is_3pl_customer
        return vals
