#coding: utf-8

from odoo import api, fields, models

from odoo.addons.http_routing.models.ir_http import slug
from odoo.tools.safe_eval import safe_eval
from odoo.tools.translate import html_translate


class business_resource_type(models.Model):
    """
    Reload to add website and portal related properties
    """
    _name = "business.resource.type"
    _inherit = ["business.resource.type", "website.published.mixin",  "website.seo.metadata", "portal.mixin",
        "website.multi.mixin"]

    def _compute_website_url(self):
        """
        Overwritting the compute method for portal_url to pass our pathes

        Methods:
         * super
        """
        super(business_resource_type, self)._compute_website_url()
        for rtype in self:
            rtype.website_url = u"/appointments/types/{}".format(slug(rtype))

    def _compute_access_url(self):
        """
        Overwritting the compute method for access_url to pass our pathes

        Methods:
         * super
        """
        for rtype in self:
            rtype.access_url = rtype.website_url

    full_website_description = fields.Html(
        string="Website Description", 
        translate=html_translate,
        default="",
    )
    donotshow_full_description = fields.Boolean(string="Do not show website full description")
    allowed_cancellation = fields.Integer(
        string="Portal: Cancellation/Re-Schedule might be done in",
        default="1",
        help="""* Set zero to allow at any moment before an appointment
* Set minus 1 to forbid cancellation and re-schedule""",
    )
    allowed_cancellation_uom = fields.Selection(
        [
            ("hours", "hours"),
            ("days", "days"),
            ("weeks", "weeks"),
            ("months", "months"),
            ("years", "years"),
        ],
        string="Cancellation UoM",
        default="days",
    )

    def action_portal_publish_button(self):
        """
        The button to publish / unpublish resource type
        """
        for rtype in self:
            rtype.website_published = not rtype.website_published

    def edit_website(self):
        """
        Open url of this resource type on website
        """
        return {
            "type": "ir.actions.act_url",
            "target": "new",
            "url": "/appointments/types/{}?enable_editor".format(self.id),
        }

    def _return_viable_resources(self, website_id):
        """
        The method to define whether this resource has published service

        Args:
         * website_id - website object

        Methods:
         * _return_check_viable of business.resource
         * _return_viable_resource

        Returns:
         * business.resource recordset
        """
        viable = self.env["business.resource"]
        for rtype in self:
            viable += viable.union(rtype.resource_ids.filtered(lambda reso: reso._return_check_viable(website_id) \
                                                                and reso._return_viable_services(website_id) 
            ))
        return viable

    def _return_check_viable(self, website_id):
        """
        The method to check whether this resource type is available for appointments

        Args:
         * website_id - website object
        
        Extra info:
         * Expected singleton
        """
        res = True
        if not self.active or not self.website_published or self.website_id.id not in (False, website_id.id):
            res = False
        return res

    def check_cancel_timeframe(self, appointment):
        """
        The method to define the datetime after which cancellation / re-schedule are not possible

        Args:
         * business.appointment record

        Methods:
         * _return_restriction_delta

        Returns:
         * datetime.datetime or False if not allowed

        Extra info:
         * expected singleton
        """
        res = False
        if self.allowed_cancellation >= 0:
            delta = self._return_restriction_delta(self.allowed_cancellation_uom, self.allowed_cancellation)
            appointment_date = fields.Datetime.from_string(appointment.datetime_start)
            to_compare = appointment_date - delta
            if to_compare > fields.Datetime.now():
                res = True
        return res

    @api.model
    def _return_number_of_appointments_portal(self, website):
        """
        The method to return maximum number of appointments based on website configuration

        Args:
         * website - website object

        Returns:
         * int
        """
        ICPSudo = self.env["ir.config_parameter"].sudo()
        multi_schedule = safe_eval(ICPSudo.get_param("ba_multi_scheduling", default="False"))
        appoitnment_number = 1
        if multi_schedule:
            appoitnment_number = website.ba_max_multi_scheduling_portal
            appoitnment_number = appoitnment_number <= 0 and 1 or appoitnment_number
        return appoitnment_number

