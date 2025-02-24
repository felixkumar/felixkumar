# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AppointmentType(models.Model):
    _inherit = "appointment.type"

    lead_create = fields.Boolean(string="Create Opportunities",
        help="For each scheduled appointment, create a new opportunity and assign it to the responsible user.")
    opportunity_id = fields.Many2one('crm.lead', "Opportunity/Lead",
        help="Link an opportunity/lead to the appointment type created.\n"
            "Used when creating a custom appointment type from the Meeting action in the crm form view.")

    @api.model
    def _get_calendar_view_appointment_type_default_context_fields_whitelist(self):
        """ Add the opportunity_id field to list of fields we accept as default in context """
        whitelist_fields = super()._get_calendar_view_appointment_type_default_context_fields_whitelist()
        whitelist_fields.append('opportunity_id')
        return whitelist_fields
