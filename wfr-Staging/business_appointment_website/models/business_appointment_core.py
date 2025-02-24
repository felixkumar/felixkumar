#coding: utf-8

from odoo import fields, models


class business_appointment_core(models.Model):
    """
    Rewrite to add website
    """
    _inherit = "business.appointment.core"

    website_id = fields.Many2one("website", string="Website", ondelete="restrict")

    def _prepare_vals_for_real_appointment_prereserv(self):
        """
        Re-write to add website for values
        """
        values = super(business_appointment_core, self)._prepare_vals_for_real_appointment_prereserv()
        values.update({"website_id": self.website_id.id})
        return values
