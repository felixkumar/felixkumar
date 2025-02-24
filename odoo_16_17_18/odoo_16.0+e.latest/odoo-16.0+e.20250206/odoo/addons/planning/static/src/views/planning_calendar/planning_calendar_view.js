/** @odoo-module **/

import { registry } from "@web/core/registry";
import { calendarView } from "@web/views/calendar/calendar_view";
import { PlanningCalendarController } from "@planning/views/planning_calendar/planning_calendar_controller";
import { PlanningCalendarRenderer } from "@planning/views/planning_calendar/planning_calendar_renderer";
import { PlanningCalendarModel } from "@planning/views/planning_calendar/planning_calendar_model";

export const planningCalendarView = {
    ...calendarView,
    Controller: PlanningCalendarController,
    Model: PlanningCalendarModel,
    Renderer: PlanningCalendarRenderer,

    buttonTemplate: "planning.PlanningCalendarController.controlButtons",
};
registry.category("views").add("planning_calendar", planningCalendarView);
