# -*- coding: utf-8 -*-

import odoo.http as http

from odoo.http import request
from odoo.addons.calendar.controllers.main import CalendarController


class PopUpController(CalendarController):
    """
    Introduced to check popup notifications
    """
    @http.route("/business/appointment/popup/notify", type="json", auth="user")
    def notify_appointment(self):
        """
        The method to trigger check of potential popup notifications

        Methods:
         * action_get_next_popup_notif of alarm.task
        """
        res = []
        if request.env.user.has_group("business_appointment.group_ba_user"):
            try:
                res = request.env["alarm.task"].action_get_next_popup_notif()
            except:
                res = []
        return res

    @http.route("/business/appointment/alarm/delete", type="json", auth="user")
    def delete_appointment_alarm(self, alarm_id):
        """
        Remove alarm task

        Methods:
         * action_mark_popup_done of alarm.task
        """
        res = True
        try:
            alarm = request.env["alarm.task"].browse(alarm_id).exists()
            if alarm:
                res = request.env["alarm.task"].browse(alarm_id).action_mark_popup_done()
            else:
                res = False
        except Exception as er:
            res = False
        return res
