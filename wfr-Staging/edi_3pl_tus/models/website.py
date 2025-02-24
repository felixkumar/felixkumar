# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    edi_store_id = fields.Many2one("edi.customer.store", string="EDI Store ID")
