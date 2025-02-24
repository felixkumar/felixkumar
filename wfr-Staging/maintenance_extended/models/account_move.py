# -*- coding: utf-8 -*-
from odoo import models, fields, _, api


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends('maintenance_ids')
    def _domain_equipment_records(self):
        self.maintenance_request = []
        if self and self.maintenance_ids:
            self.maintenance_request = [(6, 0, self.mapped('maintenance_ids').mapped('maintenance_ids').ids)]


    maintenance_ids = fields.One2many(comodel_name='maintenance.equipment', inverse_name='move_id', string='Equipment Serial #')
    maintenance_request = fields.Many2many(comodel_name="maintenance.request", string='Maintenance', compute="_domain_equipment_records")
    maintenance_request_ids = fields.One2many(comodel_name='maintenance.request', inverse_name='move_id', string='Maintenance', domain="[('id', 'in', maintenance_request)]")
    maintenance_id = fields.Many2one(comodel_name='maintenance.equipment', string='Equipment Serial ID')
