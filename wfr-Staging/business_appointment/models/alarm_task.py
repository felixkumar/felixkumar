#coding: utf-8

import logging

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.addons.base.models.ir_cron import _intervalTypes

_logger = logging.getLogger(__name__)

SMS_TEXT = _("This is the SMS sent to {}: <br/>")


class alarm_task(models.Model):
    """
    The model to keep planned alarm queue
    """
    _name = "alarm.task"
    _description = "Reminder Task"
    _rec_name = "appointment_id"

    @api.depends("alarm_id", "alarm_id.duration_uom", "alarm_id.duration_minutes", "appointment_id", 
        "appointment_id.datetime_start", "appointment_id.datetime_end", "appointment_id.state")
    def _compute_alarm_time(self):
        """
        Compute method for alarm_time

        Methods:
         * _get_cron_tolerance
        """
        for task in self:
            alarm_time = False
            now_plus_tolerance, now_minus_tolerance = self._get_cron_tolerance()
            if task.appointment_id.state == "reserved" and task.appointment_id.datetime_start > now_plus_tolerance: 
                delta = relativedelta(minutes=task.alarm_id.duration_minutes)
                alarm_time = task.appointment_id.datetime_start - delta
            task.alarm_time = alarm_time

    appointment_id = fields.Many2one("business.appointment", string="Appointment", ondelete="cascade", required=True)
    alarm_id = fields.Many2one("appointment.alarm", string="Alarm", ondelete="cascade", required=True)
    alarm_time = fields.Datetime(string="Alarm Time", compute=_compute_alarm_time, store=True, compute_sudo=True)
    notified_partner_ids = fields.Many2many(
        "res.partner",
        "res_partner_alarm_task_relx_table",
        "res_partner_rel_id",
        "alarm_task_rel_id",
        string="Popup is done for"
    )

    _order = "alarm_time asc, id"

    @api.model
    def action_get_next_popup_notif(self):
        """
        The method to find all possible popup alarms
        Here we calculate alarms for the next 24 hours only. 

        Methods:
         * _clean_missed_tasks

        Returns:
         * list of dicts
        """
        now = fields.Datetime.now()
        self._clean_missed_tasks(["popup"], now - relativedelta(days=1))
        popups = []
        partner = self.env.user.partner_id
        if partner:
            all_alarms = self.search([
                ("alarm_time", "<=", now + relativedelta(days=1)),
                ("appointment_id.datetime_start", ">=", now - relativedelta(seconds=120)),
                ("appointment_id.state", "=", "reserved"),
                ("alarm_id.ttype", "in", ["popup"]),
            ])
            popups = all_alarms._do_popup_reminder()
        return popups

    @api.model
    def action_cron_reminder(self):
        """
        The method to check sms/email reminders and send those one by one
         * We go from the oldest to newest according to _order
         * We especially check for appointment datetime_start to make sure appointment is not yet started
         * We calculate tolerance as cron job interval

        Methods:
         * _clean_missed_tasks
         * _get_cron_tolerance
         * _do_email_reminder
         * _do_sms_reminder
        """
        self = self.sudo()
        now_plus_tolerance, now_minus_tolerance = self._get_cron_tolerance()
        self._clean_missed_tasks(["email", "sms"], now_minus_tolerance)
        self._cr.commit()
        all_alarms = self.search([
            ("alarm_time", "<", now_plus_tolerance),
            ("appointment_id.datetime_start", ">=", now_minus_tolerance),
            ("appointment_id.state", "=", "reserved"),
            ("alarm_id.ttype", "in", ["email", "sms"]),
        ])
        for alarm in all_alarms:
            if alarm.alarm_id.ttype == "email":
                alarm._do_email_reminder()
            else:
                alarm._do_sms_reminder()
            alarm.unlink()
            self._cr.commit()

    @api.model
    def _clean_missed_tasks(self, ttypes, mintolerance_date):
        """
        The goal is to delete all outdated alarms
         * we consider missed alarms as fully missed in order to avoid multiple notifications
    
        Args:
         * ttypes - - list - cleared alarms types
         * mintolerance_date - under this date alarms are considered as missed and are not shown any more
        """
        self = self.sudo()
        outdated_alarms = self.search([("alarm_time", "<", mintolerance_date), ("alarm_id.ttype", "in", ttypes)])
        outdated_alarms.unlink()

    def _do_popup_reminder(self):
        """
        The method to prepare list of dicts based on records
        The idea of delta is:
         1. To show missed popups if their alert time was in the Past > we show those unless they are marked done
         2. To plan Future alarms 
        
        Methods:
         * _get_recipients
         * return_scheduled_time_tz of business.appointment

        Returns:
         * list of dicts
        """
        res = []
        partner_id = self.env.user.partner_id
        for task in self:
            partners, internal = task._get_recipients()  
            partners -= task.notified_partner_ids
            if internal and partner_id.id in partners.ids:
                delta = (task.alarm_time - fields.Datetime.now()).total_seconds()
                delta = delta > 0 and delta or 1
                task = task.sudo()
                appointment_id = task.appointment_id
                message_template = _("Scheduled time: {};{}{}{}")
                mes_1 = appointment_id.resource_id \
                    and _(" Resource: {};").format(appointment_id.resource_id.name) or ""
                mes_2 = appointment_id.service_id \
                    and _(" Service: {};").format(appointment_id.service_id.name) or ""
                mes_3 = appointment_id.partner_id \
                    and _(" Contact: {}").format(appointment_id.partner_id.name) or ""
                final_message = message_template.format(appointment_id.return_scheduled_time_tz(), mes_1, mes_2, mes_3)
                res.append({
                    "alarm_id": task.id,
                    "event_id": task.appointment_id.id,
                    "title": task.appointment_id.name,
                    "message": final_message,
                    "timer": delta,
                    "notify_at": fields.Datetime.to_string(task.alarm_time),
                })
        return res

    def _do_email_reminder(self):
        """
        The method to parse template and send email
        
        Methods:
         * _get_recipients
         * _get_partners_by_languages
         * _get_template_ctx of business.appointment
         * _render_template & _render_template_qweb of mail.template
         * message_post of mail.thread

        Extra info:
         * We send one message for each language
         * Expected singleton
        """ 
        default_lang = self._context.get("lang") or self.env.user.lang
        appointment = self.appointment_id
        partners, internal = self._get_recipients()      
        partners_by_languages = self._get_partners_by_languages(partners, default_lang)
        for lang, partner_recordset in partners_by_languages.items():
            template_ctx = appointment._get_template_ctx(lang)          
            template = self.with_context(template_ctx).alarm_id.mail_template_id              
            body_html = template.with_context(template_ctx)._render_template_qweb(
                template.body_html,
                "business.appointment",
                [appointment.id],
            ).get(appointment.id)
            subject = template.with_context(template_ctx)._render_template(
                template.subject,
                "business.appointment",
                [appointment.id]
            ).get(appointment.id)
            self.appointment_id.with_context(mail_notify_force_send=True).message_post(
                body=body_html,
                subject=subject,
                subtype_xmlid=internal and "business_appointment.mt_reminder_internal" 
                    or "business_appointment.mt_reminder_external",
                partner_ids=partner_recordset.ids,
            )
        self._cr.commit()

    def _do_sms_reminder(self):
        """
        The method to parse template and send sms
        
        Methods:
         * _get_recipients
         * _get_partners_by_languages
         * _get_template_ctx of business.appointment
         * _render_template of mail.template
         * _send_sms of sms.api
         * message_post of mail.thread

        Extra info:
         * We send one message for each language
         * Expected singleton
        """ 
        default_lang = self._context.get("lang") or self.env.user.lang
        appointment = self.appointment_id
        partners, internal = self._get_recipients()      
        partners_by_languages = self._get_partners_by_languages(partners, default_lang)
        for lang, partner_recordset in partners_by_languages.items():
            template_ctx = appointment._get_template_ctx(lang)       
            template = self.with_context(template_ctx).alarm_id.sms_template_id           
            body_html = template.with_context(template_ctx)._render_template(
                template.body,
                "business.appointment",
                [appointment.id],
            ).get(appointment.id)
            mobiles = partner_recordset.mapped("mobile")
            partner_names = ",".join(partner_recordset.mapped("name"))
            if mobiles:
                try:
                    self.env["sms.api"]._send_sms(mobiles, body_html)
                    self.appointment_id.message_post(
                        body=SMS_TEXT.format(partner_names) + body_html,
                        subject=SMS_TEXT.format(partner_names),
                        subtype_xmlid="mail.mt_note",
                    )
                except Exception as e:
                    _logger.error("SMS reminder is not sent {}".format(e))            
        self._cr.commit()

    def _get_recipients(self):
        """
        The method to get followers required for notification

        Methods:
         * has_group of res.users

        Returns:
         * res.partner recordset
         * bool

        Extra info:
         * Expected singleton
        """
        partner_ids = self.env["res.partner"]
        appointment_id = self.appointment_id
        recipients = self.alarm_id.recipients
        internal = False
        if recipients == "user_id":
            partner_ids = appointment_id.user_id.partner_id
            internal = True
        else:
            partner_ids = appointment_id.message_partner_ids
            if recipients != "everybody":
                internal_partner_ids = self.env["res.partner"]
                user_ids = partner_ids.mapped("user_ids")
                if user_ids:
                    user_ids = user_ids.filtered(lambda user: user.has_group("base.group_user"))
                    internal_partner_ids = user_ids.mapped("partner_id")
                if recipients == "internal":
                    partner_ids = internal_partner_ids
                    internal = True
                elif recipients == "portal":
                    partner_ids = partner_ids - internal_partner_ids
        return partner_ids, internal

    @api.model
    def _get_partners_by_languages(self, partner_ids, defautl_lang):
        """
        The method combine partners by languages

        Atgs:
         * partner_ids - res.partner recordset
         * defautl_lang - char - default language code

        Returns:
         * dict, e.g. {"ru_RU": res.partner(12,13), "en_US": res.partner(2,14), False: res.partner(7,)}      
        """
        res = {}
        for partner in partner_ids:
            lang = partner.lang or defautl_lang
            if res.get(lang):
                res[lang] = res[lang] + partner
            else:
                res[lang] = partner
        return res

    @api.model
    def _get_cron_tolerance(self):
        """
        Calculare reminder tolerance based on cron interval

        Returns:
         * datetime, datetime
        """
        cron = self.env.ref("business_appointment.cron_reminder_alarm_task", False)
        tolerance = relativedelta(minutes=5)
        if cron: 
            tolerance = _intervalTypes[cron.interval_type](cron.interval_number)
        now = fields.Datetime.now()
        now_plus_tolerance = now + tolerance
        now_minus_tolerance = now - tolerance
        return now_plus_tolerance, now_minus_tolerance

    def action_mark_popup_done(self):
        """
        The method to mark this popup alarm done for this user
        In case it is done for all required users > unlink the task

        Methods:
         * _get_recipients

        Extra info:
         * Expected singleton
        """
        if self:
            partner_id = self.env.user.partner_id.id
            self = self.sudo()
            self.notified_partner_ids = [(4, partner_id)]
            partners, internal = self._get_recipients()      
            if self.notified_partner_ids == partners:
                self.unlink()
        return True

    @api.model
    def _nofity_popup_bus(self, partner_ids):
        """
        The method to notify user buses about changed popups
        
        Args:
         * partner_ids - list of involved partners

        Methods:
         * action_get_next_popup_notif
         * _sendmany of bus.bus

        Extra info:
         * we need to check rights for the sudden case responsible is not an appointment manager
        """
        notifications = []
        users = self.env["res.users"].search([("partner_id.id", "in", partner_ids)])
        for user in users:
            if user.has_group("business_appointment.group_ba_user"):
                popups = self.with_user(user).action_get_next_popup_notif()
                notifications.append([user.partner_id, "alarm.task", popups])
        if len(notifications) > 0:
            self.env["bus.bus"]._sendmany(notifications)
