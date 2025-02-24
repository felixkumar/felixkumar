#coding: utf-8

from odoo import fields, models

from odoo.addons.http_routing.models.ir_http import slug
from odoo.tools.translate import html_translate


class business_resource(models.Model):
    """
    Reload to add website and portal related properties
    """
    _name = "business.resource"
    _inherit = ["business.resource", "website.published.mixin",  "website.seo.metadata", "portal.mixin",
        "website.multi.mixin",]

    def _compute_website_url(self):
        """
        Overwritting the compute method for portal_url to pass our pathes

        Methods:
         * super
        """
        super(business_resource, self)._compute_website_url()
        for ba_resource in self:
            ba_resource.website_url = u"/appointments/resources/{}".format(slug(ba_resource))

    def _compute_access_url(self):
        """
        Overwritting the compute method for access_url to pass our pathes

        Methods:
         * super
        """
        for ba_resource in self:
            ba_resource.access_url = ba_resource.website_url

    full_website_description = fields.Html(
        string="Website Description", 
        translate=html_translate,
        default="",
    )
    donotshow_full_description = fields.Boolean(string="Do not show website full description")

    def action_portal_publish_button(self):
        """
        The button to publish / unpublish resource type
        """
        for ba_resource in self:
            ba_resource.website_published = not ba_resource.website_published
    
    def edit_website(self):
        """
        Open url of this resource type on website
        """
        return {
            "type": "ir.actions.act_url",
            "target": "new",
            "url": "/appointments/resources/{}?enable_editor".format(self.id),
        }

    def _return_viable_services(self, website_id):
        """
        The method to define whether this resource has published service

        Args:
         * website_id - website object

        Methods:
         * _return_check_viable of appointment.product

        Returns:
         * appointment.product recordset
        """
        viable = self.env["appointment.product"]
        for ba_resource in self:
            viable = viable.union(ba_resource.final_service_ids.filtered(
                lambda serv: serv._return_check_viable(website_id, self.env.user.sudo().company_id)
            ))
        return viable
    
    def _return_check_viable(self, website_id):
        """
        The method to check whether this resource is available for appointments

        Args:
         * website_id - website object
        
        Extra info:
         * Expected singleton
        """
        res = True
        if not self.active or not self.website_published or self.website_id.id not in (False, website_id.id):
            res = False
        return res
