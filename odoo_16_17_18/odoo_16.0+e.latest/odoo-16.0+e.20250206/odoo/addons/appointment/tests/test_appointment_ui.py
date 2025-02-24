# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json

from datetime import datetime, timedelta
from freezegun import freeze_time

from odoo import http
from odoo.addons.appointment.tests.common import AppointmentCommon
from odoo.addons.mail.tests.common import mail_new_test_user
from odoo.tests import common, tagged, users


class AppointmentUICommon(AppointmentCommon, common.HttpCase):

    @classmethod
    def setUpClass(cls):
        super(AppointmentUICommon, cls).setUpClass()

        cls.env.user.tz = "Europe/Brussels"
        cls.std_user = mail_new_test_user(
            cls.env,
            company_id=cls.company_admin.id,
            email='std_user@test.example.com',
            groups='base.group_user',
            name='Solène StandardUser',
            notification_type='email',
            login='std_user',
            tz='Europe/Brussels'  # UTC + 1 (at least in February)
        )
        cls.portal_user = cls._create_portal_user()

@tagged('appointment_ui', '-at_install', 'post_install')
class AppointmentUITest(AppointmentUICommon):

    @users('apt_manager')
    def test_route_apt_type_search_create_anytime(self):
        self.authenticate(self.env.user.login, self.env.user.login)
        request = self.url_open(
            "/appointment/appointment_type/search_create_anytime",
            data=json.dumps({}),
            headers={"Content-Type": "application/json"},
        ).json()
        result = request.get('result', {})
        self.assertTrue(result.get('appointment_type_id'), 'The request returns the id of the custom appointment type')
        appointment_type = self.env['appointment.type'].browse(result['appointment_type_id'])
        self.assertEqual(appointment_type.category, 'anytime')
        self.assertEqual(len(appointment_type.slot_ids), 7, "7 slots have been created: (1 / days for 7 days)")
        self.assertTrue(all(slot.slot_type == 'recurring' for slot in appointment_type.slot_ids), "All slots are 'recurring'")

    @users('apt_manager')
    def test_route_apt_type_search_create_anytime_with_context(self):
        self.authenticate(self.env.user.login, self.env.user.login)
        request = self.url_open(
            "/appointment/appointment_type/search_create_anytime",
            data=json.dumps({
                'params': {
                    'context': {
                        'default_assign_method': 'random',
                    },
                }
            }),
            headers={"Content-Type": "application/json"},
        ).json()
        result = request.get('result', dict())
        self.assertTrue(result.get('appointment_type_id'), 'The request returns the id of the custom appointment type')

        appointment_type = self.env['appointment.type'].browse(result['appointment_type_id'])
        # All default context fields should be ignored because of clean_context()
        self.assertEqual(appointment_type.assign_method, 'chosen')

    @users('apt_manager')
    def test_route_apt_type_create_custom(self):
        self.authenticate(self.env.user.login, self.env.user.login)

        with freeze_time(self.reference_now):
            unique_slots = [{
                'start': (datetime.now() + timedelta(hours=1)).replace(microsecond=0).isoformat(' '),
                'end': (datetime.now() + timedelta(hours=2)).replace(microsecond=0).isoformat(' '),
                'allday': False,
            }, {
                'start': (datetime.now() + timedelta(days=2)).replace(microsecond=0).isoformat(' '),
                'end': (datetime.now() + timedelta(days=3)).replace(microsecond=0).isoformat(' '),
                'allday': True,
            }]
            request = self.url_open(
                "/appointment/appointment_type/create_custom",
                data=json.dumps({
                    'params': {
                        'slots': unique_slots,
                    }
                }),
                headers={"Content-Type": "application/json"},
            ).json()
        result = request.get('result', {})
        self.assertTrue(result.get('appointment_type_id'), 'The request returns the id of the custom appointment type')
        appointment_type = self.env['appointment.type'].browse(result['appointment_type_id'])
        self.assertEqual(appointment_type.category, 'custom')
        self.assertEqual(appointment_type.name, "%s - Let's meet" % self.env.user.name)
        self.assertEqual(len(appointment_type.slot_ids), 2, "Two slots have been created")

        with freeze_time(self.reference_now):
            for slot in appointment_type.slot_ids:
                self.assertEqual(slot.slot_type, 'unique', 'All slots should be unique')
                if slot.allday:
                    self.assertEqual(slot.start_datetime, datetime.now() + timedelta(days=2))
                    self.assertEqual(slot.end_datetime, datetime.now() + timedelta(days=3))
                else:
                    self.assertEqual(slot.start_datetime, datetime.now() + timedelta(hours=1))
                    self.assertEqual(slot.end_datetime, datetime.now() + timedelta(hours=2))

    @users('apt_manager')
    def test_route_create_custom_with_context(self):
        self.authenticate(self.env.user.login, self.env.user.login)
        now = datetime.now()
        unique_slots = [{
            'start': (now + timedelta(hours=1)).replace(microsecond=0).isoformat(' '),
            'end': (now + timedelta(hours=2)).replace(microsecond=0).isoformat(' '),
            'allday': False,
        }, {
            'start': (now + timedelta(days=2)).replace(microsecond=0).isoformat(' '),
            'end': (now + timedelta(days=3)).replace(microsecond=0).isoformat(' '),
            'allday': True,
        }]
        request = self.url_open(
            "/appointment/appointment_type/create_custom",
            data=json.dumps({
                'params': {
                    'slots': unique_slots,
                    'context': {
                        'default_assign_method': 'random',
                    },
                }
            }),
            headers={"Content-Type": "application/json"},
        ).json()
        result = request.get('result', dict())
        self.assertTrue(result.get('appointment_type_id'), 'The request returns the id of the custom appointment type')

        appointment_type = self.env['appointment.type'].browse(result['appointment_type_id'])
        # The default context fields should be ignored as the fields are not whitelisted
        self.assertEqual(appointment_type.assign_method, 'chosen')

    def test_share_appointment_type(self):
        self._create_invite_test_data()
        self.authenticate(None, None)
        res = self.url_open(self.invite_apt_type_bxls_2days.book_url)
        self.assertEqual(res.status_code, 200, "Response should = OK")

    def test_share_appointment_type_multi(self):
        self._create_invite_test_data()
        self.authenticate(None, None)
        res = self.url_open(self.invite_all_apts.book_url)
        self.assertEqual(res.status_code, 200, "Response should = OK")

    @users('apt_manager')
    def test_appointment_meeting_url(self):
        """ Test if a meeting linked to an appointment having location set,
        it should have a meeting URL (and visa versa).
        """
        CalendarEvent = self.env['calendar.event']
        self.authenticate(self.env.user.login, self.env.user.login)

        online_demo = self.env['appointment.type'].create({
            'name': 'Schedule a Demo (online - one hour)',
            'staff_user_ids': self.staff_user_bxls,
        })

        # Case 1: without location
        meeting_without_location_data = {
            'datetime_str': '2022-07-04 12:30:00',
            'duration_str': '1.0',
            'staff_user_id': self.staff_user_bxls.id,
            'name': 'Online Meeting',
            'phone': '2025550999',
            'email': 'test1@test.example.com',
            'csrf_token': http.Request.csrf_token(self)
        }
        url = f"/appointment/{online_demo.id}/submit"
        res = self.url_open(url, data=meeting_without_location_data)
        self.assertEqual(res.status_code, 200, "Response should = OK")
        access_token = res.url.split('?')[0].split('/calendar/view/')[-1]
        self.assertTrue(
            CalendarEvent.search([('access_token', '=', access_token)]).videocall_location,
            "Should have videocall_location set as the appointment type does not have a location"
        )

        # Case 2: with location
        meeting_with_location_data = {
            'datetime_str': '2022-07-04 10:30:00',
            'duration_str': '1.0',
            'staff_user_id': self.staff_user_bxls.id,
            'name': 'Doctor Appointment',
            'phone': '2025550888',
            'email': 'test2@test.example.com',
            'csrf_token': http.Request.csrf_token(self),
        }
        url = f"{self.base_url()}/appointment/{self.apt_type_bxls_2days.id}/submit"
        res = self.url_open(url, data=meeting_with_location_data)
        self.assertEqual(res.status_code, 200, "Response should = OK")
        access_token = res.url.split('?')[0].split('/calendar/view/')[-1]
        self.assertFalse(
            CalendarEvent.search([('access_token', '=', access_token)]).videocall_location,
            "Should not have videocall_location set as the appointment type has a location"
        )


