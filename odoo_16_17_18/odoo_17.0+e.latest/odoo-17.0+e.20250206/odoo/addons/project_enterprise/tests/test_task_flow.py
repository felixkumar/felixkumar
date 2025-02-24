# Part of Odoo. See LICENSE file for full copyright and licensing details

from datetime import datetime
from dateutil.relativedelta import relativedelta
from markupsafe import Markup
from pytz import timezone

from odoo import Command
from odoo.tests import TransactionCase
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from odoo.addons.mail.tests.common import mail_new_test_user


class TestTaskFlow(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.resource_calendar_id.tz = "Europe/Brussels"
        cls.project_user = mail_new_test_user(
            cls.env, login='Armande',
            name='Armande Project_user', email='armande.project_user@example.com',
            notification_type='inbox',
            groups='project.group_project_user',
        )

        cls.project_test_user = mail_new_test_user(
            cls.env, login='Armando',
            name='Armando Project_user', email='armando.project_user@example.com',
            notification_type='inbox',
            groups='project.group_project_user',
        )

        cls.project_test = cls.env['project.project'].create({
            'name': 'Project Test',
        })

        cls.portal_user = mail_new_test_user(
            cls.env, login='portal_project',
            name='Portal_user', email='portal_project_user@example.com',
            notification_type='email',
            groups='base.group_portal',
        )

    def create_tasks(self, nb=40):
        now = datetime.combine(datetime.now(), datetime.min.time())
        hour_start = [6, 11]
        hour_end = [10, 15]
        users = [self.project_test_user, self.project_user, self.project_user | self.project_test_user]

        self.env['project.task'].with_context(tracking_disable=True).create([{
            'name': 'Fsm task ' + str(i),
            'user_ids': users[i % 3],
            'project_id': self.project_test.id,
            'planned_date_begin': now + relativedelta(days=i / 2, hour=hour_start[i % 2]),
            'date_deadline': now + relativedelta(days=i / 2, hour=hour_end[i % 2])
        } for i in range(0, nb)])

    def test_planning_overlap(self):
        task_A = self.env['project.task'].create({
            'name': 'Fsm task 1',
            'user_ids': self.project_user,
            'project_id': self.project_test.id,
            'planned_date_begin': datetime.now(),
            'date_deadline': datetime.now() + relativedelta(hours=4)
        })
        task_B = self.env['project.task'].create({
            'name': 'Fsm task 2',
            'user_ids': self.project_user,
            'project_id': self.project_test.id,
            'planned_date_begin': datetime.now() + relativedelta(hours=2),
            'date_deadline': datetime.now() + relativedelta(hours=6)
        })
        task_C = self.env['project.task'].create({
            'name': 'Fsm task 2',
            'user_ids': self.project_user,
            'project_id': self.project_test.id,
            'planned_date_begin': datetime.now() + relativedelta(hours=5),
            'date_deadline': datetime.now() + relativedelta(hours=7)
        })
        task_D = self.env['project.task'].create({
            'name': 'Fsm task 2',
            'user_ids': self.project_user,
            'project_id': self.project_test.id,
            'planned_date_begin': datetime.now() + relativedelta(hours=8),
            'date_deadline': datetime.now() + relativedelta(hours=9)
        })
        self.assertEqual(task_A.planning_overlap, Markup('<p>Armande Project_user has 1 tasks at the same time.</p>'))
        self.assertEqual(task_B.planning_overlap, Markup('<p>Armande Project_user has 2 tasks at the same time.</p>'))
        self.assertFalse(task_D.planning_overlap, "No task should be overlapping with task_D")

    def test_gantt_progress_bar(self):
        self.env['project.task'].create([{
            'name': 'Task 1',
            'user_ids': self.project_user,
            'project_id': self.project_test.id,
            'planned_date_begin': '2021-09-24 06:00:00',
            'date_deadline': '2021-09-24 15:00:00',
        }, {
            'name': 'Task 2',
            'user_ids': self.project_user,
            'project_id': self.project_test.id,
            'planned_date_begin': '2021-09-27 06:00:00',
            'date_deadline': '2021-09-28 15:00:00',
        }, {
            'name': 'Task 3',
            'user_ids': self.project_user,
            'project_id': self.project_test.id,
            'planned_date_begin': '2021-09-29 05:00:00',
            'date_deadline': '2021-09-29 08:00:00',
        }, {
            'name': 'Task 4',
            'user_ids': self.project_user,
            'project_id': self.project_test.id,
            'planned_date_begin': '2021-09-30 12:00:00',
            'date_deadline': '2021-09-30 15:00:00',
        }])

        progress_bar = self.env['project.task'].gantt_progress_bar(
            ['user_ids'], {'user_ids': self.project_user.ids}, '2021-09-26 00:00:00', '2021-10-02 23:59:59'
        )['user_ids']
        self.assertEqual(22, progress_bar[self.project_user.id]['value'], "User should have 22 hours planned on this period")
        self.assertEqual(40, progress_bar[self.project_user.id]['max_value'], "User is expected to work 40 hours on this period")

        self.env['project.task'].create([{
            'name': 'Task 1',
            'user_ids': self.project_user,
            'project_id': self.project_test.id,
            'planned_date_begin': '2021-10-02 08:00:00',
            'date_deadline': '2021-10-02 17:00:00',
        }])

        progress_bar = self.env['project.task'].gantt_progress_bar(
            ['user_ids'], {'user_ids': self.project_user.ids}, '2021-09-26 00:00:00', '2021-10-02 23:59:59'
        )['user_ids']
        self.assertEqual(31, progress_bar[self.project_user.id]['value'], "User should have 31 hours planned on this period")
        self.assertEqual(40, progress_bar[self.project_user.id]['max_value'], "User is expected to work 40 hours on this period")

        self.env['project.task'].create([{
            'name': 'Task 2',
            'user_ids': self.project_user,
            'project_id': self.project_test.id,
            'planned_date_begin': '2021-09-24 08:00:00',
            'date_deadline': '2021-09-27 17:00:00',
        }])

        progress_bar = self.env['project.task'].gantt_progress_bar(
            ['user_ids'], {'user_ids': self.project_user.ids}, '2021-09-26 00:00:00', '2021-10-02 23:59:59'
        )['user_ids']
        self.assertEqual(39, progress_bar[self.project_user.id]['value'], "User should have 39 hours planned on this period")
        self.assertEqual(40, progress_bar[self.project_user.id]['max_value'], "User is expected to work 40 hours on this period")

    def test_project_user_can_see_progress_bar(self):
        self.env['project.task'].create([{
            'name': 'Task 1',
            'user_ids': self.project_user,
            'project_id': self.project_test.id,
            'planned_date_begin': '2021-09-27 06:00:00',
            'date_deadline': '2021-09-28 15:00:00',
        }])

        progress_bar = self.env['project.task'].with_user(self.project_test_user).gantt_progress_bar(
            ['user_ids'], {'user_ids': self.project_user.ids}, '2021-09-26 00:00:00', '2021-10-02 23:59:59'
        )['user_ids']
        self.assertEqual(16, progress_bar[self.project_user.id]['value'], "User should have 22 hours planned on this period")
        self.assertEqual(40, progress_bar[self.project_user.id]['max_value'], "User is expected to work 40 hours on this period")

    def test_portal_user_cannot_see_progress_bar(self):
        self.env['project.task'].create([{
            'name': 'Task 1',
            'user_ids': self.project_user,
            'project_id': self.project_test.id,
            'planned_date_begin': '2021-09-27 06:00:00',
            'date_deadline': '2021-09-28 15:00:00',
        }])

        progress_bar = self.env['project.task'].with_user(self.portal_user).gantt_progress_bar(
            ['user_ids'], {'user_ids': self.project_user.ids}, '2021-09-26 00:00:00', '2021-10-02 23:59:59'
        )['user_ids']
        self.assertFalse(progress_bar, "Progress bar should be empty for non-project users")

    def test_planned_date_consistency_for_tasks(self):
        """ This test ensures that a task can not have date start set, if its date end is False"""
        task_1 = self.env['project.task'].create([{
            'name': 'Task 1',
            'user_ids': self.project_user,
            'project_id': self.project_test.id,
            'planned_date_begin': '2021-09-27 06:00:00',
            'date_deadline': '2021-09-28 15:00:00',
        }])

        task_1.planned_date_begin = False
        self.assertFalse(task_1.planned_date_begin, 'the planned date begin should be set to False')
        self.assertEqual('2021-09-28', task_1.date_deadline.strftime('%Y-%m-%d'))

        task_1.write({'planned_date_begin': '2021-09-27 06:00:00'})
        self.assertEqual('2021-09-27', task_1.planned_date_begin.strftime('%Y-%m-%d'), 'the planned date begin should be set to the new date')
        self.assertEqual('2021-09-28', task_1.date_deadline.strftime('%Y-%m-%d'), 'the planned date end should be set')

        task_1.date_deadline = False
        self.assertFalse(task_1.planned_date_begin, 'the planned date begin should be set to False')
        self.assertFalse(task_1.date_deadline, 'the planned date end should be set to False')

        task_1.write({'date_deadline': '2021-09-27 06:00:00'})
        self.assertFalse(task_1.planned_date_begin, 'the planned date begin should not be updated')
        self.assertEqual('2021-09-27', task_1.date_deadline.strftime('%Y-%m-%d'))

    def test_performance(self):
        nb = 40
        self.create_tasks(nb=nb)
        start = datetime.combine(datetime.now(), datetime.min.time()) + relativedelta(days=-1)
        end = start + relativedelta(days=nb / 2 + 1)
        users = self.project_user | self.project_test_user

        with self.assertQueryCount(__system__=7):
            # Query count should be stable even if the number of tasks or users increase (progress bar query count is O(1))
            progress_bar = self.env['project.task'].gantt_progress_bar(
                ['user_ids'], {'user_ids': users.ids}, start.strftime(DEFAULT_SERVER_DATETIME_FORMAT), end.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            )['user_ids']

        self.assertEqual(len(progress_bar), 3)  # 2 users + 1 warning

    def test_editing_task_planned_date(self):
        """Check writing dates to a task:
            - when writing to a single task, write dates as given
            - when writing to multiple tasks, write dates as given if any task already had dates
            - otherwise, modify dates according to assignee's or company's schedule
        """
        self.env.user.tz = "UTC"
        self.env.company.resource_calendar_id.tz = "UTC"
        self.project_user.resource_calendar_id = self.env.company.resource_calendar_id
        self.project_test_user.resource_calendar_id = self.env['resource.calendar'].create({
            'attendance_ids': [Command.create({
                'name': day,
                'dayofweek': day,
                'day_period': 'afternoon',
                'hour_from': 12,
                'hour_to': 19,
            }) for day in '12345'],
        })

        tasks = task_A, task_B, task_C = self.env['project.task'].create([{
            'name': "Task A - Armande",
            'user_ids': self.project_user.ids,
            'project_id': self.project_test.id,
        }, {
            'name': "Task B - Armando",
            'user_ids': self.project_test_user.ids,
            'project_id': self.project_test.id,
        }, {
            'name': "Task C - Planned",
            'user_ids': (self.project_user + self.project_test_user).ids,
            'project_id': self.project_test.id,
            'planned_date_begin': '2024-08-27 05:00:00',
            'date_deadline': '2024-08-27 10:00:00',
        }])

        self.assertEqual(task_C.planned_date_begin.hour, 5, "No overwrite on create")
        self.assertEqual(task_C.date_deadline.hour, 10, "No overwrite on create")

        (task_A + task_C).write({
            'planned_date_begin': '2024-08-25 00:00:00',
            'date_deadline': '2024-08-26 23:59:59',
        })

        self.assertEqual(task_A.planned_date_begin.hour, 0, "Write as is when batch processing includes task with dates")
        self.assertEqual(task_A.date_deadline.hour, 23, "Write as is when batch processing includes task with dates")
        self.assertEqual(task_C.planned_date_begin.hour, 0, "Write as is when batch processing includes task with dates")
        self.assertEqual(task_C.date_deadline.hour, 23, "Write as is when batch processing includes task with dates")

        task_B.write({
            'planned_date_begin': '2024-08-27 16:00:00',
            'date_deadline': '2024-08-27 21:00:00',
        })
        self.assertEqual(task_B.planned_date_begin.hour, 16, "Hand-picked hours shouldn't change")
        self.assertEqual(task_B.date_deadline.hour, 21, "Hand-picked hours shouldn't change")

        tasks.date_deadline = False
        self.assertFalse(
            any(task.planned_date_begin for task in tasks),
            "Removing deadline should also remove planned_date_begin",
        )

        tasks.write({
            'planned_date_begin': '2024-08-27 16:00:00',
            'date_deadline': '2024-08-27 22:00:00',
        })
        self.assertListEqual(
            [(task.planned_date_begin.hour, task.date_deadline.hour) for task in tasks],
            [(16, 17), (16, 19), (16, 17)],
            "Plan tasks using schedule when batch processing",
        )

        tasks.write({
            'date_deadline': False,
            'user_ids': self.project_user.ids,
        })
        (task_B + task_C).write({
            'planned_date_begin': '2024-03-24 06:00:00',
            'date_deadline': '2024-03-30 15:00:00',
        })
        self.assertEqual('2024-03-25', task_B.planned_date_begin.strftime('%Y-%m-%d'),
            'the planned date begin should be the first working day found according to the resource calendar of the user assigned and the start datetime selected by the user')
        self.assertEqual('2024-03-29', task_B.date_deadline.strftime('%Y-%m-%d'),
            'the planned date end should be the last working day found according to the resource calendar of the user assigned and the end datetime selected by the user')
        self.assertEqual('2024-03-25', task_C.planned_date_begin.strftime('%Y-%m-%d'),
            'the planned date begin should be the first working day found according to the resource calendar of the user assigned and the start datetime selected by the user')
        self.assertEqual('2024-03-29', task_C.date_deadline.strftime('%Y-%m-%d'),
            'the planned date end should be the last working day found according to the resource calendar of the user assigned and the end datetime selected by the user')

        tasks.write({
            'planned_date_begin': '2024-03-24 06:00:00',
            'date_deadline': '2024-03-30 15:00:00',
        })
        self.assertEqual('2024-03-24', task_A.planned_date_begin.strftime('%Y-%m-%d'),
            'the planned date begin should be the one selected by the user')
        self.assertEqual('2024-03-30', task_A.date_deadline.strftime('%Y-%m-%d'),
            'the planned date end should be the one selected by the user')
        self.assertEqual('2024-03-24', task_B.planned_date_begin.strftime('%Y-%m-%d'),
            'the planned date begin should be the one selected by the user')
        self.assertEqual('2024-03-30', task_B.date_deadline.strftime('%Y-%m-%d'),
            'the planned date end should be the one selected by the user')
        self.assertEqual('2024-03-24', task_C.planned_date_begin.strftime('%Y-%m-%d'),
            'the planned date begin should be the one selected by the user')
        self.assertEqual('2024-03-30', task_C.date_deadline.strftime('%Y-%m-%d'),
            'the planned date end should be the one selected by the user')
