#coding: utf-8

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class appointment_alarm(models.Model):
    """
    The model to keep alarm settings to be applied in appointment
    """
    _name = "appointment.alarm"
    _description = "Appointment Alarm"
    _rec_name = "ttype"

    @api.model
    def _default_mail_template_id(self):
        """
        Default method for email template
        """
        return self.sudo().env.ref("business_appointment.email_template_default_reminder", False)

    @api.model
    def _default_sms_template_id(self):
        """
        Default method for email template
        """
        return self.sudo().env.ref("business_appointment.sms_template_default_reminder", False)

    @api.depends("duration_uom", "duration")
    def _compute_duration_minutes(self):
        """
        Compute method for duration_minutes
        """
        for record in self:
            multiplier = record.duration_uom == "days" and 60*24 or record.duration_uom == "hours" and 60 or 1
            record.duration_minutes = record.duration * multiplier

    @api.depends("ttype", "mail_template_id", "sms_template_id")
    def _compute_template_name(self):
        """
        Compute method for template_name

        Extra info:
         * purposefully not compute to be in user language
        """
        for alarm in self:
            alarm.template_name = alarm.ttype == "email" and alarm.mail_template_id.name or alarm.ttype == "sms" \
                and alarm.sms_template_id.name or alarm.ttype == "popup" and ""

    @api.constrains("ttype", "recipients")
    def constrains_durations(self):
        """
        Constrain method for type and recipients
        """
        for record in self:
            if record.ttype == "popup" and record.recipients in ["portal", "everybody"]:
                raise ValidationError(_("Popup notifications are available only for internal users"))

    ttype = fields.Selection(
        [("email", "Email"), ("sms", "SMS"), ("popup", "Popup"),],
        string="Type",
        required=True,
        default="email",
    )
    duration_uom = fields.Selection(
        [("minutes", "Minute(s)"), ("hours", "Hour(s)"), ("days", "Day(s)")],
        string="Interval",
        required=True,
        default="days",
    )
    duration = fields.Integer("Remind Before", required="1", default=1)
    duration_minutes = fields.Integer("Duration", compute=_compute_duration_minutes, store=True)
    mail_template_id = fields.Many2one("mail.template", "Email Template", default=_default_mail_template_id)
    sms_template_id = fields.Many2one("sms.template", "SMS Template", default=_default_sms_template_id)
    template_name = fields.Char(string="Template", compute=_compute_template_name,)
    recipients = fields.Selection(
        [
            ("user_id", "Only responsible"),
            ("internal", "All internal followers"),
            ("portal", "All external followers (portal)"),
            ("everybody", "All followers"),
        ],
        string="Recipients",
        required=True,
        default="internal",
    )
    color = fields.Integer(string="Color")

    _order = "duration_minutes, id"

    _sql_constraints = [("allowed_duration", "check (duration>0)", _("The duration should be positive!"))]

    def write(self, vals):
        """
        Re-write to recover cleaned tasks

        Methods:
         * _apply_changes_to_alarms of business.appointment
        """
        res = super(appointment_alarm, self).write(vals)
        self = self.sudo()
        now = fields.Datetime.now()
        all_appointments = self.env["business.appointment"]
        for alarm in self:
            all_appointments += self.env["business.appointment"].search([
                ("state", "=", "reserved"), ("datetime_start", ">=", now), ("alarm_ids", "=", alarm.id),
            ])
        if all_appointments:
            all_appointments._apply_changes_to_alarms()
        return res

    def name_get(self):
        """
        Overloading the method to make a name since alarm doesn't have it own
        """
        result = []
        for alarm in self:
            name = _(u"{} {} {} ({}{})".format(
                alarm.duration,
                dict((alarm._fields["duration_uom"]._description_selection(self.env)))[alarm.duration_uom],
                dict((alarm._fields["ttype"]._description_selection(self.env)))[alarm.ttype],
                dict((alarm._fields["recipients"]._description_selection(self.env)))[alarm.recipients],
                alarm.template_name and " / {}".format(alarm.template_name) or "",
            ))
            result.append((alarm.id, name))
        return result
