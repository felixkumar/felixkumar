# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import common, tagged


@tagged('voip')
class TestVoipMailActivity(common.TransactionCase):

    def test_voip_activity_deadline(self):
        partner = self.env['res.partner'].create({
            'name': 'Freddy Krueger',
            'phone': '1234',
        })
        baseDate = fields.Date.today(self)
        activity = self.env['mail.activity'].create({
            'activity_type_id': self.env.ref('mail.mail_activity_data_call').id,
            'user_id': self.env.user.id,
            'date_deadline': baseDate,
            'res_id': partner.id,
            'res_model_id': self.env['ir.model']._get('res.partner').id,
        })
        phonecall = activity.voip_phonecall_id
        self.assertEqual(phonecall.date_deadline, baseDate, "Phonecall deadline should have been set")
        newdate = fields.Date.today(self) + relativedelta(days=2)
        activity.date_deadline = newdate
        self.assertEqual(phonecall.date_deadline, newdate, "Phonecall deadline should have been updated")

    def test_voip_activity_phonecall_creation(self):
        """
        Creating a new 'phonecall' activity must result in the creation of a new
        phonecall record. This new record is populated with the data from the
        activity, including the related partner, even when the partner is not
        necessary to retrieve a relevant phone number.
        """
        phone_number = "+1-225-555-0132"
        partner = self.env["res.partner"].create({
            "name": "Bernadette Disco",
            "phone": phone_number,
        })
        activity = self.env["mail.activity"].create({
            "activity_type_id": self.env.ref("mail.mail_activity_data_call").id,
            "user_id": self.env.user.id,
            "date_deadline": fields.Date.today(),
            "res_id": partner.id,
            "res_model_id": self.env["ir.model"]._get("res.partner").id,
            "res_name": "Corkscrew replenishment",
        })
        phonecall = self.env["voip.phonecall"].search([("activity_id", "=", activity.id)])
        # Asserts that creating a new 'phonecall' activity results in the creation of a new phonecall record.
        self.assertTrue(phonecall)
        # Asserts that the new phonecall record has been populated with the expected data.
        self.assertRecordValues(phonecall, [{
            "activity_id": activity.id,
            "partner_id": partner.id,
            "phone": phone_number,
            "user_id": self.uid,
            "name": activity.res_name,
        }])
