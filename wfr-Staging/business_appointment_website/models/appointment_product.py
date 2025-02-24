#coding: utf-8

from odoo import fields, models
from odoo.tools.translate import html_translate


class appointment_product(models.Model):
    """
    Overwrite to add website publish properties
    """
    _name = "appointment.product"
    _inherit = ["appointment.product", "website.published.mixin",  "website.seo.metadata", "portal.mixin",
                "website.multi.mixin",]

    def _compute_website_url(self):
        """
        Overwritting the compute method for portal_url to pass our pathes

        Methods:
         * super
        """
        super(appointment_product, self)._compute_website_url()
        for product in self:
            product.website_url = u"/appointments/services/{}".format(slug(product))

    def _compute_access_url(self):
        """
        Overwritting the compute method for access_url to pass our pathes

        Methods:
         * super
        """
        for product in self:
            product.access_url = product.website_url

    full_website_description = fields.Html(
        string="Website Appointments Description",
        translate=html_translate,
        default="",
    )
    donotshow_full_description = fields.Boolean(string="Do not show website full description")

    def action_portal_publish_button(self):
        """
        The button to publish / unpublish resource type
        """
        for product in self:
            product.website_published = not product.website_published

    def edit_website(self):
        """
        Open url of this resource type on website
        """
        return {
            "type": "ir.actions.act_url",
            "target": "new",
            "url": "/appointments/services/{}?enable_editor".format(self.id),
        }

    def _return_check_viable(self, website_id, company_id):
        """
        The method to check whether this service is available for appointments

        Args:
         * website_id - website object
         * company_id - res_company
        
        Extra info:
         * Expected singleton
        """
        res = True
        if not self.active or not self.website_published \
                or self.website_id.id not in (False, website_id.id) \
                or self.company_id.id not in (False, company_id.id):
            res = False
        return res
