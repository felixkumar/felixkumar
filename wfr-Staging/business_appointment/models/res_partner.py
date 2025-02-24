# -*- coding: utf-8 -*-

import json

from odoo import api, fields, models


class res_partner(models.Model):
    """
    Overwrite to add appointments buton
    """
    _inherit = "res.partner"

    @api.depends("appointment_ids")
    def _compute_appointments_len(self):
        """
        Compute method for appointments_len
        """
        for partner in self:
            partner.appointments_len = len(partner.appointment_ids)

    appointment_ids = fields.One2many("business.appointment", "partner_id", string="Appointments")
    appointments_len = fields.Integer(string="Appointments Count", compute=_compute_appointments_len, store=True)
    ba_calendar_defaults = fields.Text(string="Calendar Defaults")

    @api.model
    def action_save_ba_calendar_defaults(self, default_values):
        """
        The method to store calendar sidebar filters for future use
        
        Args:
         * default_values - dict
        """
        partner_id = self.env.user.partner_id
        partner_id.ba_calendar_defaults = json.dumps(default_values)
