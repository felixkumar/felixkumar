#coding: utf-8

from odoo import _, api, fields, models
from odoo.addons.http_routing.models.ir_http import slug


class business_appointment(models.Model):
    """
    Reload to add website and portal related properties
    """
    _name = "business.appointment"
    _inherit = ["business.appointment", "website.published.mixin", "portal.mixin", "website.multi.mixin", ]

    success = fields.Text(help="Sucess: tech field for the website")
    error = fields.Text(help="Error: tech field for the website")

    def _compute_website_url(self):
        """
        Overwritting the compute method for portal_url to pass our pathes

        Methods:
         * super
        """
        super(business_appointment, self)._compute_website_url()
        for core in self:
            core.website_url = u'/my/business/appointments/{}'.format(slug(core))

    def _compute_access_url(self):
        """
        Overwritting the compute method for access_url to pass our pathes

        Methods:
         * super
        """
        for core in self:
            core.access_url = core.website_url

    def action_portal_cancel_reservation(self):
        """
        The method to cancel business.appointment (from portal)
        
        Methods:
         * check_cancel_timeframe of business.resource.type
         * action_cancel

        Returns:
         * cancelled appointment id or False if cannot be cancelled

        Extra info:
         * Expected singleton
        """
        allowed = self.sudo().resource_type_id.check_cancel_timeframe(self)
        if allowed:
            self.action_cancel()
            self.success = _("The appointment is successfully canceled")
        else:
            self.error = _("Sorry but this appointment cannot be canceled")
        return allowed

    @api.model
    def _mail_get_partner_fields(self):
        """
        Overwrite to make possible chatting without an access token in portal
        This will block making an access token invitation for a partner_id
        """
        return []