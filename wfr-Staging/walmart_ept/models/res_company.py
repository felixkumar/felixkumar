""" Usage : Inherit the model res company and added and manage the functionality of Onboarding Panel"""
from odoo import fields, models, api

WALMART_ONBOARDING_STATES = [('not_done', "Not done"), ('just_done', "Just done"), ('done', "Done"),
                             ('closed', "Closed")]

class ResCompany(models.Model):
    """
        Inherit Class and added and manage the functionality of Onboarding (Banner) Panel
    """
    _inherit = 'res.company'

    # Walmart Onboarding Panel
    walmart_onboarding_state = fields.Selection(selection=WALMART_ONBOARDING_STATES,
                                                string="State of the walmart onboarding panel", default='not_done')
    walmart_instance_onboarding_state = fields.Selection(selection=WALMART_ONBOARDING_STATES,
                                                         string="State of the walmart instance onboarding panel",
                                                         default='not_done')
    walmart_general_configuration_onboarding_state = fields.Selection(WALMART_ONBOARDING_STATES, default='not_done',
                                                                      string="State of the onboarding walmart financial "
                                                                             "status step")
    walmart_cron_configuration_onboarding_state = fields.Selection(WALMART_ONBOARDING_STATES, default='not_done',
                                                                   string="State of the onboarding walmart cron "
                                                                          "configurations step")
    is_create_walmart_more_instance = fields.Boolean(string='Is create walmart more instance?', default=False)
    walmart_onboarding_toggle_state = fields.Selection(selection=[('open', "Open"), ('closed', "Closed")],
                                                       default='open')

    @api.model
    def action_close_walmart_instances_onboarding_panel(self):
        """ Mark the onboarding panel as closed.
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 23 July 2021 .
            Task_id: 176151 - Walmart Panel
        """
        self.env.company.walmart_onboarding_state = 'closed'

    def get_and_update_walmart_instances_onboarding_state(self):
        """ This method is called on the controller rendering method and ensures that the animations
            are displayed only one time.
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 23 July 2021 .
            Task_id: 176151 - Walmart Panel
        """
        steps = [
            'walmart_instance_onboarding_state',
            'walmart_general_configuration_onboarding_state',
            'walmart_cron_configuration_onboarding_state',
        ]
        return self._get_and_update_onboarding_state('walmart_onboarding_state', steps)

    def action_toggle_walmart_instances_onboarding_panel(self):
        """ To change and pass the value of selection of current company to hide / show panel.
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 23 July 2021 .
            Task_id: 176151 - Walmart Panel
        """
        self.walmart_onboarding_toggle_state = 'closed' if self.walmart_onboarding_toggle_state == 'open' else 'open'
        return self.walmart_onboarding_toggle_state
