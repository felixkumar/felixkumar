#coding: utf-8

from odoo import api, fields, models


class choose_appointment_customer(models.TransientModel):
    """
    The model to prepare contact info required for appointment
    """
    _name = "choose.appointment.customer"
    _inherit = "appointment.contact.info"
    _description = "Finish Scheduling"
    _rec_name = "partner_id"

    @api.onchange("appointment_id")
    def _onchange_appointment_id(self):
        """
        Onchange method for appointment_id

        Methods:
         * _return_appointment_values

        Extra info:
         * Expected singleton
        """
        if self.appointment_id:
            values = self.appointment_id._return_appointment_values(pure_values=True, tosession=False)
            values.update({"partner_id": self.appointment_id.partner_id.id})
            return {"value": values}

    appointment_id = fields.Many2one("business.appointment", string="Appointment")
    reservation_ids = fields.Many2many("business.appointment.core", string="Prereservations")

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overwrite to write values to trigger appointments update, not the wizard itself

        Methods:
         * write of business.appointment.core
         * action_start_prereserv() of business.appointment.core
         * _confirm_prereserv() of business.appointment.core

        Extra info:
         * in case of re-scheduling there migth only one pre-reservation --> so, we get the first
         * in case of internal pre-reservation we do not require confirmation, so we immediately approve pre-reservation
        """
        wizards = super(choose_appointment_customer, self).create(vals_list)
        for wiznnum in range(0, len(wizards)):
            vals = vals_list[wiznnum]
            vals.pop("appointment_id", None)
            vals.pop("reservation_ids", None)
            wizard = wizards[wiznnum]
            if wizard.appointment_id:
                appointment_ids = wizard.appointment_id
                pre_reservation_id = wizard.reservation_ids[0]
                pre_reservation_id.write(vals)
                pre_reservation_id.action_start_prereserv()
                pre_reservation_id._confirm_prereserv(appointment_ids)
            else:
                for pre_reservation_id in wizard.reservation_ids:
                    pre_reservation_id.write(vals)
                    pre_reservation_id.action_start_prereserv()
                appointment_ids = wizard.reservation_ids._confirm_prereserv()
        return wizards

    @api.model
    def action_return_resource_types(self, appointment_ids):
        """
        The method to find all involved resource types (used to change custom fields visibility)

        Args:
         * appointment_ids - list of ints

        Returns:
         * list OF ints
        """
        res = []
        if appointment_ids:
            appointments = self.env["business.appointment.core"].browse(appointment_ids)
            res = appointments.mapped("resource_type_id.id")
        return res
