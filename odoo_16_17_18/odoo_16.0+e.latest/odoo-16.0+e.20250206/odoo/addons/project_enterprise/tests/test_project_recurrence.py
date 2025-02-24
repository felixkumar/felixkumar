# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase

from datetime import date
from freezegun import freeze_time

class TestProjectRecurrenceEnterprise(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestProjectRecurrenceEnterprise, cls).setUpClass()
        cls.env.user.groups_id += cls.env.ref('project.group_project_recurring_tasks')
        cls.stage_a, cls.stage_b = cls.env['project.task.type'].create([
            {'name': 'a'},
            {'name': 'b'},
        ])
        cls.project_recurring = cls.env['project.project'].with_context({'mail_create_nolog': True}).create({
            'name': 'Recurring',
            'allow_recurring_tasks': True,
            'type_ids': [
                (4, cls.stage_a.id),
                (4, cls.stage_b.id),
            ]
        })

    def test_recurrence_with_planned_date_01(self):
        """
            Check that the planning date on the task is taken into account
            when calculating the date on which the next recurrence will be generated.
        """
        with freeze_time("2023-10-15"):
            task = self.env['project.task'].create({
                'name': 'test recurring task',
                'project_id': self.project_recurring.id,
                'recurring_task': True,
                'recurrence_update': 'all,',
                'planned_date_begin': '2023-11-12 06:50:00',
                'repeat_interval': 6,
                'repeat_unit': 'month',
                'repeat_type': 'forever',
                'repeat_on_month': 'date',
                'repeat_day': '1',
                'repeat_weekday': 'mon',
            })
            self.assertEqual(task.recurrence_id.next_recurrence_date, date(2024, 5, 1))  # And not date(2024, 4, 1) which is the date calculated from the current day

    def test_recurrence_with_planned_date_02(self):
        """
            Check that the planning date on the task is taken into account
            when calculating the date on which the next recurrence will be generated.
        """
        with freeze_time("2023-10-15"):
            task = self.env['project.task'].create({
                'name': 'test recurring task',
                'project_id': self.project_recurring.id,
                'recurring_task': True,
                'recurrence_update': 'all,',
                'planned_date_begin': '2023-07-11 06:50:00',
                'repeat_interval': 1,
                'repeat_unit': 'month',
                'repeat_type': 'until',
                'repeat_until': '2024-07-11',
                'repeat_on_month': 'date',
                'repeat_day': '1',
                'repeat_weekday': 'mon',
            })
            # 08/01/2023
            # 09/01/2023
            # 10/01/2023
            # 11/01/2023 --> first date after tomorrow
            # 12/01/2023
            # ...
            self.assertEqual(task.recurrence_id.next_recurrence_date, date(2023, 11, 1))

    def test_recurrence_with_planned_date_03(self):
        with freeze_time("2023-10-15"):
            task = self.env['project.task'].create({
                'name': 'test recurring task',
                'project_id': self.project_recurring.id,
                'recurring_task': True,
                'recurrence_update': 'all,',
                'planned_date_begin': '2023-07-11 06:50:00',
                'repeat_interval': 1,
                'repeat_unit': 'day',
                'repeat_type': 'until',
                'repeat_until': '2024-07-11',
                'repeat_on_month': 'date',
                'repeat_day': '1',
                'repeat_weekday': 'mon',
            })
            # Tomorrow even if there is an anterior date begin
            self.assertEqual(task.recurrence_id.next_recurrence_date, date(2023, 10, 16))

    def test_recurrence_with_planned_date_04(self):
        """
            Check if there is no error during comparison with tomorrow's date
            to select the next recurrence.
            Note: `freezegun` uses the `FakeDate` or `FakeDatetime` type
            Note 2: no assert because it uses the system date, which will vary
        """
        self.env['project.task'].create({
            'name': 'test recurring task',
            'project_id': self.project_recurring.id,
            'recurring_task': True,
            'recurrence_update': 'all,',
            'planned_date_begin': '2023-07-11 06:50:00',
            'repeat_interval': 1,
            'repeat_unit': 'day',
            'repeat_type': 'forever',
            'repeat_on_month': 'date',
            'repeat_day': '1',
            'repeat_weekday': 'mon',
        })
