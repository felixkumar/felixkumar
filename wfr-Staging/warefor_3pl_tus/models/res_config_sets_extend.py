# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettingsExtend(models.TransientModel):
    _inherit = 'res.config.settings'

    pallet_batch_email_validation = fields.Boolean(related='company_id.pallet_batch_email_validation', readonly=False)
    pallet_batch_user_id = fields.Many2one(related='company_id.pallet_batch_user_id', readonly=False)
    pallet_in_location = fields.Integer(related="company_id.pallet_in_location", readonly=False)
    rack_in_location = fields.Integer(related="company_id.rack_in_location", readonly=False)
    use_virtual_location = fields.Boolean(related="company_id.use_virtual_location", string="Use Virtual Location?",
                                          readonly=False)
