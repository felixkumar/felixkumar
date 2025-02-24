# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class CommonLogBookEpt(models.Model):
    """Inherit the common log book here to handel the log book in the connector"""
    _inherit = "common.log.book.ept"

    walmart_marketplace_id = fields.Many2one("walmart.marketplace.ept", "Marketplace")
    module = fields.Selection(selection_add=[('walmart_ept', 'Walmart Connector')])
