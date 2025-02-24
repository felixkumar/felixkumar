# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import _
from odoo.http import route, request
from odoo.addons.website_mass_mailing.controllers import main

_logger = logging.getLogger(__name__)

class MassMailController(main.MassMailController):

    @route('/website_mass_mailing/subscribe', type='json', website=True, auth='public')
    def subscribe(self, list_id, value, subscription_type, **post):
        Contacts = request.env['mailing.contact'].sudo()
        name, value = Contacts.get_name_email(value)
        if '@' in value:
            email_values = {
                'email_from': self.env.user.email_formatted,
                'email_to': value,
            }
            self.env['mail.template'].sudo().browse(
                self.env.ref('website_order_discount_tus.mail_template_desc_tus_ext').id).send_mail(self.id,
                                                                                                    email_values=email_values,
                                                                                                    force_send=True)
        return super(MassMailController, self).subscribe(list_id, value, subscription_type, **post)



    @route('/website_mass_mailing/subscribe', type='json', website=True, auth='public')
    def subscribe(self, list_id, value, subscription_type, **post):
        if not request.env['ir.http']._verify_request_recaptcha_token('website_mass_mailing_subscribe'):
            return {
                'toast_type': 'danger',
                'toast_content': _("Suspicious activity detected by Google reCaptcha."),
            }

        _logger.info("********** SUBSCRIBED: {}**************".format(value))
        ContactSubscription = request.env['mailing.contact.subscription'].sudo()
        Contacts = request.env['mailing.contact'].sudo()
        if subscription_type == 'email':
            name, value = Contacts.get_name_email(value)
        elif subscription_type == 'mobile':
            name = value

        fname = self._get_fname(subscription_type)
        subscription = ContactSubscription.search(
            [('list_id', '=', int(list_id)), (f'contact_id.{fname}', '=', value)], limit=1)
        if not subscription:
            # inline add_to_list as we've already called half of it
            contact_id = Contacts.search([(fname, '=', value)], limit=1)
            if not contact_id:
                contact_id = Contacts.create({'name': name, fname: value})
            contact_subscription_id = ContactSubscription.create({'contact_id': contact_id.id, 'list_id': int(list_id)})

            _logger.info("********** Contact Created: {}**************".format(contact_subscription_id))
            if '@' in value and contact_subscription_id:

                template = request.env['mail.template'].sudo().browse(
                    request.env.ref('website_order_discount_tus.mail_template_desc_tus_ext').id)

                email_values = {
                    'email_from': template.email_from or 'logistics@warefor.com',
                    'email_to': value,
                }

                template.send_mail(
                    contact_subscription_id.contact_id.id,
                    email_values=email_values,
                    force_send=True)
                _logger.info("********** Mail is sent from subscribed **************")

        elif subscription.opt_out:
            subscription.opt_out = False

        # Send discount mail to subscriber
        if '@' in value and ContactSubscription:
            email_values = {
                'email_from': self.env.user.email_formatted,
                'email_to': value,
            }
            self.env['mail.template'].sudo().browse(
                self.env.ref('website_order_discount_tus.mail_template_desc_tus_ext').id).send_mail(ContactSubscription.id,
                                                                                                    email_values=email_values,
                                                                                                    force_send=True)

        # add email to session
        request.session[f'mass_mailing_{fname}'] = value
        return {
            'toast_type': 'success',
            'toast_content': _("Thanks for subscribing!"),
        }
