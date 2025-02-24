#coding: utf-8

import logging

from dateutil.relativedelta import relativedelta
from pytz import timezone

from odoo import _, api, fields, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

FORBIDDENSYMBOLS = [':', '*', '?', '"', "'", '<', '>', '|', '+', '%', '!', '@', '\\', '/',]


class business_appointment(models.Model):
    """
    The model to manage appointment
    """
    _name = "business.appointment"
    _inherit = ["business.appointment.core", "rating.mixin"]
    _description = "Appointment"

    @api.depends("name")
    def _compute_safe_file_name(self):
        """
        Compute method for safe_file_name
        """
        for appointment in self:
            for symbol in FORBIDDENSYMBOLS:
                appointment.safe_file_name = appointment.name.replace(symbol, "-")

    @api.model
    def _state_selection(self):
        """
        The method to construct possible selection values

        Returns:
         * list of tuples
        """
        return [("reserved", _("Planned")), ("done", _("Done")), ("missed", _("Missed")), ("cancel", _("Canceled"))]

    name = fields.Char(string="Reference", readonly=True, tracking=1,)
    state = fields.Selection(
        _state_selection,
        string="Stage",
        required=True,
        default="reserved",
        tracking=2,
        index=True,
    )
    resource_type_id = fields.Many2one(index=True)
    partner_id = fields.Many2one(required=True)
    start_slot_datetime = fields.Datetime("Pre-Reservation Datetime")
    alarm_ids = fields.Many2many(
        "appointment.alarm",
        "appointment_alarm_business_appointment_rel_table",
        "appointment_alarm_id",
        "business_appointment_id",
        string="Alarms",
    )
    extra_product_ids = fields.One2many("associated.product.line", "appointment_id", string="Complementary Products")
    safe_file_name = fields.Char(string="Confimration File Name", compute=_compute_safe_file_name, store=True)
    extra_resource_ids = fields.Many2many(
        "business.resource",
        "business_resource_business_appoinment_extra_rel_table",
        "business_resource_rel_id",
        "business_appointment_rel_id",
        string="Extra Resources",
        help="The resources that are needed to provide this appointment service besides the main resource. Such \
resources, as well as the main resource, will be considered busy for this time period",
    )
    resource_color = fields.Integer(related="resource_id.color")
    videocall = fields.Char(string="Video call URL", copy=False)
    video_channel_id = fields.Many2one("mail.channel", string="Video channel", copy=False)
    prereservation_id = fields.Many2one("business.appointment.core", string="Origin", index=True)

    _order = "id desc"

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overwrite to check whether the time slot is not yet occupied

        Methods:
         * _ba_auto_subsribe
         * _apply_changes_to_alarms
         * _auto_generate_videocall
        """
        appointments = self.env["business.appointment"]
        for vals in vals_list:
            company_id = self.env["business.resource"].browse(vals.get("resource_id")).company_id
            if company_id:
                vals["name"] = self.env["ir.sequence"].with_context(company_id=company_id.id).next_by_code(
                    "business.appointment"
                )
            else:
                vals["name"] = self.env["ir.sequence"].next_by_code("business.appointment")            
            appointment = super(business_appointment, self).create(vals)
            if vals.get("alarm_ids"):
                appointment._apply_changes_to_alarms()
            appointment._ba_auto_subsribe(vals)
            appointments += appointment
        appointments.sudo()._auto_generate_videocall()
        return appointments

    def write(self, vals):
        """
        Overwrite to check whether the time slot is not yet occupied
         1. Update alarms 
         2. Clean alarm task if appointment is not topical

        Methods:
         * _check_busy_now_prereserv - to make sure we do not update slot crossing with another
         * _remove_outdated_alarms
         * _create_alarm_tasks
         * _ba_auto_subsribe
         * _send_rating_request
         * _apply_changes_to_alarms
         * _auto_generate_videocall
         * _clear_videocall
        """
        res = super(business_appointment, self).write(vals)
        for appointment in self:
            if (vals.get("state") == "reserved") or (not vals.get("state") and appointment.state == "reserved"):
                appointment._check_busy_now_prereserv()
            # 1 
            if vals.get("state") == "reserved" or vals.get("datetime_start") or vals.get("datetime_end") \
                    or vals.get("alarm_ids"):
                appointment._apply_changes_to_alarms()
                appointment.sudo()._auto_generate_videocall()
            # 2
            if vals.get("state") and vals.get("state") != "reserved":
                bus_partners = appointment._remove_outdated_alarms()           
                if bus_partners:
                    self.env["alarm.task"]._nofity_popup_bus(bus_partners.ids)
                appointment.sudo()._clear_videocall()
            if vals.get("state") == "done":
                appointment._send_rating_request()
        self._ba_auto_subsribe(vals)
        return res

    def unlink(self):
        """
        Re-write to unlink video calls if appointments are deleted
        """
        for appointment in self:
            appointment.sudo()._clear_videocall()
        return super(business_appointment, self).unlink()

    def name_get(self):
        """
        Overloading the method to make a name, since it doesn't have own
        """
        result = []
        for appointment in self:
            name = _("{} for {} by {}".format(
                appointment.name,
                appointment.resource_id.sudo().name,
                appointment.partner_id.sudo().name or appointment.sudo().contact_name,
            ))
            result.append((appointment.id, name))
        return result

    def _creation_subtype(self):
        """
        To track creation
        """
        return self.env.ref("business_appointment.mt_business_appointment_new")
    
    def _track_subtype(self, init_values):
        """
        Re-write to add custom events

        Extra info:
         * Expecteds singleton
        """
        if "state" in init_values:
            if self.state == "reserved":
                return self.sudo().env.ref("business_appointment.mt_business_appointment_new")
            if self.state == "cancel":
                return self.sudo().env.ref("business_appointment.mt_business_appointment_cancel")
        elif "datetime_start" in init_values or "datetime_end" in init_values or "resource_id" in init_values:
            return self.sudo().env.ref("business_appointment.mt_business_appointment_reserved_time_change")
        return super(business_appointment, self)._track_subtype(init_values)

    def _message_subscribe(self, partner_ids=None, subtype_ids=None, customer_ids=None):
        """
        Re-write to trigger bus on popups alarms if any

        Methods:
         * _nofity_popup_bus
        """
        res = super(business_appointment, self)._message_subscribe(
            partner_ids=partner_ids, subtype_ids=subtype_ids, customer_ids=customer_ids,
        )
        self.env["alarm.task"]._nofity_popup_bus(partner_ids)
        return res

    def message_unsubscribe(self, partner_ids=None, channel_ids=None):
        """
        Re-write to trigger bus on popups alarms if any

        Methods:
         * bus_all_alarms_update
        """
        res = super(business_appointment, self).message_unsubscribe(partner_ids=partner_ids)
        self.env["alarm.task"]._nofity_popup_bus(partner_ids)

    def _ba_auto_subsribe(self, vals):
        """
        The method to auto subsribe user and partner if not yet

        Methods:
         * message_subscribe
        """
        self = self.sudo()
        for appointment in self:
            partners = []
            if vals.get("resource_id"):
                company_ids = self._context.get("allowed_company_ids", [])
                resource_user = appointment.resource_id.user_id
                if company_ids:                    
                    user_company_ids = resource_user.company_ids.ids
                    if not any(cid not in user_company_ids for cid in company_ids):
                        partners.append(resource_user.partner_id.id)
                else:
                    partners.append(resource_user.partner_id.id)
            if vals.get("partner_id"):
                partners.append(appointment.partner_id.id)
            if appointment and partners:
                self.message_subscribe(partner_ids=partners)

    def action_cancel(self):
        """
        The method to change state to cancelled
        """
        self.write({"state": "cancel"})

    def action_mark_missed(self):
        """
        The method to change state to missed
        """
        self.write({"state": "missed"})

    def action_mark_done(self):
        """
        The method to change state to done
        """
        self.write({"state": "done"})

    def action_restore(self):
        """
        The method to change state to planned
        """
        self.write({"state": "reserved"})

    def action_generate_videocall(self):
        """
        The method to generate video URL

        Methods:
         * _generate_videocall        

        Extra info:
         * Expected singleton
        """
        self._generate_videocall()

    def action_clear_videocall(self):
        """
        The method to unlink video url
        
        Methods:
         * _clear_video_call

        Extra info:
         * Expected singleton
        """
        self._clear_videocall()

    @api.model
    def action_return_appointments_view(self, prereservation_ids):
        """
        The method to return appointments based on received prereservations

        Args:
         * prereservation_ids - list of ints

        Returns:
         * action dict
        """
        appointment_ids = self.search([("prereservation_id", "in", prereservation_ids)])
        res = False
        if len(appointment_ids) > 1:
            res = self.sudo().env.ref("business_appointment.business_appointment_action_tree_main").read()[0]
            res["domain"] = [("id", "in", appointment_ids.ids)]
        elif len(appointment_ids) == 1:
            res = self.sudo().env.ref("business_appointment.business_appointment_action_only_form").read()[0]
            res["res_id"] = appointment_ids.id
        return res

    def return_not_topical(self):
        """
        The method to return whether the appointment is still planned and in the future
        
        Returns:
         * bool - true if not topical, false - otherwise

        Extra info:
         * Expected sigleton
        """
        self = self.sudo()
        return self.state != "reserved" or self.datetime_end < fields.Datetime.now()

    def return_scheduled_time_tz(self, in_user_tz=False):
        """
        The method to return scheduled period with tz

        Args:
         * in_user_tz - whether this appointment partner time should be used

        Methods:
         * _return_dt_format

        Returns:
         * char

        Extra info:
         * we have the param in_user_tz to be used for emails to avoid the sender tz appleid
         * Expected singleton

        To-do:
         * Re-consider and optimize
        """
        def ba_time_localize(c_datetime, c_tz, c_checkout_time=0.0):
            """
            The method to format UTC datatime to a new timezone

            Args:
             * c_datetime - string (in datetime format)
             * c_tz - timezone object
             * c_checkout_time - float
            """
            n_datetime = fields.Datetime.from_string(c_datetime)
            if c_checkout_time:
                n_datetime = n_datetime-relativedelta(minutes=c_checkout_time*60)
            return timezone("UTC").localize(n_datetime).astimezone(c_tz)

        diff_tz = self.env.company.ba_timezone_option
        checkout_time = self.service_id.sudo().checkout_time
        if diff_tz:
            if in_user_tz:
                tz_name = self.tz or self.partner_id.tz or self._context.get("tz") or "UTC"
            else:
                tz_name = self.env.user.partner_id.tz or self._context.get("tz") or "UTC"
        else:
            if in_user_tz:
                tz_name = self._context.get("user_tz") or self.sudo().company_id.partner_id.tz \
                    or self._context.get("tz") or self.env.user.sudo().company_id.partner_id.tz or "UTC"
            else:
                tz_name = self.env.user.sudo().company_id.partner_id.tz or self._context.get("tz") or "UTC"
        tz = timezone(tz_name)
        datetime_start = ba_time_localize(self.datetime_start, tz)
        datetime_end = ba_time_localize(self.datetime_end, tz, checkout_time)   
        result = u"{} {}".format(self._return_dt_format(datetime_start.date()), datetime_start.strftime("%I:%M %p"))
        if datetime_start.date() != datetime_end.date():
            result = u"{} - {} {}".format(
                result, self._return_dt_format(datetime_end.date()), datetime_end.strftime("%I:%M %p")
            )
        else:
            result = u"{} - {}".format(result, datetime_end.strftime("%I:%M %p"))
        # result = u"{} ({})".format(result, tz_name)
        result = u"{}".format(result)
        return result

    @api.model
    def _return_dt_format(self, target_date):
        """
        The method to format date according to the lang

        Agrs:
         * datetime.date

        Methods:
         * _return_lang_date_format of business.resource

        Returns: 
         * char
        """
        lang_date_format = self.env["business.resource"]._return_lang_date_format()
        return target_date.strftime(lang_date_format)

    def _send_success_email(self, reshedule=False):
        """
        The method to render success email for appointments

        Args:
         * reshedule - if success relate to re-secheduling

        Methods:
         * _render_template_qweb & _render_template of mail.template (and sms.template)
         * _prepare_confirmation_report
         * build_email of ir.mail.server
         * send_email of ir.mail.server
        
        Extra info:
         * backend success might be linked to various resource types. We send email by each of that
        """
        def _send_confirmation_by_appointments(main_appointment, main_template, main_template_ctx, voucher_needed):
            """
            The method to send email based on appointment, template and predefined context

            Args:
             * main_appointment - business.appointment object
             * main_template - mail.template object
             * main_template_ctx - dict of values
             * voucher_needed - whether success voucher should be attached
            """
            body_html = main_template.with_context(main_template_ctx)._render_template_qweb(
                main_template.body_html, "business.appointment", [main_appointment.id],
            ).get(main_appointment.id)
            subject = main_template.with_context(main_template_ctx)._render_template(
                main_template.subject, "business.appointment", [main_appointment.id],
            ).get(main_appointment.id)
            attachments = []
            if voucher_needed:
                for single_appointment in this_resource_appointments:
                    pdf_content = single_appointment._prepare_confirmation_report()
                    attachments.append((single_appointment.safe_file_name + ".pdf", pdf_content, "application/pdf"))
            mail_server = self.env["ir.mail_server"]
            try:
                receivers_emails = [main_appointment.partner_id.email]
                if resource_id and resource_id.sucess_email_partner_ids:
                    receivers_emails += resource_id.sucess_email_partner_ids.mapped("email")
                for receiver in receivers_emails:
                    message = mail_server.build_email(
                        email_from=self.env.company.partner_id.email or self.env.user.company_id.partner_id.email,
                        subject=subject,
                        body=body_html,
                        subtype="html",
                        email_to=[receiver],
                        attachments=attachments,
                    )
                    mail_server.send_email(message)
            except Exception as e:
                _logger.error("Success email is not sent {}".format(e))      

        if self:
            lang = self[0].partner_id.lang or self._context.get("lang") or self.env.user.lang
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            template_ctx = self._context.copy()
            template_ctx.update({
                "lang": lang, "base_url": base_url, "reshedule": reshedule,
            })
            website_needed = hasattr(self[0], "website_id")
            templ_key = "business_appointment.email_template_successful_appointment_multi"
            default_template = self.with_context(lang=lang).env.ref(templ_key, False)
            resources = self.mapped("resource_id")
            for resource_id in resources:
                rtype = resource_id.resource_type_id
                template = rtype.with_context(lang=lang).success_mail_template_id or default_template
                voucher_needed = not rtype.no_report_on_success
                if not template:
                     _logger.error("Success email is not sent since no template is found".format(e))
                else:
                    this_resource_appointments = self.filtered(lambda appoi: appoi.resource_id == resource_id) 
                    main_appointment = this_resource_appointments[0]                  
                    website_http_domain = website_needed and main_appointment.website_id \
                        and main_appointment.website_id.domain or base_url  
                    company_id = main_appointment.company_id
                    if not company_id:
                        company_id = website_needed and main_appointment.website_id.company_id \
                            or self.env.company or self.env.user.company_id

                    template_ctx.update({
                        "appointments": this_resource_appointments,
                        "website_http_domain": website_http_domain,
                        "target_company": company_id,
                    })     
                    _send_confirmation_by_appointments(
                        main_appointment=main_appointment, 
                        main_template=template, 
                        main_template_ctx=template_ctx,
                        voucher_needed=voucher_needed,
                    )

    def _get_template_ctx(self, lang=None):
        """
        The method to prepare context for generated email templates

        Args:
         * lang - char - code of recipient language

        Returns:
         * context dict
        
        Extra info:
         * Expected singleton
        """
        lang = lang or self._context.get("lang") or self.env.user.lang
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        website_needed = hasattr(self[0], "website_id")
        website_http_domain = website_needed and self.website_id and self.website_id.domain or base_url  
        company_id = self.company_id
        if not company_id:
            company_id = website_needed and self.website_id.company_id or self.env.company or self.env.user.company_id
        template_ctx = self._context.copy()    
        template_ctx.update({
            "lang": lang,
            "base_url": base_url,
            "website_http_domain": website_http_domain,
            "target_company": company_id,
        })
        return template_ctx

    def _apply_changes_to_alarms(self):
        """
        The method to update alarms

        Methods:
         * _remove_outdated_alarms
         * _create_alarm_tasks
        """
        for appointment in self:
            bus_partners = appointment._remove_outdated_alarms()
            appointment._create_alarm_tasks(bus_partners)

    def _remove_outdated_alarms(self):
        """
        The method to remove all previous alarms

        Methods:
         * _get_recipients of task.alarm

        Returns:
         * bus_partners - res.partner recordset

        Extra info:
         * Expected singleton
        """
        self = self.sudo()
        existing_alarm_ids = self.env["alarm.task"].search([("appointment_id", "=", self.id)])
        now_plus = fields.Datetime.now() + relativedelta(days=1)
        bus_alarms = existing_alarm_ids.filtered(
            lambda task: task.alarm_id.ttype == "popup" and (not task.alarm_time or task.alarm_time <= now_plus)
        )
        bus_partners = self.env["res.partner"]
        for bus_alarm in bus_alarms:
            partners, internal = bus_alarm._get_recipients()
            bus_partners += partners            
        existing_alarm_ids.unlink()
        return bus_partners

    def _create_alarm_tasks(self, bus_partners=False):
        """
        The method to update alarms
        The goal is to prepare alarm tasks and remove outdated ones

        Args:
         * bus_partners - res.partner recordset

        Methods:
         * return_not_topical
         * _get_recipients of alarm.task
            
        Extra info:
         * Expected singleton
        """
        self = self.sudo()
        now = fields.Datetime.now()
        now_plus = now + relativedelta(days=1)
        if not self.return_not_topical():
            bus_partners = bus_partners and bus_partners or self.env["res.partner"]
            for alarm in self.alarm_ids:
                task_id = self.env["alarm.task"].create({
                    "appointment_id": self.id,
                    "alarm_id": alarm.id,
                })
                alarm_time = task_id.alarm_time
                if not alarm_time or alarm_time < now:
                    task_id.unlink()
                elif alarm.ttype == "popup" and alarm_time <= now_plus:
                    partners, internal = task_id._get_recipients()
                    bus_partners += partners
            if bus_partners:
                self.env["alarm.task"]._nofity_popup_bus(bus_partners.ids)

    def _prepare_confirmation_report(self):
        """
        The method to prepare confirmation report

        Methods:
         * _render_qweb_pdf of report

        Returns:
         * binary

        Extra info:
         * Expected singleon    
        """
        pdf_content, mimetype = self.with_context(lang=self.env.user.lang).env["ir.actions.report"]._render_qweb_pdf(
            "business_appointment.action_report_business_appointment", [self.id], {}
        )       
        return pdf_content

    def _send_rating_request(self):
        """
        The method to send rating request

        Methods:
         * rating_send_request of rating.mixin
        """
        for appointment in self:
            if appointment.resource_type_id.rating_option and appointment.partner_id:
                template = appointment.resource_type_id.rating_mail_template_id \
                   or self.sudo().env.ref("business_appointment.email_template_rating_appointment")
                if template:
                    try:
                        appointment.rating_send_request(
                            template=template, lang=appointment.partner_id.lang, force_send=True,
                        )
                    except Exception as e:
                        _logger.error("Rating request has not been sent {}".format(e))

    def rating_apply(self, rate, token=None, rating=None, feedback=None, subtype_xmlid=None, notify_delay_send=False):
        """
        Re-write to apply directly subtype_xmlid
        """
        return super(business_appointment, self).rating_apply(
            rate, token=token, rating=rating, feedback=feedback,
            subtype_xmlid="business_appointment.mt_appointment_rating", notify_delay_send=notify_delay_send,
        )

    def _rating_get_parent_field_name(self):
        """
        Define parent as a related business.resource.type
        """
        return "resource_type_id"

    def _auto_generate_videocall(self):
        """
        The method to hceck whether video call should be auto created and trigger its creation if necessary
        
        Methods:
         * _generate_videocall
        
        To-do:
         * the unreal condition is added until https://github.com/odoo/odoo/issues/100464 is fixed
        """
        if 1 == 0 and self.env.user.has_group("business_appointment.group_business_appointment_video_calls"):
            for appointment in self:
                if appointment.resource_type_id.video_call_option:
                    self._generate_videocall()

    def _generate_videocall(self):
        """
        The method to generate a new videocall
        """
        for appointment in self:
            partners_to = []
            user_id = self.env.user
            if appointment.user_id:
                user_id = appointment.user_id
                partners_to.append(user_id.partner_id.id)
            if appointment.partner_id:
                partners_to.append(appointment.partner_id.id)
            channel_info = self.env["mail.channel"].with_user(user_id).create_group(
                partners_to=partners_to,
                default_display_mode="video_full_screen",
            )
            channel_id = self.env["mail.channel"].browse(channel_info.get("id"))
            channel_id.write({"name": appointment.name, "description": appointment.service_id.name})
            appointment.write({
                "videocall": f"{self.get_base_url()}/chat/{channel_id.id}/{channel_info.get('uuid')}",
                "video_channel_id": channel_id.id,
            })

    def _clear_videocall(self):
        """
        The method to remove appointment video call and delete linked mail.channel
        """
        for appointment in self:
            appointment.videocall = False
            if appointment.video_channel_id:
                appointment.video_channel_id.sudo().unlink()
