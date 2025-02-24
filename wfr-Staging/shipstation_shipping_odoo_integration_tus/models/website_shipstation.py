# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class WebsiteShipstation(models.Model):
    _name = 'website.shipstation.configuration'
    _description = "Website/Shipstation Configuration"
    _rec_name = 'website_id'

    website_id = fields.Many2one("website", string="Website")
    shipstation_store_id = fields.Many2one('shipstation.store.vts', string='Shipstation Store', copy=False)
    is_export = fields.Boolean("Export In Shipstation", default=False)

    def update_configuration(self):
        """
        Enable/Disable the configuration for exporting website order automatically in Shipstation
        """
        for rec in self:
            if rec.is_export:
                rec.is_export = False
            else:
                rec.is_export = True
        return True
