from odoo import models, fields, api, _


class AccountAssetAsset(models.Model):
    """
    Account Asset Asset Inherits
    """
    _inherit = 'account.asset.asset'

    maintenance_equipment_ids = fields.Many2many('maintenance.equipment', string="Internal Equipment #", copy=False)
    maintenance_equipment_count = fields.Integer(compute='_compute_maintenance_equipment_count', string="Maintenance Count", store=True)

    def open_maintenance_equipment(self):
        return {
            'name': _('Maintenance'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'maintenance.request',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.maintenance_equipment_ids.maintenance_ids and self.maintenance_equipment_ids.maintenance_ids.ids or [])],
        }

    @api.depends('maintenance_equipment_ids')
    def _compute_maintenance_equipment_count(self):
        self.maintenance_equipment_count = len(self.maintenance_equipment_ids.maintenance_ids)
