from odoo import models


class SpreadsheetDashboard(models.Model):
    _name = 'spreadsheet.dashboard'
    _inherit = ['spreadsheet.dashboard', 'spreadsheet.collaborative.mixin']

    def action_edit_dashboard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "action_edit_dashboard",
            "params": {
                "spreadsheet_id": self.id,
            },
        }

    def _save_concurrent_revision(self, next_revision_id, parent_revision_id, commands):
        result = super()._save_concurrent_revision(next_revision_id, parent_revision_id, commands)
        if result:
            # find ir model data related and set to no update
            self.env["ir.model.data"].sudo().search([
                ("model", "=", self._name),
                ("res_id", "=", self.id),
            ], order='id asc', limit=1).write({'noupdate': True})

        return result


    def write(self, vals):
        if "data" in vals:
            self._delete_collaborative_data()
        return super().write(vals)
