/** @odoo-module **/

import { CalendarController } from "@web/views/calendar/calendar_controller";
import { CalendarFilters } from "@business_appointment/components/calendar_filters/calendar_filters";
import { viewButtons } from "@business_appointment/views/view_buttons/view_buttons";

export class AppointmentCalendarController extends CalendarController {
    /*
    * Overwrite to add onw actions and services
    */
    setup() {
        super.setup(...arguments);
        Object.assign(this, viewButtons(this));
    }
    /*
    * Re-write to always launch the scheduling wizard
    */
    createRecord(record) {
        this.model._makeAppointment(record);
    }
    /*
    * The method to prepare appointment context
    */
    getAppointmentsContext() {
    	return this.model.getAppointmentsContext()
    }
}

AppointmentCalendarController.template = `business_appointment.BusinessAppointmentCalendarView`;
AppointmentCalendarController.components = { ...CalendarController.components, CalendarFilters }
