from odoo import models, _

class WalmartOnboardingConfirmationEpt(models.TransientModel):
    _name = 'walmart.onboarding.confirmation.ept'
    _description = 'Walmart Onboarding Confirmation'

    def done_all_configuration(self):
        """ Save the Cron Changes by Instance Wise.
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 29 July 2021 .
            Task_id: 176151 - Walmart Panel
        """
        instance_id = self._context.get('walmart_marketplace_id', False)
        if instance_id:
            instance = self.env['walmart.marketplace.ept'].browse(instance_id)
            company = instance.company_id
            company.write({
                'walmart_instance_onboarding_state': 'not_done',
                'walmart_general_configuration_onboarding_state': 'not_done',
                'walmart_cron_configuration_onboarding_state': 'not_done',
                'is_create_walmart_more_instance': False
            })
            instance.write({'is_onboarding_configurations_done': True})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Operation completed successfully!'),
                    'message': _("Congratulations, You have done All Configurations of the instance: {}".format(
                            instance.name)),
                    'type': 'success',
                    'sticky': False
                },
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def remaining_configuration(self):
        """ Unsave the changes and reload the page.
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on 29 21 July 2021 .
            Task_id: 176151 - Walmart Panel
        """
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
