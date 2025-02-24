#coding: utf-8

import logging

from dateutil.relativedelta import relativedelta
from random import randint

from odoo import _, fields, models

from odoo.tools import email_normalize
from odoo.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)


class website_business_appointment(models.Model):
    """
    The model to keep settings of current (session) appointment
    """
    _name = "website.business.appointment"
    _inherit = "appointment.contact.info"
    _description = "Website Business Appointment"
    _rec_name = "partner_id" 

    def _compute_prereservation_timer(self):
        """
        Compute method for prereservation_timer

        Special values:
         * "0" - no need for timer (step doesn't assume timer)
         * "-1" - if reservation is just expired (it is 0, but this value is reserved for the point above)

        Extra info:
         * minus 2 seconds: to compensate possible js slowdonwons (to show user pessimistic estimation)
        """
        ICPSudo = self.env["ir.config_parameter"].sudo()
        for record in self:
            prereservation_time = 0
            url_reservation_ids = record.url_reservation_ids.filtered(lambda reserv: reserv.state != "processed")
            if url_reservation_ids:
                progress_step = record.progress_step
                if progress_step >= 6:
                    approval_type = str(ICPSudo.get_param("ba_approval_type", default="no"))
                    if approval_type != "no":
                        to_compare_date = min(url_reservation_ids.mapped("schedule_datetime"))
                        confirmation = float(ICPSudo.get_param("ba_max_approval_time", default="2.0"))
                        prereservation_time = (to_compare_date + relativedelta(hours=confirmation) \
                           - fields.Datetime.now()).total_seconds() or -1
                else:
                    to_compare_date = min(url_reservation_ids.mapped("create_date"))
                    preresrvation = float(ICPSudo.get_param("ba_max_preresevation_time", default="0.5"))
                    prereservation_time = (to_compare_date + relativedelta(hours=preresrvation) \
                       -  fields.Datetime.now()).total_seconds() or -1
            record.prereservation_timer = prereservation_time != 0 and int(prereservation_time) -2 or 0

    url_ba_type_id = fields.Many2one("business.resource.type", string="Resource Type")
    all2choose_rtype_ids = fields.Many2many(
        "business.resource.type",
        "website_ba_brt_all_rel_table",
        "business_resource_id",
        "website_business_appointment_id",
        string="All Resources",
    )
    url_resource_ids = fields.Many2many(
        "business.resource",
        "website_ba_br_rel_table",
        "business_resource_id",
        "website_business_appointment_id",
        string="Resources",
    )
    url_service_id = fields.Many2one("appointment.product", string="Service")
    url_reservation_ids = fields.Many2many(
        "business.appointment.core",
        "website_ba_bac_rel_table",
        "business_appointment_core_id",
        "website_business_appointment_id",
        string="Pre-reservations",
    )
    resechedule_id = fields.Many2one("business.appointment", string="Re-Scheduled Appointment")
    progress_step = fields.Integer(string="Progress Step", default=1)
    active_step = fields.Integer(string="Active Step", default=1)
    partner_id = fields.Many2one("res.partner", string="Partner", default=lambda self: self.env.user.partner_id)
    public_partner_id = fields.Many2one("res.partner", string="Public Partner")
    website_id = fields.Many2one("website", string="Website")
    error = fields.Char()
    error_message = fields.Char()
    error_vals = fields.Char()
    prereservation_timer = fields.Integer(compute=_compute_prereservation_timer, compute_sudo=True)
    confirmation_code = fields.Char(string="Confirmation Code",)
    confirmation_attempts = fields.Integer(string="Confirmation Attempts", default=0)
    confirmation_retrial_time = fields.Datetime(string="Confirmation Re-Trial Time")
    confirmation_refresh_attempts = fields.Integer(string="Code Refreshing Done", default=0)
    resource_type_id = fields.Many2many(
        "business.resource.type",
        "business_resource_type_website_business_appointment_rel_table",
        "business_resource_type_id",
        "website_business_appointment_id",
        string="Chosen resource types",
    )

    def _check_and_adapt_session_order(
        self, website_id, active_step, url_ba_type_id, url_resource_ids, url_service_id, progress_step
    ):
        """
        The method to check all vals, session params and based on those adapt website.business.appointment and
        reservations

        Args:
         * website_id - website object
         * active_step - int
         * url_ba_type_id - int - business.resource.type ID
         * url_resource_ids - str - represents list of business.resource.object ids [1,2]
         * url_service_id - int - business.resource ID
         * progress_step - int  

        Methods:
         * return_not_topical
         * _return_viable_resources of business.resource.type
         * _return_viable_services of busienss.resource
         * _calculate_hidden_steps
         * _check_expired_reservations
         * _reroute_hidden_steps
         * action_cancel_prereserv of business.appointment.core
         * _caclulate_expiration_timer

        Returns:
         * dict of session values

        Extra info:
         * When we check viable resources, we may also think of still viable services and reservations. However,
           it would significantly increase code complexity and migth be resource-demanding. So, we just remove
           such service and reservations   
         * In case a single reversation is cancelled we cancel all of those
         * Do not remove logger.debug: beside debugging it is used to make sure records exist and user has enough rights
         * Expected singleton
        """
        self = self.sudo()
        self.ensure_one()
        if self.resechedule_id and self.resechedule_id.return_not_topical():
            self.resechedule_id = False
        try:
            resource_type_id = self.url_ba_type_id
            resource_ids = self.url_resource_ids
            service_id = self.url_service_id
            if url_ba_type_id:
                resource_type_id = self.env["business.resource.type"].browse(int(url_ba_type_id))
                resource_ids = False
                service_id = False           
            if url_resource_ids:
                resource_ids = self.env["business.resource"].browse(list(set(safe_eval(url_resource_ids))))
                service_id = False
            if url_service_id:
                service_id = self.env["appointment.product"].browse(int(url_service_id))                          
            _logger.debug("Appointment session info: {}, {}, {}".format(
                resource_type_id and resource_type_id.name or False, 
                resource_ids and [resource.name for resource in resource_ids] or False, 
                service_id and service_id.name or False,
            ))
            active_step = active_step and int(active_step) or self.active_step
            progress_step = progress_step and int(progress_step) or self.progress_step
        except Exception as error:
            _logger.warning("Business appointment url params are broken: {}".format(error))
            return None

        hidden_steps, types_all, resources_all, service_all = self._calculate_hidden_steps(
            website_id, resource_type_id, resource_ids,
        )
        session_values = {
            "all2choose_rtype_ids": types_all and [(6, 0, types_all.ids)] or [(6, 0, [])],
            "url_ba_type_id": False,
            "url_resource_ids": [(6, 0, [])],
            "url_service_id": False,
            "url_reservation_ids": [(6, 0, [])],
        }
        to_cancel_reservations = self.sudo().url_reservation_ids
        if types_all and resource_type_id and (resource_type_id in types_all) and progress_step >= 1:
            session_values.update({"url_ba_type_id": resource_type_id.id,})
            if resources_all and resource_ids and (resource_ids & resources_all == resource_ids) and progress_step >= 2:
                session_values.update({"url_resource_ids": [(6, 0, resource_ids.ids)],})
                if service_all and service_id and (service_id in service_all) and progress_step >= 3:
                    session_values.update({"url_service_id": service_id.id,})                   
                    if progress_step >= 4:
                        url_reservation_ids, to_cancel_reservations, four_step = self._check_reservations(
                            resource_ids, service_id
                        )
                        if url_reservation_ids.sudo():
                            session_values.update({"url_reservation_ids": [(6, 0, url_reservation_ids.sudo().ids)],})
                        if four_step:
                            progress_step = progress_step <= 4 and progress_step or 4
                else:
                    progress_step = progress_step <= 3 and progress_step or 3
            else:
                progress_step = progress_step <= 2 and progress_step or 2 
        else:
            progress_step = progress_step <= 1 and progress_step or 1 

        active_step = active_step <= progress_step and active_step or progress_step 
        reroute_values = self._reroute_hidden_steps(active_step, hidden_steps, types_all, resources_all, service_all)
        if reroute_values:
            session_values.update(reroute_values)
        else:            
            session_values.update({
                "active_step": active_step, "progress_step": progress_step,
            })
        self.sudo().write(session_values)
        if to_cancel_reservations.sudo():
            to_cancel_reservations.sudo().action_cancel_prereserv()
        resend_timer = active_step == 6 and self._caclulate_expiration_timer() or 0
        res_values = {
            "hidden_steps": hidden_steps,
            "default_url": "/appointments/{}".format(self.active_step),
            "progress_step": self.progress_step,
            "active_step": self.active_step,
            "url_ba_type_id": self.url_ba_type_id,
            "url_resource_ids": self.url_resource_ids,
            "url_service_id": self.url_service_id,
            "resend_timer": resend_timer,
            "confirmation_refresh_attempts": self.confirmation_refresh_attempts,
            "prereservation_timer": self.sudo().prereservation_timer,
            "resechedule_id": self.resechedule_id,
        }
        return res_values
           
    def _calculate_hidden_steps(self, website_id, url_ba_type_id, url_resource_ids):
        """
        The method to clear out which steps are or should be missed since there is no choice
         1. If there are no viable resource types, progressbar is always hidden
         2. We hide the step 1 if all (!) viable resource types count equals 1   
         3. If no resource types is chosen, we restrict possible resources by viable types (not by chosen types)
            We also make sure that currently chosne resource type is fine
         4. We hide the step 2 if all (!) viable resources by viable types count equals 1 (not by chosen resources)
         5. We also hide step 2, if all chosen / viable resource types are automatic or have a single resource
         6. If no resources are chosen, we get viable resources by all chosen / viable resource types  
         7. We hide step 3, if number of services resulted from all (!) chosen / viable resources is one. We check all,
            since multi resources selection is possible 
         8. We hide step 6 if confirmation is not required   
        
        Args:
         * website_id - website object
         * url_ba_type_id - business.resource.type object
         * url_resource_ids - business.resource recordset

        Methods:
         * _return_viable_resources of business.resource.type
         * _return_viable_services of busienss.resource

        Returns:
         * hidden_steps - list of ints
         * types_all - business.resource.type recordset
         * resources_all - business.resource recordset
         * service_all - appointment.product recordset

        Extra info:
         * Expected singleton
        """
        self = self.sudo()
        self.ensure_one()
        hidden_steps = []
        # 1
        types_all = self.env["business.resource.type"].search([
            ("website_published", "=", True), ("website_id", "in", (False, website_id.id)),
        ])
        if types_all:
            types_all = types_all.filtered(lambda rtype: rtype._return_viable_resources(website_id))
        if not types_all:
            # 1
            hidden_steps, types_all, resources_all, service_all = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], False, False, False
        else:
            # 2
            if len(types_all) == 1:
                hidden_steps.append(1)
            # 3
            resource_type_ids = (url_ba_type_id and url_ba_type_id in types_all) and url_ba_type_id or types_all
            resources_all = resource_type_ids._return_viable_resources(website_id)
            if len(resources_all) == 1:
                # 4
                hidden_steps.append(2)
            else: 
                # 5  
                manual_type_ids = resource_type_ids.filtered(lambda rtype: rtype.allocation_type == "manual" \
                    and len(rtype._return_viable_resources(website_id)) > 1)
                if not manual_type_ids:
                    hidden_steps.append(2)
            # 6
            resource_ids = url_resource_ids or resources_all
            # 7
            service_all = resource_ids._return_viable_services(website_id)
            if len (service_all) == 1:
                hidden_steps.append(3)
            # 8 
            ICPSudo = self.env["ir.config_parameter"].sudo()
            approval_type = str(ICPSudo.get_param("ba_approval_type", default="no"))
            if approval_type == "no":
                hidden_steps.append(6)
        return hidden_steps, types_all, resources_all, service_all

    def _reroute_hidden_steps(self, active_step, hidden_steps, types_all, resources_all, service_all):
        """
        The method to make sure all chosen params lead to viable choice

        Args:
         * active_step - int
         * hidden_steps - list of int
         * types_all - business.resource.type recordset
         * resources_all - business.resource recordset
         * service_all - appointment.product recordset

        Returns:
         * dict of values

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        session_values = {}
        if active_step == 1 and 1 in hidden_steps:
            active_step = 2
            session_values.update({
                "active_step": 2,
                "progress_step": 2,
                "url_ba_type_id": types_all and types_all[0].id or False,
            })
        if active_step == 2 and 2 in hidden_steps:
            active_step = 3
            session_values.update({
                "active_step": 3,
                "progress_step": 3,
                "url_resource_ids": resources_all and [(6, 0, resources_all.ids)] or [(6, 0, [])],
            })        
        if active_step == 3 and 3 in hidden_steps:
            active_step = 4
            session_values.update({
                "active_step": 4,
                "progress_step": 4,
                "url_service_id": service_all and service_all[0].id or False,
            })           
        return session_values

    def _check_reservations(self, resource_ids, service_id):
        """
        The method to check reservations for beeing expired and whether preious params suit

        Args:
         * resource_ids - business.resource recordset
         * service_id - appointment.product object

        Methods:
         * _check_expired of business.appointment.core

        Returns:
         * business.appointment.core recordset
         * business.appointment.core recordset
         * bool

        Extra info:
         * Expected singleton
        """
        self = self.sudo()
        reservation_ob = self.env["business.appointment.core"]
        url_reservation_ids = self.url_reservation_ids
        to_cancel_reservations = reservation_ob
        four_step = False
        if url_reservation_ids:
            to_cancel_reservations = reservation_ob._check_expired(url_reservation_ids.ids)
            to_cancel_reservations += url_reservation_ids.filtered(
                lambda core: core.resource_id not in resource_ids or core.service_id != service_id
            )
            if to_cancel_reservations:
                four_step = True
                url_reservation_ids = reservation_ob
        else:
            four_step = True
        return url_reservation_ids, to_cancel_reservations, four_step

    def _return_contact_info(self):
        """
        The method to prepare values for input form

        Methods:
         * _return_input_values - inherited from appointment.contact.info
         * _return_appointment_values - inherited from appointment.contact.info

        Returns:
         * dict

        Extra info:
         * Expected singleton 
        """
        values = self._return_partner_values()
        values.update(self._return_appointment_values(pure_values=False, tosession=True))
        return values

    def _update_session_contact_details(self, values, prereserv=False):
        """
        The method to update session values and related reservations
        
        Args:
         * values - dict
         * prereserv - bool whether to make reservations need for approval

        Methods:
         * _return_partner_values
         * action_start_prereserv of business.appointment.core
         * _update_confirmation_code

        Extra info:
         * Expected singleton
        """
        self = self.sudo()
        self.write(values)
        url_reservation_ids = self.url_reservation_ids
        for not_reserv_val in ["error", "error_message", "error_vals"]:
            if values.get(not_reserv_val) is not None:
                del values[not_reserv_val]
        url_reservation_ids.write(values)           
        if self.partner_id:
            partner_values = self._return_partner_values(True)
            self.partner_id.write(partner_values)
        if prereserv:
            url_reservation_ids.action_start_prereserv() 
            res = self._update_confirmation_code()     

    def _update_session_confirmation(self, values=None, confirmed=False):
        """
        The method to update session values and related reservations
        
        Args:
         * values - dict
         * confirmed - bool whether to make reservations approved

        Methods:
         * _confirm_prereserv of business.appointment.core
         * action_cancel of business.appointment
         * action_cancel_prereserv of business.appointment.core
        
        Returns:
         * appointment_ids - business.appointment recordset or False
         * error_internal - char or False

        Extra info:
         * We require rollbacks to avoid duplicated users or too early confirmation. Otherwise, try/except would
           create certain data partically
         * Expected singleton 
        """
        self = self.sudo()
        if values:
            self.write(values)        
        appointment_ids = False
        error_internal = False
        if confirmed:
            try:
                appointment_ids = self.url_reservation_ids._confirm_prereserv(self.resechedule_id)
                if appointment_ids:
                    self.public_partner_id = appointment_ids[0].partner_id
            except Exception as error:
                _logger.error("Appointment is not confirmed {}".format(error))
                self.write({"error": {"misc": "error"}, "error_message": [str(error)]}) 
                error_internal = True
        else:
            ICPSudo = self.env["ir.config_parameter"].sudo()
            max_total_attempts = int(ICPSudo.get_param("ba_max_approval_trials", default="5"))
            total_attempts = self.confirmation_attempts + 1
            left_attempts = max_total_attempts - total_attempts
            if left_attempts <= 0:
                self.url_reservation_ids.action_cancel_prereserv()
                self.unlink()
            else:
                self.confirmation_attempts = total_attempts
                if left_attempts <= 2:
                    self.error_message = values.get("error_message") \
                        + [_("You have {} attempt(s) to insert the correct code".format(left_attempts))]
        return appointment_ids, error_internal
   
    def _update_confirmation_code(self):
        """
        The method to generate new generation code and send email
        """
        ICPSudo = self.env["ir.config_parameter"].sudo()
        approval_type = str(ICPSudo.get_param("ba_approval_type", default="no"))
        if approval_type != "no":
            for record in self:
                record.confirmation_code = "".join(["{}".format(randint(0, 9)) for num in range(0, 4)])
                ba_confirmation_retry_period = int(ICPSudo.get_param("ba_confirmation_retry_period", default="60"))
                ba_confirmation_retry_trials = int(ICPSudo.get_param("ba_confirmation_retry_trials", default="3"))
                record.confirmation_retrial_time = fields.Datetime.now() \
                    + relativedelta(seconds=ba_confirmation_retry_period)
                record.confirmation_refresh_attempts = record.confirmation_refresh_attempts + 1
                if record.confirmation_refresh_attempts > ba_confirmation_retry_trials:
                    record.confirmation_refresh_attempts = - 1
                record.sudo()._prepare_and_send_confirmation(approval_type)

    def _prepare_and_send_confirmation(self, approval_type):
        """
        The method to render template and send email/sms with confirmation code

        Args:
         * approval_type - char

        Methods:
         * _render_template of mail.template (and sms.template)
         * _send_sms of sms.api
         * build_email of ir.mail.server
         * send_email of ir.mail.server

        Extra info:
         * In case sms are not available but should be >> use email confirmation
         * Expected singleton
        """
        lang = self.partner_id.lang or self._context.get("lang") or self.env.user.lang
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        website_http_domain = self.website_id.domain or base_url
        template_ctx = self._context.copy()
        template_ctx.update({
            "lang": lang, "base_url": base_url, "website_http_domain": website_http_domain,
        })
        if approval_type == "sms":
            template = self.sudo().with_context(lang=lang).env.ref(
                "business_appointment_website.sms_template_ba_confirmation_code", False,
            )
            if template:
                body_html = template.with_context(template_ctx)._render_template(
                    template.body, "website.business.appointment", [self.id],
                ).get(self.id)     
                mobile = self.partner_id and self.partner_id.mobile or self.mobile
                if mobile:
                    try:
                        self.env["sms.api"]._send_sms([mobile], body_html)
                    except Exception as e:
                        _logger.error("Confirmation SMS is not sent {}".format(e))
                        approval_type = "email"
                else:
                    _logger.error("No mobile or phone are defined to send confirmation sms")
                    approval_type = "email"                    
        if approval_type == "email":
            template = self.sudo().with_context(lang=lang).env.ref(
                "business_appointment_website.email_template_confirmation_code", False,
            )
            if template:
                body_html = template.with_context(template_ctx)._render_template_qweb(
                    template.body_html, "website.business.appointment", [self.id],
                ).get(self.id)        
                subject = _("{}: Confirmation Code").format(self.website_id.company_id.name)
                mail_server = self.env["ir.mail_server"]
                try:
                    message = mail_server.build_email(
                        email_from=self.env.company.partner_id.email, subject=subject, body=body_html,
                        subtype="html", email_to=[self.partner_id.email or self.email],
                    )
                    mail_server.send_email(message)
                except Exception as e:
                    _logger.error("Confirmation Email is not sent {}".format(e))

    def _caclulate_expiration_timer(self):
        """
        The method to calculate confirmation resend timer

        Return:
         * int - number of seconds
        
        Extra info:
         * Expceted singleton
        """
        expiration_timer = 0
        if self.confirmation_retrial_time and self.confirmation_retrial_time > fields.Datetime.now():
            expiration_timer = (self.confirmation_retrial_time - fields.Datetime.now()).total_seconds()
        return int(expiration_timer)

    def return_prereservation_timer(self):
        """
        The method to return pre-reservation timer (used when slots are re-calced in js)
        IMPORTANT: if we are after time slots selection, and in case of time slots changes we also should move back 
        to the stage "Choose time", since new slots are added / old ones are cancelled

        Returns:
         * int

        Extra info:
         * Expected singleton
        """
        self = self.sudo()
        prereservation_timer = False
        if self.progress_step > 4:
            self.progress_step = 4
            self.url_reservation_ids.write({"state": "draft"})
        else:
            prereservation_timer = self.prereservation_timer
        return prereservation_timer

    def _create_portal_user(self, company_id=False):
        """
        The method to create user for the partner

        Args:
         * company_id - res.company object

        Methods:
         * signup_prepare of res.partner
         * _create_user_from_template of res.users

        Returns:
         * str (singup url or False)

        Extra info:
         * Expected singleton
        """
        self = self.sudo()
        res = False
        partner_id = self.public_partner_id
        if partner_id:
            user_vals = {
                "email": email_normalize(partner_id.email),
                "login": email_normalize(partner_id.email),
                "partner_id": partner_id.id,
                "company_id": company_id.id,
                "company_ids": [(6, 0, [company_id.id])],
            }           
            try:
                new_user = self.env["res.users"].with_context(no_reset_password=True)._create_user_from_template(
                    user_vals
                )
                lang = self._context.get("lang") or self.env.user.lang
                signup_ctx = {"signup_force_type_in_url": "", "lang": lang}
                partner_id.signup_prepare()
                res = partner_id.signup_url
                self._send_invitation_email(res)
            except Exception as e:
                _logger.error("User is not created. Reason: {}".format(e))
        return res

    def _send_invitation_email(self, token_url):
        """
        The method to invite portal user 

        Args:
         * token_url - char - url to finish regisration

        Methods:
         * _render_template of mail.template
         * build_email of ir.mail.server
         * send_email of ir.mail.server
        """
        lang = self.partner_id.lang or self._context.get("lang") or self.env.user.lang
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        website_http_domain = self.website_id.domain or base_url
        template_ctx = self._context.copy()
        template_ctx.update({
            "lang": lang, "base_url": base_url, "website_http_domain": website_http_domain, "token_url": token_url,
        })
        template = self.sudo().with_context(lang=lang).env.ref(
            "business_appointment_website.email_ba_public_invitation", False,
        )
        if template:
            body_html = template.with_context(template_ctx)._render_template_qweb(
                template.body_html, "website.business.appointment", [self.id],
            ).get(self.id)        
            subject = _("{}: Invitation").format(self.website_id.company_id.name)
            mail_server = self.env["ir.mail_server"]
            try:
                message = mail_server.build_email(
                    email_from=self.env.company.partner_id.email, subject=subject, body=body_html,
                    subtype="html", email_to=[self.partner_id.email or self.email],
                )
                mail_server.send_email(message)
            except Exception as e:
                _logger.error("The invitation email is not sent: {}".format(e))
