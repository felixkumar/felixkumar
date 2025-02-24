# Part of Odoo. See LICENSE file for full copyright and licensing details.

from markupsafe import escape

from odoo import fields
from odoo.addons.test_whatsapp.tests.common import WhatsAppFullCase
from odoo.addons.whatsapp.tests.common import MockIncomingWhatsApp
from odoo.tests import tagged, users


@tagged('wa_message')
class DiscussChannel(WhatsAppFullCase, MockIncomingWhatsApp):

    @users('user_wa_admin')
    def test_channel_info_link(self):
        """ Test information posted on channels. Use case: first a message is
        sent to the customer, he replies, then another message is posted using a
        template. Record information should be displayed in channel. """
        template = self.whatsapp_template.with_user(self.env.user)
        test_record = self.test_base_record_nopartner.with_env(self.env)

        composer = self._instanciate_wa_composer_from_records(template, test_record)
        with self.mockWhatsappGateway():
            composer.action_send_whatsapp_template()

        with self.mockWhatsappGateway():
            self._receive_whatsapp_message(self.whatsapp_account, 'Hello', '32499123456')

        composer = self._instanciate_wa_composer_from_records(template, test_record)
        with self.mockWhatsappGateway():
            composer.action_send_whatsapp_template()

        discuss_channel = self.assertWhatsAppDiscussChannel(
            "32499123456",
            wa_msg_count=1, msg_count=3,
            wa_message_fields_values={
                'state': 'sent',
            },
        )
        (second_info, answer, first_info) = discuss_channel.message_ids
        self.assertEqual(
            second_info.body,
            f'<p>Template {template.name} was sent from WhatsApp Base Test <a target="_blank" '
            f'href="{test_record.get_base_url()}/web#model={test_record._name}&amp;id={test_record.id}">'
            f'{escape(test_record.display_name)}</a></p>',
            "Should contain a link and display_name to the new record from which the template was sent")
        self.assertEqual(answer.body, '<p>Hello</p>')
        self.assertIn(
            first_info.body,
            f'<p>Related WhatsApp Base Test: <a target="_blank" href="{test_record.get_base_url()}/web#'
            f'model={test_record._name}&amp;id={test_record.id}">{escape(test_record.display_name)}</a></p>',
            "Should contain a link and display_name to the new record from which the template was sent")

    @users('user_wa_admin')
    def test_channel_info_link_noname(self):
        """ Test that a channel can be created for a model without a name field
        and rec_name is correctly used for logged info. """
        test_record_noname = self.env['whatsapp.test.nothread.noname'].create({
            'country_id': self.env.ref('base.be').id,
            'customer_id': self.test_partner.id,
        })
        template = self.whatsapp_template.with_user(self.env.user)
        template.write({
            'model_id': self.env['ir.model']._get_id('whatsapp.test.nothread.noname'),
        })

        composer = self._instanciate_wa_composer_from_records(template, test_record_noname)
        with self.mockWhatsappGateway():
            composer.action_send_whatsapp_template()

        with self.mockWhatsappGateway():
            self._receive_whatsapp_message(self.whatsapp_account, 'Hello', '32485221100')

        discuss_channel = self.assertWhatsAppDiscussChannel("32485221100", wa_msg_count=1, msg_count=2)
        (answer, first_info) = discuss_channel.message_ids
        self.assertEqual(answer.body, '<p>Hello</p>')
        self.assertIn(
            first_info.body,
            f'<p>Related WhatsApp NoThread / NoResponsible /NoName: <a target="_blank"'
            f' href="{test_record_noname.get_base_url()}/web#model={test_record_noname._name}&amp;id={test_record_noname.id}">'
            f'{escape(test_record_noname.customer_id.name)}</a></p>',
            "Should contain a link and display_name to the new record from which the template was sent")

    @users('user_wa_admin')
    def test_channel_validity_date(self):
        """ Ensure the validity date of a whatsapp channel is only affected by
        messages sent by the whatsapp recipient. """
        template = self.whatsapp_template.with_user(self.env.user)
        test_record = self.test_base_record_nopartner.with_env(self.env)

        composer = self._instanciate_wa_composer_from_records(template, test_record)
        with self.mockWhatsappGateway():
            composer.action_send_whatsapp_template()

        self._receive_whatsapp_message(self.whatsapp_account, 'Hello', '32499123456')

        discuss_channel = self.env["discuss.channel"].search([("whatsapp_number", "=", "32499123456")])
        self.assertTrue(discuss_channel.whatsapp_channel_valid_until)
        first_valid_date = discuss_channel.whatsapp_channel_valid_until

        composer = self._instanciate_wa_composer_from_records(template, test_record)
        with self.mockWhatsappGateway():
            composer.action_send_whatsapp_template()
        second_valid_date = discuss_channel.whatsapp_channel_valid_until

        self.assertEqual(first_valid_date, second_valid_date)

    def test_message_reaction(self):
        """ Check a reaction is correctly added on a whatsapp message. """
        with self.mockWhatsappGateway():
            self._receive_whatsapp_message(self.whatsapp_account, "test", "32499123456")
        discuss_channel = self.assertWhatsAppDiscussChannel("32499123456", wa_msg_count=1, msg_count=1)
        message = discuss_channel.message_ids[0]
        self.assertTrue(message)
        with self.mockWhatsappGateway():
            self._receive_whatsapp_message(
                self.whatsapp_account,
                "",
                "32499123456",
                additional_message_values={
                    "reaction": {
                        "message_id": message.wa_message_ids[0].msg_uid,
                        "emoji": "😊",
                    },
                    "type": "reaction",
                },
            )
        self._reset_bus()
        with self.assertBus(
            [(self.cr.dbname, "discuss.channel", discuss_channel.id)],
            [{
                "type": "mail.record/insert",
                "payload": {"Message": {
                    "id": message.id,
                    "reactions": [
                        ["DELETE", {
                            "content": "😊",
                            "count": 0,
                            "message": {"id": message.id},
                            "personas": [[
                                "DELETE",
                                {"id": message.author_id.id, "type": "partner"},
                            ]],
                        }],
                        ["ADD", {
                            "content": "👍",
                            "count": 1,
                            "message": {"id": message.id},
                            "personas": [[
                                "ADD",
                                {
                                    "id": message.author_id.id,
                                    "type": "partner",
                                    "name": message.author_id.name,
                                    "write_date": fields.Datetime.to_string(
                                        message.author_id.write_date
                                    ),
                                },
                            ]],
                        }],
                    ],
                }
                },
            }],
        ):
            with self.mockWhatsappGateway():
                self._receive_whatsapp_message(
                    self.whatsapp_account,
                    "",
                    "32499123456",
                    additional_message_values={
                        "reaction": {
                            "message_id": message.wa_message_ids[0].msg_uid,
                            "emoji": "👍",
                        },
                        "type": "reaction",
                    },
                )
