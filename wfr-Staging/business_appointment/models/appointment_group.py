#coding: utf-8

from odoo import api, fields, models


class appointment_group(models.Model):
    """
    The model to combine appointments in groups (from the same wizard or order)
    The goal is avoid multiple partners creation
    """
    _name = "appointment.group"
    _description = "Appointment Group"
    _rec_name = "id"

    @api.depends("appointment_ids")
    def _compute_appointment_len(self):
        """
        Compute method for appointment_len
        """
        for record in self:
            record.appointment_len = len(record.appointment_ids)

    partner_id = fields.Many2one("res.partner", string="Partner")
    appointment_ids = fields.One2many("business.appointment.core", "reservation_group_id", string="Appointments")
    appointment_len = fields.Integer(
        string="Number",
        compute=_compute_appointment_len,
        compute_sudo=True,
        store=True,
    )
