/** @odoo-module **/

import { CalendarModel } from "@web/views/calendar/calendar_model";
import { serializeDate } from "@web/core/l10n/dates";
import { viewButtons } from "@business_appointment/views/view_buttons/view_buttons";


export class AppointmentCalendarModel extends CalendarModel {
    /*
    * Re-write to add input upload
    */
    setup() {
        super.setup(...arguments);
        Object.assign(this, viewButtons(this));
    }
    /*
    * Re-write to always launch the scheduling wizard
    */
    async updateRecord(record, options = {}) {
        this._makeAppointment(record, { default_appointment_id: record.id })
    }
    /*
    * The method to launch make appointment wizard
    */
    async _makeAppointment(record, extraContext={}) {
        if (!this.canCreate) { return };
        const scheduleContext = Object.assign(extraContext, this.getAppointmentsContext(), this._getAppointmentDefaults(record));
        await this.startScheduling(extraContext);
    }
    /*
    * The method to prepare context based on filters and record data
    */
    getAppointmentsContext() {
        return this.env.searchModel.globalContext
    }
    /*
    * The method to calculate defaults based on the record data
    */
    _getAppointmentDefaults(record) {
        let start = record.start;
        let end = record.end;
        if (!end || !end.isValid) { end = start };
        return {
            default_date_start: serializeDate(start),
            default_date_end: serializeDate(end),
            default_duration: Math.abs(end - start) / 36e5,
        }
    }
};
