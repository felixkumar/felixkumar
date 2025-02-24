import logging
from odoo import models, fields, api

_logger = logging.getLogger("InAppNotification")


class EmiproAppVersionDetails(models.Model):
    _inherit = 'emipro.app.version.details'

    def disable_notification_walmart_ept(self, module_name):
        """
        This method are used to find the update details of specific module, and disable the
        notification for that specific module for the customer.
        :created_by: Yagnik Joshi
        :create_date: 28.02.2023
         -----------------
        :param module_name: string
        :return: True
        """
        module = self.env['ir.module.module'].sudo()
        modules = module.search([('shortdesc', 'in', [module_name, 'Common Connector Library'])])
        if modules:
            details = self.sudo().search([('module_id', 'in', modules.ids)])
            if self.sudo().user_has_groups('walmart_ept.group_walmart_manager') and details:
                details.write({'is_notify': False})
        return True
