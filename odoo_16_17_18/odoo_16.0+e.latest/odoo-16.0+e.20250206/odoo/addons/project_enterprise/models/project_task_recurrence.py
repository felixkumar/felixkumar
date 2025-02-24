# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models

from datetime import datetime
from dateutil.relativedelta import relativedelta

class ProjectTaskRecurrence(models.Model):
    _inherit = "project.task.recurrence"

    def _set_next_recurrence_date_from_start_date(self, date_start=None):
        """
            Update the date of the next recurrence taking into account a specific start date.
            :param date_start: reference date for applying the recurrence rule,
                               tomorrow's date will be used if None
            :type date_start: date - datetime - string (format: '%Y-%m-%d %H:%M:%S') object
        """
        #
        #   date_start                 next_recurrence_date
        #       |                               |
        # ============X============X============X============X=========>
        #                               |
        #                            Tomorrow
        # X: potential future tasks to be created according to the recurrence rule
        #
        if not date_start:
            return self._set_next_recurrence_date()
        today = fields.Date.today()
        tomorrow = today + relativedelta(days=1)
        if isinstance(date_start, str):
            date_start = datetime.strptime(date_start, '%Y-%m-%d %H:%M:%S')
        if isinstance(date_start, datetime):
            date_start = date_start.date()
        for recurrence in self.filtered(
            lambda r:
            r.repeat_type == 'after' and r.recurrence_left >= 0
            or r.repeat_type == 'until' and r.repeat_until >= today
            or r.repeat_type == 'forever'
        ):
            if recurrence.repeat_type == 'after' and recurrence.recurrence_left == 0:
                recurrence.next_recurrence_date = False
            else:
                next_dates = self._get_next_recurring_dates(max(date_start, tomorrow), recurrence.repeat_interval, recurrence.repeat_unit, recurrence.repeat_type, recurrence.repeat_until, recurrence.repeat_on_month, recurrence.repeat_on_year, recurrence._get_weekdays(), recurrence.repeat_day, recurrence.repeat_week, recurrence.repeat_month)
                # If not next date after tomorrow, the recurrence is finished
                recurrence.next_recurrence_date = next((
                    next_date for next_date in next_dates
                    if (next_date.date() if isinstance(next_date, datetime) else next_date) >= tomorrow
                ), False)
