# -*- coding: utf-8 -*-

from odoo import api, fields, models


class BaseModuleUninstall(models.TransientModel):
    _inherit = "base.module.uninstall"

    def action_uninstall(self):
        modules = self.module_id
        for module in modules:
            if module.name == 'custom_backend_theme':
                # If the module Custom Backend Theme is uninstalled: remove NoUpdate + Update module "Web"
                ir_ui_view = self.env.ref('web.layout', raise_if_not_found=False)
                if ir_ui_view:
                    model_data = self.env['ir.model.data'].sudo().search(
                        [('model', '=', 'ir.ui.view'), ('module', '=', 'web'), ('res_id', '=', ir_ui_view.id)])
                    model_data.noupdate = False

                self.env['ir.module.module'].search([('name', '=', 'web')]).button_immediate_upgrade()
        return modules.button_immediate_uninstall()
