/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { AppointmentFormController } from "@business_appointment/views/form/appointment_form_controller";

export const AppointmentFormView = {
    ...formView,
    Controller: AppointmentFormController,
    buttonTemplate: "business_appointment.ControllerButtons",
};

registry.category("views").add("appointment_form", AppointmentFormView);
