# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import date
from freezegun import freeze_time

from odoo.tests.common import tagged, users
from odoo.exceptions import ValidationError

from .common import TestHelpdeskTimesheetCommon


@tagged('-at_install', 'post_install')
class TestTimesheet(TestHelpdeskTimesheetCommon):

    def test_timesheet_cannot_be_linked_to_task_and_ticket(self):
        """ Test if an exception is raised when we want to link a task and a ticket in a timesheet

            Normally, now we cannot have a ticket and a task in one timesheet.

            Test Case:
            =========
            1) Create ticket and a task,
            2) Create timesheet with this ticket and task and check if an exception is raise.
        """
        # 1) Create ticket and a task
        ticket = self.helpdesk_ticket
        task = self.env['project.task'].create({
            'name': 'Test Task',
            'project_id': self.project.id,
        })

        # 2) Create timesheet with this ticket and task and check if an exception is raise
        with self.assertRaises(ValidationError):
            self.env['account.analytic.line'].create({
                'name': 'Test Timesheet',
                'unit_amount': 1,
                'project_id': self.project.id,
                'helpdesk_ticket_id': ticket.id,
                'task_id': task.id,
                'employee_id': self.env['hr.employee'].create({'user_id': self.env.uid}).id,
            })

    def test_compute_timesheet_partner_from_ticket_customer(self):
        partner2 = self.env['res.partner'].create({
            'name': 'Customer ticket',
            'email': 'customer@ticket.com',
        })
        helpdesk_ticket = self.helpdesk_ticket
        timesheet_entry = self.env['account.analytic.line'].create({
            'name': 'the only timesheet. So lonely...',
            'helpdesk_ticket_id': helpdesk_ticket.id,
            'project_id': self.helpdesk_team.project_id.id,
            'employee_id': self.env['hr.employee'].create({'user_id': self.env.uid}).id,
        })

        self.assertEqual(timesheet_entry.partner_id, self.partner, "The timesheet entry's partner should be equal to the ticket's partner/customer")

        helpdesk_ticket.write({'partner_id': partner2.id})

        self.assertEqual(timesheet_entry.partner_id, partner2, "The timesheet entry's partner should still be equal to the ticket's partner/customer, after the change")

    @users('admin')
    def test_helpdesk_timesheet_wizard_timezones(self):
        wizard = self.env['helpdesk.ticket.create.timesheet'].create({
            'description': 'Create timesheet wizard',
            'ticket_id': self.helpdesk_ticket.id,
            'time_spent': 1.0,
        })
        timezones = [
            'Pacific/Niue',        # UTC-11,
            'Europe/Brussels',     # UTC+1
            'Pacific/Kiritimati',  # UTC+14
        ]
        test_cases = {
            '2024-01-24 08:30': (-1, +0, +0),
            '2024-01-24 10:30': (-1, +0, +1),
            '2024-01-24 16:30': (+0, +0, +1),
        }

        for utc_time, day_diffs in test_cases.items():
            with freeze_time(utc_time):
                day = date.today().day
                expected = (date(2024, 1, day + diff) for diff in day_diffs)
                for tz, local_date in zip(timezones, expected):
                    self.env.user.tz = tz
                    timesheet = wizard.action_generate_timesheet()
                    self.assertEqual(
                        timesheet.date,
                        local_date,
                        f"{utc_time} UTC should be {local_date} in {tz} time",
                    )

    def test_log_timesheet_with_ticket_analytic_account(self):
        """ Test whether the analytic account of the project is set on the ticket.

            Test Case:
            ----------
                1) Create Ticket
                2) Check the default analytic account of the project and ticket
        """

        helpdesk_ticket = self.helpdesk_ticket

        self.assertEqual(helpdesk_ticket.analytic_account_id, self.project.analytic_account_id)

    def test_get_view_timesheet_encode_uom(self):
        """ Test the label of timesheet time spent fields according to the company encoding timesheet uom """
        self.assert_get_view_timesheet_encode_uom([
            (
                'helpdesk_timesheet.helpdesk_ticket_view_form_inherit_helpdesk_timesheet',
                '//field[@name="unit_amount"]',
                ['Hours Spent', 'Days Spent']
            ),
            (
                'helpdesk_timesheet.helpdesk_ticket_view_tree_inherit_helpdesk_timesheet',
                '//field[@name="total_hours_spent"]',
                [None, 'Days Spent']
            ),
        ])

    def test_default_company_id_for_timesheet(self):
        """ This test ensures that the default company_id used when a timesheet is created from the ticket form view is the company_id of its project. """
        new_company = self.env['res.company'].create({'name': "Do the extra miles"})
        project = self.env['project.project'].create({
            'name': 'Project',
            'allow_timesheets': True,
            'partner_id': self.partner.id,
            'company_id': new_company.id,
        })
        helpdesk_team = self.env['helpdesk.team'].create({
            'name': 'Test Team new company',
            'use_helpdesk_timesheet': True,
            'project_id': project.id,
            'company_id': new_company.id,
        })
        helpdesk_ticket = self.env['helpdesk.ticket'].create({
            'name': 'Test Ticket',
            'team_id': helpdesk_team.id,
            'partner_id': self.partner.id,
        })
        # Use the default values sent by the form view
        vals = {'date': '2023-11-03', 'user_id': False, 'employee_id': self.env['hr.employee'].create({'user_id': self.env.uid}).id, 'name': False,
                'unit_amount': 0, 'project_id': self.project.id, 'task_id': False, 'helpdesk_ticket_id': helpdesk_ticket.id}
        timesheet = self.env['account.analytic.line'].create([vals])
        self.assertEqual(timesheet.company_id, new_company, 'The expected company of the timesheet is the company from the project of its ticket')
