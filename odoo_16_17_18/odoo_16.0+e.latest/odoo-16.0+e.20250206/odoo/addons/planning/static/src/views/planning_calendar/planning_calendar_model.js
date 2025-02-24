/** @odoo-module **/

import { CalendarModel } from "@web/views/calendar/calendar_model";

export class PlanningCalendarModel extends CalendarModel {
    makeContextDefaults(rawRecord) {
        const context = super.makeContextDefaults(...arguments);
        if (["day", "week"].includes(this.meta.scale)) {
            context['planning_keep_default_datetime'] = true;
        }
        return context;
    }
}
