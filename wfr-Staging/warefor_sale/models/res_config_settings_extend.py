# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettingsExtend(models.TransientModel):
    _inherit = 'res.config.settings'

    so_order_approval = fields.Boolean("Sale Order Approval", default=lambda self: self.env.company.so_double_validation == 'two_step')
    so_double_validation = fields.Selection(related='company_id.so_double_validation', string="Sale Order Levels of Approvals *", readonly=False)

    def set_values(self):
        super(ResConfigSettingsExtend, self).set_values()
        self.so_double_validation = 'two_step' if self.so_order_approval else 'one_step'
