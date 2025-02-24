/** @odoo-module **/

import { registry } from "@web/core/registry";
import { calendarView } from "@web/views/calendar/calendar_view";
import { AppointmentCalendarController } from "@business_appointment/views/calendar/appointment_calendar_controller";
import { AppointmentCalendarModel } from "@business_appointment/views/calendar/appointment_calendar_model";
import { AppointmentSearchModel } from "@business_appointment/views/search/appointment_search";

export const AppointmentCalendarView = {
    ...calendarView,
    SearchModel: AppointmentSearchModel,
    Controller: AppointmentCalendarController,
    Model: AppointmentCalendarModel,
    buttonTemplate: "business_appointment.CalendarControllerButtons",
};

registry.category("views").add("appointment_calendar", AppointmentCalendarView);
