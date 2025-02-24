#coding: utf-8

from odoo import api, models

class resource_calendar_attendance(models.Model):
    """
    Ovewrite to have possibility of 24-hours day (not finished at 23-59)
    """
    _inherit = "resource.calendar.attendance"

    @api.onchange("hour_from", "hour_to")
    def _onchange_hours(self):
        """
        Onchange method for hour_from, hour_to
        """
        for attend in self:
            attend.hour_from = min(attend.hour_from, 23.99)
            attend.hour_from = max(attend.hour_from, 0.0)
            attend.hour_to = min(attend.hour_to, 24.00)
            attend.hour_to = max(attend.hour_to, 0.0)
            attend.hour_to = max(attend.hour_to, attend.hour_from)
