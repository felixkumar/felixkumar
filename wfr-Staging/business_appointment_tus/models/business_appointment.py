#coding: utf-8

import logging
from odoo import _, api, fields, models
_logger = logging.getLogger(__name__)


class business_appointment(models.Model):
    """
    The model to manage appointment
    """
    _inherit = "business.appointment"
    _description = "Appointment"

    def write(self, vals):
        res = super(business_appointment, self).write(vals)
        for appointment in self:
            appointment.x_oz_cbaf_3.update({"pickup_schedule_date": appointment.datetime_start,
                                            "outbound_stage_id": self.env.ref('mc_freight_app.scheduled_outbound').id,
                                            "stage_id": self.env.ref('mc_freight_app.freight_quote').id,
                                            })
        return res

    @api.model
    def create(self, vals):
        """
        Write pickup schedule date in freight record
        """
        res = super(business_appointment, self).create(vals)
        freight_id = self.env["freight.freight"].browse(vals.get("x_oz_cbaf_3"))
        if freight_id:
            freight_id.pickup_schedule_date = vals.get('datetime_start')
            freight_id.outbound_stage_id = self.env.ref('mc_freight_app.scheduled_outbound').id
            freight_id.stage_id = self.env.ref('mc_freight_app.freight_quote').id
        return res

    def name_get(self):
        result = []
        for appointment in self:
            if appointment.x_oz_cbaf_3:
                result.append(
                    (appointment.id, appointment.sudo().x_oz_cbaf_3 and appointment.sudo().x_oz_cbaf_3.name or ""))
            else:
                name = _(u"{} for {} by {}".format(appointment.name, appointment.resource_id.sudo().name,
                                                   appointment.partner_id.sudo().name or appointment.sudo().contact_name, ))
                result.append((appointment.id, name))
        return result

    # def _send_success_email(self, reshedule=False):
    #     """
    #     The method to render success email for appointments
    #
    #     Args:
    #      * reshedule - if success relate to re-secheduling
    #
    #     Methods:
    #      * _get_http_domain of website
    #      * _render_template of mail.template (and sms.template)
    #      * _prepare_confirmation_report
    #      * build_email of ir.mail.server
    #      * send_email of ir.mail.server
    #
    #     Extra info:
    #      * backend success might be linked to various resource types. We send email by each of that
    #     """
    #     if self:
    #         lang = self[0].partner_id.lang or self._context.get("lang") or self.env.user.lang
    #         base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #         template_ctx = self._context.copy()
    #         template_ctx.update({
    #             "lang": lang,
    #             "base_url": base_url,
    #             "reshedule": reshedule,
    #         })
    #         website_needed = hasattr(self[0], "website_id")
    #         templ_key = "business_appointment.email_template_successful_appointment"
    #         default_template = self.with_context(lang=lang).env.ref(templ_key, False)
    #         for appointment in self:
    #             rtype = appointment.resource_type_id
    #             template = rtype.with_context(lang=lang).success_mail_template_id or default_template
    #             if template:
    #                 website_http_domain = website_needed and appointment.website_id \
    #                                       and appointment.website_id._get_http_domain() or base_url
    #                 company_id = appointment.company_id
    #                 if not company_id:
    #                     company_id = website_needed and appointment.website_id.company_id or self.env.user.company_id
    #                 template_ctx.update({
    #                     "website_http_domain": website_http_domain,
    #                     "target_company": company_id,
    #                 })
    #                 body_html = template.with_context(template_ctx)._render_template(
    #                     template.body_html,
    #                     'business.appointment',
    #                     [appointment.id],
    #                 ).get(appointment.id)
    #                 subject = template.with_context(template_ctx)._render_template(
    #                     template.subject,
    #                     'business.appointment',
    #                     [appointment.id],
    #                 ).get(appointment.id)
    #                 pdf_content = appointment._prepare_confirmation_report()
    #                 attachments = False
    #                 if template.is_send_attachment:
    #                     attachments = [(appointment.safe_file_name + ".pdf", pdf_content, 'application/pdf')]
    #                 mail_server = self.env['ir.mail_server']
    #                 try:
    #                     receivers_emails = [appointment.partner_id.email]
    #                     if appointment.resource_id and appointment.resource_id.sucess_email_partner_ids:
    #                         receivers_emails += appointment.resource_id.sucess_email_partner_ids.mapped("email")
    #                     for receiver in receivers_emails:
    #                         cemail_from = self.env.company.partner_id.email or self.env.user.company_id.partner_id.email
    #                         message = mail_server.build_email(
    #                             email_from=cemail_from,
    #                             subject=subject,
    #                             body=body_html,
    #                             subtype='html',
    #                             email_to=[receiver],
    #                             attachments=attachments,
    #                         )
    #                         mail_server.send_email(message)
    #                 except Exception as e:
    #                     _logger.error("Success email is not sent {}".format(e))


class MailTemplate(models.Model):
    _inherit = "mail.template"

    is_send_attachment = fields.Boolean(string="Is Send Attachment")