@tagged('appointment_ui', '-at_install', 'post_install')
class CalendarTest(AppointmentUICommon):

    def test_meeting_accept_authenticated(self):
        event = self.env["calendar.event"].create(
            {"name": "Doom's day",
             "start": datetime(2019, 10, 25, 8, 0),
             "stop": datetime(2019, 10, 27, 18, 0),
             "partner_ids": [(4, self.std_user.partner_id.id)],
            }
        )
        token = event.attendee_ids[0].access_token
        url = "/calendar/meeting/accept?token=%s&id=%d" % (token, event.id)
        self.authenticate(self.std_user.login, self.std_user.login)
        res = self.url_open(url)

        self.assertEqual(res.status_code, 200, "Response should = OK")
        event.attendee_ids[0].invalidate_recordset()
        self.assertEqual(event.attendee_ids[0].state, "accepted", "Attendee should have accepted")

    def test_meeting_accept_unauthenticated(self):
        event = self.env["calendar.event"].create(
            {"name": "Doom's day",
             "start": datetime(2019, 10, 25, 8, 0),
             "stop": datetime(2019, 10, 27, 18, 0),
             "partner_ids": [(4, self.std_user.partner_id.id)],
            }
        )
        token = event.attendee_ids[0].access_token
        url = "/calendar/meeting/accept?token=%s&id=%d" % (token, event.id)
        res = self.url_open(url)

        self.assertEqual(res.status_code, 200, "Response should = OK")
        event.attendee_ids[0].invalidate_recordset()
        self.assertEqual(event.attendee_ids[0].state, "accepted", "Attendee should have accepted")

    def test_meeting_cancel_authenticated(self):
        """ Test that the meeting is not archived when a participant cancels their participation while
        there are still multiple attendees for the event and the meeting should be archived if there
        are fewer than 2 attendees.
        """
        self.authenticate(self.portal_user.login, self.portal_user.login)
        self.apt_type_bxls_2days.write({'is_published': 'True'})
        event_1, event_2 = self.env['calendar.event'].create([{
            'name': 'Test-Meeting 1',
            'user_id': self.staff_user_nz.id,
            'start': datetime(2023, 11, 23, 8, 0),
            'stop':  datetime(2023, 11, 23, 9, 0),
            'partner_ids':  [
                (4, self.staff_user_nz.partner_id.id),
                (4, self.portal_user.partner_id.id)
            ],
            'appointment_type_id': self.apt_type_bxls_2days.id,
        }, {
            'name': 'Test-Meeting 2',
            'user_id': self.staff_user_nz.id,
            'start': datetime(2023, 11, 23, 9, 0),
            'stop':  datetime(2023, 11, 23, 10, 0),
            'partner_ids': [
                (4, self.staff_user_nz.partner_id.id),
                (4, self.staff_user_aust.partner_id.id),
                (4, self.portal_user.partner_id.id)
            ],
            'appointment_type_id': self.apt_type_bxls_2days.id,
        }])
        cancel_meeting_data = {
            'access_token': event_1.access_token,
            'partner_id': self.portal_user.partner_id.id,
            'csrf_token': http.Request.csrf_token(self),
        }
        with freeze_time(datetime(2023, 11, 22, 8, 0)):
            cancel_meeting_url = f"/calendar/{event_1.access_token}/cancel"
            res = self.url_open(cancel_meeting_url, data=cancel_meeting_data)
        self.assertEqual(res.status_code, 200)
        # event_1 should be archive because there are < 2 attendee
        self.assertFalse(event_1.active)
        cancel_meeting_data = {
            'access_token': event_2.access_token,
            'partner_id': self.portal_user.partner_id.id,
            'csrf_token': http.Request.csrf_token(self),
        }
        with freeze_time(datetime(2023, 11, 22, 8, 0)):
            cancel_meeting_url = f"/calendar/{event_2.access_token}/cancel"
            res = self.url_open(cancel_meeting_url, data=cancel_meeting_data)
        self.assertEqual(res.status_code, 200)
        # event_2 should not be archive because there are 2 or more attendee
        self.assertTrue(event_2.active)
        self.assertEqual(event_2.attendee_ids.partner_id, self.staff_user_aust.partner_id + self.staff_user_nz.partner_id)
