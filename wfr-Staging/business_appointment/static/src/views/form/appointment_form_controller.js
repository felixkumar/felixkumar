/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { viewButtons } from "@business_appointment/views/view_buttons/view_buttons";

export class AppointmentFormController extends FormController {
    /*
    * Overwrite to add onw actions and services
    */
    setup() {
        super.setup(...arguments);
        Object.assign(this, viewButtons(this));
    }
    /*
    * The method to rescehdule the current appointment
    */
    async startReScheduling() {
        await this.startScheduling({ default_appointment_id: this.model.root.data.id });
    }
    /*
    * The method to prepare appointment context
    */
    getAppointmentsContext() {
        return this.env.searchModel.globalContext
    }
}

AppointmentFormController.template = `business_appointment.BusinessAppointmentFormView`;
