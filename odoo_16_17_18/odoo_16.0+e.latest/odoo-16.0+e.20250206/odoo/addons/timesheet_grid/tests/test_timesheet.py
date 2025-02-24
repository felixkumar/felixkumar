# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo import fields, Command
from odoo.osv import expression
from odoo.tools.float_utils import float_compare

from odoo.addons.mail.tests.common import MockEmail
from odoo.addons.hr_timesheet.tests.test_timesheet import TestCommonTimesheet
from odoo.exceptions import AccessError, UserError

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


@freeze_time(datetime(2021, 4, 1) + timedelta(hours=12, minutes=21))
class TestTimesheetValidation(TestCommonTimesheet, MockEmail):

    def setUp(self):
        super(TestTimesheetValidation, self).setUp()
        today = fields.Date.today()
        self.timesheet1 = self.env['account.analytic.line'].with_user(self.user_employee).create({
            'name': "my timesheet 1",
            'project_id': self.project_customer.id,
            'task_id': self.task1.id,
            'date': today - timedelta(days=1),
            'unit_amount': 2.0,
        })
        self.timesheet2 = self.env['account.analytic.line'].with_user(self.user_employee).create({
            'name': "my timesheet 2",
            'project_id': self.project_customer.id,
            'task_id': self.task2.id,
            'date': today - timedelta(days=1),
            'unit_amount': 3.11,
        })

    def test_timesheet_validation_user(self):
        """ Employee record its timesheets and Officer validate them. Then try to modify/delete it and get Access Error """
        # Officer validate timesheet of 'user_employee' through wizard
        timesheet_to_validate = self.timesheet1 | self.timesheet2
        timesheet_to_validate.with_user(self.user_manager).action_validate_timesheet()

        # Check timesheets 1 and 2 are validated
        self.assertTrue(self.timesheet1.validated)
        self.assertTrue(self.timesheet2.validated)

        # Employee can not modify validated timesheet
        with self.assertRaises(AccessError):
            self.timesheet1.with_user(self.user_employee).write({'unit_amount': 5})
        # Employee can not delete validated timesheet
        with self.assertRaises(AccessError):
            self.timesheet2.with_user(self.user_employee).unlink()

        # Employee can still create new timesheet before the validated date
        last_month = datetime.now() - relativedelta(months=1)
        self.env['account.analytic.line'].with_user(self.user_employee).create({
            'name': "my timesheet 3",
            'project_id': self.project_customer.id,
            'task_id': self.task2.id,
            'date': last_month,
            'unit_amount': 2.5,
        })

        # Employee can still create timesheet after validated date
        next_month = datetime.now() + relativedelta(months=1)
        timesheet4 = self.env['account.analytic.line'].with_user(self.user_employee).create({
            'name': "my timesheet 4",
            'project_id': self.project_customer.id,
            'task_id': self.task2.id,
            'date': next_month,
            'unit_amount': 2.5,
        })
        # And can still update non validated timesheet
        timesheet4.write({'unit_amount': 7})

    def test_timesheet_validation_manager(self):
        """ Officer can see timesheets and modify the ones of other employees """
       # Officer validate timesheet of 'user_employee' through wizard
        timesheet_to_validate = self.timesheet1 | self.timesheet2
        timesheet_to_validate.with_user(self.user_manager).action_validate_timesheet()
        # manager modify validated timesheet
        self.timesheet1.with_user(self.user_manager).write({'unit_amount': 5})

    def test_timesheet_validation_stop_timer(self):
        """ Check that the timers are stopped when validating the task even if the timer belongs to another user """
        # Start timer with employee user
        timesheet = self.timesheet1
        timesheet.date = fields.Date.today()
        start_unit_amount = timesheet.unit_amount
        timesheet.with_user(self.user_employee).action_timer_start()
        timer = self.env['timer.timer'].search([("user_id", "=", self.user_employee.id), ('res_model', '=', 'account.analytic.line')])
        self.assertTrue(timer, 'A timer has to be running for the user employee')
        with freeze_time(fields.Date.today() + timedelta(days=1)):
            # Manager will validate the timesheet the next date but the employee forgot to stop his timer.
            # Validate timesheet with manager user
            timesheet.with_user(self.user_manager).action_validate_timesheet()
        # Check if old timer is stopped
        self.assertFalse(timer.exists())
        # Check if time spent is add to the validated timesheet
        self.assertGreater(timesheet.unit_amount, start_unit_amount, 'The unit amount has to be greater than at the beginning')

    def _test_next_date(self, now, result, delay, interval):

        def _now(*args, **kwargs):
            return now

        # To allow testing

        patchers = [patch('odoo.fields.Datetime.now', _now)]

        for patcher in patchers:
            self.startPatcher(patcher)

        self.user_manager.company_id.write({
            'timesheet_mail_manager_interval': interval,
            'timesheet_mail_manager_delay': delay,
        })

        self.assertEqual(result, self.user_manager.company_id.timesheet_mail_manager_nextdate)

    def test_timesheet_next_date_reminder_neg_delay(self):

        result = datetime(2020, 4, 23, 8, 8, 15)
        now = datetime(2020, 4, 22, 8, 8, 15)
        self._test_next_date(now, result, -3, "weeks")

        result = datetime(2020, 4, 30, 8, 8, 15)
        now = datetime(2020, 4, 23, 8, 8, 15)
        self._test_next_date(now, result, -3, "weeks")
        now = datetime(2020, 4, 24, 8, 8, 15)
        self._test_next_date(now, result, -3, "weeks")
        now = datetime(2020, 4, 25, 8, 8, 15)
        self._test_next_date(now, result, -3, "weeks")

        result = datetime(2020, 4, 27, 8, 8, 15)
        now = datetime(2020, 4, 26, 8, 8, 15)
        self._test_next_date(now, result, -3, "months")

        result = datetime(2020, 5, 28, 8, 8, 15)
        now = datetime(2020, 4, 27, 8, 8, 15)
        self._test_next_date(now, result, -3, "months")
        now = datetime(2020, 4, 28, 8, 8, 15)
        self._test_next_date(now, result, -3, "months")
        now = datetime(2020, 4, 29, 8, 8, 15)
        self._test_next_date(now, result, -3, "months")

        result = datetime(2020, 2, 27, 8, 8, 15)
        now = datetime(2020, 2, 26, 8, 8, 15)
        self._test_next_date(now, result, -3, "weeks")

        result = datetime(2020, 3, 5, 8, 8, 15)
        now = datetime(2020, 2, 27, 8, 8, 15)
        self._test_next_date(now, result, -3, "weeks")
        now = datetime(2020, 2, 28, 8, 8, 15)
        self._test_next_date(now, result, -3, "weeks")
        now = datetime(2020, 2, 29, 8, 8, 15)
        self._test_next_date(now, result, -3, "weeks")

        result = datetime(2020, 2, 26, 8, 8, 15)
        now = datetime(2020, 2, 25, 8, 8, 15)
        self._test_next_date(now, result, -3, "months")

        result = datetime(2020, 3, 28, 8, 8, 15)
        now = datetime(2020, 2, 26, 8, 8, 15)
        self._test_next_date(now, result, -3, "months")
        now = datetime(2020, 2, 27, 8, 8, 15)
        self._test_next_date(now, result, -3, "months")
        now = datetime(2020, 2, 28, 8, 8, 15)
        self._test_next_date(now, result, -3, "months")

    def test_minutes_computing_after_timer_stop(self):
        """ Test if unit_amount is updated after stoping a timer """
        Timesheet = self.env['account.analytic.line']
        timesheet_1 = Timesheet.with_user(self.user_employee).create({
            'project_id': self.project_customer.id,
            'task_id': self.task1.id,
            'name': '/',
            'unit_amount': 1,
        })

        # When the timer is greater than 1 minute
        now = datetime.now()
        timesheet_1.with_user(self.user_employee).action_timer_start()
        timesheet_1.with_user(self.user_employee).user_timer_id.timer_start = now - timedelta(minutes=1, seconds=28)
        timesheet_1.with_user(self.user_employee).action_timer_stop()

        self.assertGreater(timesheet_1.unit_amount, 1, 'unit_amount should be greated than his last value')

    def test_timesheet_display_timer(self):
        current_timesheet_uom = self.env.company.timesheet_encode_uom_id

        # self.project_customer.allow_timesheets = True

        self.env.company.timesheet_encode_uom_id = self.env.ref('uom.product_uom_hour')
        self.assertTrue(self.timesheet1.display_timer)

        # Force recompute field
        self.env.company.timesheet_encode_uom_id = self.env.ref('uom.product_uom_day')
        self.timesheet1._compute_display_timer()
        self.assertFalse(self.timesheet1.display_timer)

        self.env.company.timesheet_encode_uom_id = current_timesheet_uom

    def test_add_time_from_wizard(self):
        wizard = self.env['project.task.create.timesheet'].create({
            'time_spent': 0.15,
            'task_id': self.task1.id,
        })
        wizard.with_user(self.user_employee).save_timesheet()
        self.assertEqual(self.task1.timesheet_ids[0].unit_amount, 0.15)

    def test_action_add_time_to_timer_multi_company(self):
        company = self.env['res.company'].create({'name': 'My_Company'})
        self.env['hr.employee'].with_company(company).create({
            'name': 'coucou',
            'user_id': self.user_manager.id,
        })
        self.user_manager.write({'company_ids': [Command.link(company.id)]})
        timesheet = self.env['account.analytic.line'].with_user(self.user_manager).create({'name': 'coucou', 'project_id': self.project_customer.id})
        timesheet.with_user(self.user_manager).action_add_time_to_timer(1)

    def test_working_hours_for_employees(self):
        company = self.env['res.company'].create({'name': 'My_Company'})
        employee = self.env['hr.employee'].with_company(company).create({
            'name': 'Juste Leblanc',
            'user_id': self.user_manager.id,
            'create_date': date(2021, 1, 1),
            'employee_type': 'freelance',  # Avoid searching the contract if hr_contract module is installed before this module.
        })
        employees_grid_data = [{
            'id': employee.id,
            'display_name': employee.name,
            'grid_row_index': 0}]

        working_hours = employee.get_timesheet_and_working_hours_for_employees(employees_grid_data, '2021-12-01', '2021-12-31')
        self.assertEqual(working_hours[employee.id]['units_to_work'], 184.0, "Number of hours should be 23d * 8h/d = 184h")

        # Create a user in the second company and link it to the employee created above
        user = self.env['res.users'].with_company(company).create({
            'name': 'Juste Leblanc',
            'login': 'juste_leblanc',
            'groups_id': [
                Command.link(self.env.ref('project.group_project_user').id),
                Command.link(self.env.ref('hr_timesheet.group_hr_timesheet_user').id),
            ],
            'company_ids': [Command.link(company.id), Command.link(self.project_customer.company_id.id),],
        })
        employee.user_id = user

        # Create a timesheet for a project in the first company for the employee in the second company
        self.assertTrue(employee.company_id != self.project_customer.company_id)
        self.assertTrue(user.company_id != self.project_customer.company_id)
        Timesheet = self.env['account.analytic.line']
        Timesheet.with_user(user).create({
            'project_id': self.project_customer.id,
            'task_id': self.task1.id,
            'unit_amount': 1.0,
        })

        # Read the timesheets and working hours of the second company employee as a manager from the first company
        # Invalidate the env cache first, because the above employee creation filled the fields data as superuser.
        # The data of the fields must be emptied so the manager user fetches the data again.
        self.env.invalidate_all()
        working_hours = self.env['hr.employee'].with_user(
            self.user_manager
        ).get_timesheet_and_working_hours_for_employees(employees_grid_data, '2021-04-01', '2021-04-30')
        self.assertEqual(working_hours[employee.id]['worked_hours'], 1.0)

        # Now, same thing but archiving the employee. The manager should still be able to read his timesheet
        # despite the fact the employee has been archived.
        employee.active = False
        self.env.invalidate_all()
        working_hours = self.env['hr.employee'].with_user(
            self.user_manager
        ).get_timesheet_and_working_hours_for_employees(employees_grid_data, '2021-04-01', '2021-04-30')
        self.assertEqual(working_hours[employee.id]['worked_hours'], 1.0)

        # Now same thing but with the multi-company employee rule disabled
        # Users are allowed to disable multi-company rules at will,
        # the code should be compliant with that,
        # and should still work/not crash when the multi-company rule is disabled
        self.env.ref('hr.hr_employee_comp_rule').active = False
        self.env.invalidate_all()
        working_hours = self.env['hr.employee'].with_user(
            self.user_manager
        ).get_timesheet_and_working_hours_for_employees(employees_grid_data, '2021-04-01', '2021-04-30')
        self.assertEqual(working_hours[employee.id]['worked_hours'], 1.0)

    def test_timesheet_grid_filter_equal_string(self):
        """Make sure that if you use a filter with (not) equal to,
           there won't be any error with grid view"""
        row_fields = ['project_id', 'task_id']
        col_field = 'date'
        cell_field = 'unit_amount'
        domain = [['employee_id', '=', self.user_employee.employee_id.id],
                  ['project_id', '!=', False]]
        grid_range = {'name': 'week', 'string': 'Week', 'span': 'week', 'step': 'day'}
        orderby = 'project_id,task_id'

        # Filter on project equal a different name, expect 0 row
        new_domain = expression.AND([domain, [('project_id', '=', self.project_customer.name[:-1])]])
        result = self.env['account.analytic.line'].read_grid(row_fields, col_field, cell_field, domain=new_domain, range=grid_range, orderby=orderby)
        self.assertFalse(result['rows'])

        # Filter on project not equal to exact name, expect 0 row
        new_domain = expression.AND([domain, [('project_id', '!=', self.project_customer.name)]])
        result = self.env['account.analytic.line'].read_grid(row_fields, col_field, cell_field, domain=new_domain, range=grid_range, orderby=orderby)
        self.assertFalse(result['rows'])

        # Filter on project_id to make sure there are timesheets
        new_domain = expression.AND([domain, [('project_id', '=', self.project_customer.name)]])
        result = self.env['account.analytic.line'].read_grid(row_fields, col_field, cell_field, domain=new_domain, range=grid_range, orderby=orderby)
        self.assertEqual(len(result['rows']), 2)

        # Filter on task equal to task1, expect timesheet1 (task 1)
        new_domain = expression.AND([domain, [('task_id', '=', self.timesheet1.task_id.name)]])
        result = self.env['account.analytic.line'].read_grid(row_fields, col_field, cell_field, domain=new_domain, range=grid_range, orderby=orderby)
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['rows'][0]['values']['project_id'][0], self.timesheet1.project_id.id)
        self.assertEqual(result['rows'][0]['values']['task_id'][0], self.timesheet1.task_id.id)

        # Filter on task not equal to task1, expect timesheet2 (task 2)
        new_domain = expression.AND([domain, [('task_id', '!=', self.timesheet1.task_id.name)]])
        result = self.env['account.analytic.line'].read_grid(row_fields, col_field, cell_field, domain=new_domain, range=grid_range, orderby=orderby)
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['rows'][0]['values']['project_id'][0], self.timesheet2.project_id.id)
        self.assertEqual(result['rows'][0]['values']['task_id'][0], self.timesheet2.task_id.id)

    def test_timesheet_manager_reminder(self):
        """ Reminder mail will be sent to both manager Administrator and User Officer to validate the timesheet """
        date = datetime(2022, 3, 3, 8, 8, 15)
        now = datetime(2022, 3, 1, 8, 8, 15)
        self._test_next_date(now, date, -3, "weeks")
        user = self.env.ref('base.user_admin')

        with freeze_time(date), self.mock_mail_gateway():
            self.env['res.company']._cron_timesheet_reminder_manager()
            self.assertEqual(len(self._new_mails.filtered(lambda x: x.res_id == user.employee_id.id)), 1, "An email sent to the 'Administrator Manager'")
            self.assertEqual(len(self._new_mails.filtered(lambda x: x.res_id == self.empl_manager.id)), 1, "An email sent to the 'User Empl Officer'")

    def test_timesheet_employee_reminder(self):
        """ Reminder mail will be sent to each Users' Employee """

        date = datetime(2022, 3, 3, 8, 8, 15)

        Timesheet = self.env['account.analytic.line']
        timesheet_vals = {
            'name': "my timesheet",
            'project_id': self.project_customer.id,
            'date': datetime(2022, 3, 2, 8, 8, 15),
            'unit_amount': 8.0,
        }
        Timesheet.with_user(self.user_employee).create({**timesheet_vals, 'task_id': self.task2.id})
        Timesheet.with_user(self.user_employee2).create({**timesheet_vals, 'task_id': self.task1.id})

        self.user_employee.company_id.timesheet_mail_employee_nextdate = date

        with freeze_time(date), self.mock_mail_gateway():
            self.env['res.company']._cron_timesheet_reminder_employee()
            self.assertEqual(len(self._new_mails.filtered(lambda x: x.res_id == self.empl_employee.id)), 1, "An email sent to the 'User Empl Employee'")
            self.assertEqual(len(self._new_mails.filtered(lambda x: x.res_id == self.empl_employee2.id)), 1, "An email sent to the 'User Empl Employee 2'")

    def test_task_timer_min_duration_and_rounding(self):
        self.env["res.config.settings"].create({
            "timesheet_min_duration": 23,
            "timesheet_rounding": 0,
        }).execute()

        self.task1.action_timer_start()
        act_window_action = self.task1.action_timer_stop()
        wizard = self.env[act_window_action['res_model']].with_context(act_window_action['context']).new()
        self.assertEqual(float_compare(wizard.time_spent, 0.38, 0), 0)
        self.env["res.config.settings"].create({
            "timesheet_rounding": 30,
        }).execute()

        self.task1.action_timer_start()
        act_window_action = self.task1.action_timer_stop()
        wizard = self.env[act_window_action['res_model']].with_context(act_window_action['context']).new()
        self.assertEqual(wizard.time_spent, 0.5)

    def test_timesheet_grid_filter_task_without_project(self):
        """Make sure that a task without project can not be pulled in the domain"""
        row_fields = ['project_id', 'task_id']
        col_field = 'date'
        cell_field = 'unit_amount'
        domain = [['employee_id', '=', self.user_employee.employee_id.id],
                  ['project_id', '!=', False]]
        orderby = 'project_id,task_id'
        # add a task without project
        self.env['project.task'].with_context({'mail_create_nolog': True}).create({
            'name': 'Test task without project'
        })
        # look for this task
        new_domain = expression.AND([domain, [('task_id', '=', 'Test task without project')]])
        result = self.env['account.analytic.line'].with_context(group_expand="group_expand").read_grid(row_fields, col_field, cell_field, domain=new_domain, orderby=orderby)
        # there is no error and nothing is in the result because a task witout project can not have timesheets
        self.assertEqual(len(result['rows']), 0)

    def test_adjust_grid(self):
        today_date = fields.Date.today()
        company = self.env['res.company'].create({'name': 'My_Company'})
        self.user_manager.company_ids = self.env.companies
        employee = self.env['hr.employee'].with_company(company).create({
            'name': 'coucou',
            'timesheet_manager_id': self.user_manager.id,
        })

        Timesheet = self.env['account.analytic.line']
        timesheet = Timesheet.with_user(self.user_manager).create({
            'employee_id': employee.id,
            'project_id': self.project_customer.id,
            'date': today_date - timedelta(days=1),
            'unit_amount': 2,
        })
        timesheet.with_user(self.user_manager).action_validate_timesheet()

        column_date = f'{today_date - timedelta(days=1)}/{today_date}'
        Timesheet.adjust_grid([('id', '=', timesheet.id)], 'date', column_date, 'unit_amount', 3.0)

        self.assertEqual(Timesheet.search_count([('employee_id', '=', employee.id)]), 2, "Should create new timesheet instead of updating validated timesheet in cell")

    def test_get_last_week(self):
        """Test the get_last_week method. It should return grid_anchor (GA), last_week (LW),
            where last_week is first Sunday before GA - 7 days. Example:
            Su Mo Tu We Th Fr Sa
            LW -- -- -- -- -- --
            -- -- GA -- -- -- --
        """
        AnalyticLine = self.env['account.analytic.line']
        for d in range(8, 22):
            grid_anchor = datetime(2023, 1, d)
            dummy, last_week = AnalyticLine.with_context(grid_anchor=grid_anchor)._get_last_week()
            self.assertEqual(last_week, date(2023, 1, ((d - 1) // 7 - 1) * 7 + 1))

    def test_validation_timesheet_at_current_date(self):
        Timesheet = self.env['account.analytic.line']
        timesheet1, timesheet2 = Timesheet.create([
            {
                'name': '/',
                'project_id': self.project_customer.id,
                'employee_id': self.empl_employee.id,
                'unit_amount': 1.0,
            } for i in range(2)
        ])
        timesheet1.with_user(self.user_manager).action_validate_timesheet()
        self.assertTrue(timesheet1.validated)

        # Try to validate another timesheet at the current date when Lock Date feature is enabled
        self.env['res.config.settings'].create({'prevent_old_timesheets_encoding': True}) \
                                       .execute()
        self.assertEqual(
            self.empl_employee.last_validated_timesheet_date,
            date.today(),
            'The last validated timesheet date set on the employee should be the current one.'
        )

        # Try to launch a timer with that employee
        self.assertFalse(timesheet2.with_user(self.user_employee).is_timer_running)
        timesheet2.with_user(self.user_employee).action_timer_start()
        self.assertTrue(timesheet2.with_user(self.user_employee).is_timer_running)
        timesheet = Timesheet.with_user(self.user_employee).create({
            'name': '/',
            'project_id': self.project_customer.id,
            'unit_amount': 2.0,
        })
        self.assertEqual(timesheet.employee_id, self.empl_employee)

        timesheet2.with_user(self.user_manager).action_validate_timesheet()
        self.assertTrue(timesheet2.validated)
        self.assertFalse(timesheet2.with_user(self.user_employee).is_timer_running)

        with self.assertRaises(AccessError):
            Timesheet.with_user(self.user_employee).create({
                'name': '/',
                'project_id': self.project_customer.id,
                'unit_amount': 1.0,
                'date': date.today() - relativedelta(days=1),
            })

    def test_validate_multi_company_with_prevent_old_timesheets_encoding(self):
        """
            Check timesheets validation with `prevent_old_timesheets_encoding` setting
            in a multi-company context.
        """
        company_A = self.env['res.company'].create({'name': 'Company A'})
        company_B = self.env['res.company'].create({'name': 'Company B'})

        self.env['res.config.settings'].with_company(company_A).create({
            'prevent_old_timesheets_encoding': True,
        }).execute()

        self.user_manager.write({'company_ids': [Command.link(company_A.id), Command.link(company_B.id)]})

        employee_A = self.env['hr.employee'].with_company(company_A).create({'name': 'Employee A'})
        employee_B = self.env['hr.employee'].with_company(company_B).create({'name': 'Employee B'})

        project_A = self.env['project.project'].with_company(company_A).create({'name': 'Project A'})
        project_B = self.env['project.project'].with_company(company_B).create({'name': 'Project B'})

        timesheets = self.env['account.analytic.line'].with_user(self.user_manager).create([
            {'employee_id': employee_A.id, 'project_id': project_A.id},
            {'employee_id': employee_B.id, 'project_id': project_B.id},
        ])

        # Validate timesheets belonging to two different companies at the same time
        timesheets.with_user(self.user_manager).action_validate_timesheet()

    def test_timesheet_entry_with_multiple_projects(self):
        Timesheet = self.env['account.analytic.line']

        # Create project
        project_customer2 = self.env['project.project'].create({
            'name': 'Project Y',
            'allow_timesheets': True,
            'partner_id': self.partner.id,
            'analytic_account_id': self.analytic_account.id,
        })

        # Create two timesheet entries for the same employee, one for each project, with different unit amounts
        Timesheet.create([
            {
                'name': 'Timesheet 1',
                'project_id': self.project_customer.id,
                'employee_id': self.empl_employee.id,
                'unit_amount': 5.0,
                'date': '2024-01-01',
            },
            {
                'name': 'Timesheet 2',
                'project_id': project_customer2.id,
                'employee_id': self.empl_employee.id,
                'unit_amount': 10.0,
                'date': '2024-01-01',
            },
        ])

        timesheet_count = Timesheet.search_count([('employee_id', '=', self.empl_employee.id), ('date', '=', '2024-01-01')])
        Timesheet.adjust_grid([('employee_id', '=', self.empl_employee.id)], 'date', '2024-01-01', 'unit_amount', 3.0)
        self.assertEqual(
            Timesheet.search_count([('employee_id', '=', self.empl_employee.id), ('date', '=', '2024-01-01')]),
            timesheet_count + 1,
            "Adjust grid should create new timesheet if cell contains multiple timesheets"
        )

        # Disable timesheet feature for projects
        self.project_customer.allow_timesheets = False
        project_customer2.allow_timesheets = False

        # Raise user error if timesheet is disabled in both projects
        with self.assertRaises(UserError):
            Timesheet.adjust_grid([('employee_id', '=', self.empl_employee.id)], 'date', '2024-01-01', 'unit_amount', 5.0)
