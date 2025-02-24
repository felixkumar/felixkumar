# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details
from datetime import date, datetime

from odoo import fields
from odoo.addons.project_forecast.tests.common import TestCommonForecast
from odoo.addons.hr_timesheet.tests.test_timesheet import TestCommonTimesheet


class TestPlanningTimesheet(TestCommonForecast):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.setUpEmployees()
        cls.setUpProjects()
        cls.employee_bert.write({
            'employee_type': 'freelance',
            'create_date': datetime(2019, 5, 6, 8, 0, 0),
        })

    def test_no_auto_genertaed_timesheet_in_future(self):
        with self._patch_now('2019-06-06 18:00:00'):
            self.project_opera.write({'allow_timesheets': True})

            planning_shift = self.env['planning.slot'].create({
                'project_id': self.project_opera.id,
                'employee_id': self.employee_bert.id,
                'resource_id': self.resource_bert.id,
                'allocated_hours': 16,
                'start_datetime': datetime(2019, 6, 6, 8, 0, 0),  # 6/6/2019 is a thursday, so a working day
                'end_datetime': datetime(2019, 6, 7, 17, 0, 0),
                'allocated_percentage': 100,
                'state': 'published',
            })
            self.assertFalse(planning_shift.timesheet_ids, "There should be no timesheet linked with current shift.")
            planning_shift._action_generate_timesheet()
            self.assertEqual(len(planning_shift.timesheet_ids), 1, "One timesheet should be generated for current shift.")
            self.assertEqual(planning_shift.timesheet_ids.date, fields.Datetime.today().date(), "Generated timesheet date should be today.")
            self.assertEqual(planning_shift.timesheet_ids.unit_amount, 8, "Timesheet should be generated for the 8 working hours of the employee")
            self.assertFalse(planning_shift.timesheet_ids.filtered(lambda x: x.date > date(2019, 6, 6)), "No timesheet should be generated in the future.")

    def test_custom_time_on_auto_generated_timesheet(self):
        with self._patch_now('2019-06-07 18:00:00'):
            self.project_opera.write({'allow_timesheets': True})

            planning_shift = self.env['planning.slot'].create({
                'project_id': self.project_opera.id,
                'employee_id': self.employee_bert.id,
                'resource_id': self.resource_bert.id,
                'allocated_hours': 37,
                'start_datetime': datetime(2019, 6, 3, 10, 0, 0),  # 3/6/2019 is a monday, so a working day
                'end_datetime': datetime(2019, 6, 7, 16, 0, 0),    # 7/6/2019 is a friday, so a working day
                'allocated_percentage': 100,
                'state': 'published',
            })
            self.assertFalse(planning_shift.timesheet_ids, "There should be no timesheet linked with current shift.")
            planning_shift._action_generate_timesheet()
            self.assertEqual(len(planning_shift.timesheet_ids), 5, "Five days timesheet should be generated for current shift.")
            self.assertEqual(planning_shift.timesheet_ids.filtered(lambda x: x.date == date(2019, 6, 3)).unit_amount, 6, "There should be a 6-hour timesheet on the first day of the shift.")
            self.assertEqual(planning_shift.timesheet_ids.filtered(lambda x: x.date == date(2019, 6, 4)).unit_amount, 8, "There should be a 8-hour timesheet on the second day of the shift.")
            self.assertEqual(planning_shift.timesheet_ids.filtered(lambda x: x.date == date(2019, 6, 7)).unit_amount, 7, "There should be a 7-hour timesheet on the last day of the shift.")

    def test_generate_timesheet_with_multiple_slots(self):
        """
        A test to check that when we create a timesheet from multiple slots
        with the same date and the same employee, we only get one.
        Test case:
        - Create two planning slots with th same date and employee
        - generate timesheets from the slots
        - ensure we got one timesheet line
        """
        slots = self.env["planning.slot"].create([
            {
                'project_id': self.project_opera.id,
                'resource_id': self.resource_joseph.id,
                'start_datetime': datetime(2021, 10, 29, 8, 0, 0),
                'end_datetime': datetime(2021, 10, 29, 12, 0, 0),
                'state': 'published',
                'allow_timesheets': True,
            },
            {
                'project_id': self.project_opera.id,
                'resource_id': self.resource_joseph.id,
                'start_datetime': datetime(2021, 10, 29, 13, 0, 0),
                'end_datetime': datetime(2021, 10, 29, 14, 0, 0),
                'state': 'published',
                'allow_timesheets': True,
            }
        ])
        slots._action_generate_timesheet()
        nb_timesheet = self.env["account.analytic.line"].search_count([('slot_id', 'in', slots.ids)])
        self.assertEqual(nb_timesheet, 1)

    def test_generate_timesheet_for_flexible_employees(self):
        """
        Generate timesheets for slot with a resource that has flexible hours.
        It should be coherent with the way we calculate allocated hours for the slot for a flexible resource.
        All datetime used in this test are working days.
        """
        self.project_opera.write({'allow_timesheets': True})
        self.resource_joseph.flexible_hours = True

        one_day_slot, multi_day_slot = self.env["planning.slot"].create([
            {
                'project_id': self.project_opera.id,
                'resource_id': self.resource_joseph.id,
                'start_datetime': datetime(2023, 5, 15, 6, 0, 0),
                'end_datetime': datetime(2023, 5, 15, 18, 0, 0),
                'allocated_hours': 12,
                'allocated_percentage': 150,
                'state': 'published',
                'allow_timesheets': True,
            },
            {
                'project_id': self.project_opera.id,
                'resource_id': self.resource_joseph.id,
                'start_datetime': datetime(2023, 5, 15, 8, 0, 0),
                'end_datetime': datetime(2023, 5, 16, 10, 0, 0),
                # as of writing this, allocated hours for a slot with a flexible resource
                # over the span of multiple days is just the average company hours per day
                # (so for 2 days = 16h for a 40h/w company calendar)
                'allocated_hours': 24,
                'allocated_percentage': 150,
                'state': 'published',
                'allow_timesheets': True,
            }
        ])
        (one_day_slot + multi_day_slot)._action_generate_timesheet()
        self.assertEqual(len(one_day_slot.timesheet_ids), 1, "One timesheet should be generated for a 1 day span slot.")
        self.assertEqual(one_day_slot.timesheet_ids.duration_unit_amount, 12, "The timesheet duration should be 12h.")
        self.assertEqual(len(multi_day_slot.timesheet_ids), 2, "Two timesheets should be generated for a 2 day span slot.")
        self.assertEqual(multi_day_slot.timesheet_ids.mapped('duration_unit_amount'), [12, 12], "The timesheets duration should be 12h per day.")

    def test_gantt_progress_bar_group_by_project(self):
        """
        This test ensures that the _gantt_progress_bar_project_id return values is correct.
        - Every project_id present in the res_ids should be present in the dict.
        - The 'value' should be 0 if the project contains no planning slot available in the date range given, else it should be equal to the total of every available slot for the given date range.
        - The 'max value' should be equal to the 'allocated_hours' field for each project.
        """
        projects = project_without_slot, project_slot_not_in_date_range, project_slot_in_date_range = self.env['project.project'].with_context(tracking_disable=True).create([{
            'name': 'Project no slot',
            'allow_forecast': True,
            'allocated_hours': 40,
        }, {
            'name': 'Project slot not in date range',
            'allow_forecast': True,
            'allocated_hours': 50,
        }, {
            'name': 'Project slot in date range',
            'allow_forecast': True,
            'allocated_hours': 60,
        }])
        start_date = datetime(2021, 10, 22, 8, 0, 0)
        end_date = datetime(2021, 10, 29, 8, 0, 0)
        planning_vals = {
            'resource_id': self.resource_joseph.id,
            'state': 'published',
            'allow_timesheets': True,
        }
        self.env["planning.slot"].create([{
            **planning_vals,
            'project_id': project_slot_in_date_range.id,
            'start_datetime': datetime(2021, 10, 25, 8, 0, 0),
            'end_datetime': datetime(2021, 10, 26, 12, 0, 0),
        }, {
            **planning_vals,
            'project_id': project_slot_in_date_range.id,
            'start_datetime': datetime(2021, 10, 26, 13, 0, 0),
            'end_datetime': datetime(2021, 10, 26, 17, 0, 0),
        }, {
            **planning_vals,
            'project_id': project_slot_not_in_date_range.id,
            'start_datetime': datetime(2021, 10, 20, 8, 0, 0),
            'end_datetime': datetime(2021, 10, 21, 12, 0, 0),
        }])
        res_ids = projects.ids
        expected_values = {
            project_without_slot.id: {'value': 0.0, 'max_value': 40.0},
            project_slot_not_in_date_range.id: {'value': 0.0, 'max_value': 50.0},
            project_slot_in_date_range.id: {'value': 16.0, 'max_value': 60.0}, # 12 hours in the 1st slot + 4 hours in the 2nd slot
        }
        values = self.env["planning.slot"]._gantt_progress_bar_project_id(res_ids, start_date, end_date)
        self.assertDictEqual(values, expected_values)

    def test_timesheets_forecast_analysis_with_weekend_included(self):
        with self._patch_now('2019-06-06 01:00:00'):
            self.project_opera.write({'allow_timesheets': True})
            self.env['planning.slot'].create({
                'project_id': self.project_opera.id,
                'employee_id': self.employee_bert.id,
                'resource_id': self.resource_bert.id,
                'allocated_hours': 40,
                'start_datetime': datetime(2019, 6, 6, 8, 0, 0),
                # 6/8/2019 and 6/9/2019 are weekend days
                'end_datetime': datetime(2019, 6, 12, 17, 0, 0),
                'allocated_percentage': 100,
                'state': 'draft',
            })
            self.env['planning.slot'].flush_model()
            result = self.env['project.timesheet.forecast.report.analysis'].read_group(
                domain=[["project_id", "=", self.project_opera.id]],
                fields=["planned_hours:sum", 'effective_hours:sum', 'difference:sum'],
                groupby=["entry_date:month"], lazy=False
            )
            self.assertEqual((result[0]['planned_hours']), 40)


class TestPlanningTimesheetView(TestCommonTimesheet):
    def test_get_view_timesheet_encode_uom(self):
        """ Test the label of timesheet time spent fields according to the company encoding timesheet uom """
        self.assert_get_view_timesheet_encode_uom([
            (
                'project_timesheet_forecast.project_timesheet_forecast_report_view_pivot',
                '//field[@name="planned_hours"]',
                [None, 'Planned Days']
            ),
        ])
