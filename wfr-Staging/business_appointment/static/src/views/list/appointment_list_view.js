/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { AppointmentListController } from "@business_appointment/views/list/appointment_list_controller";

export const AppointmentListView = {
    ...listView,
    Controller: AppointmentListController,
    buttonTemplate: "business_appointment.ControllerButtons",
};

registry.category("views").add("appointment_list", AppointmentListView);
