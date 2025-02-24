/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { viewButtons } from "@business_appointment/views/view_buttons/view_buttons";

export class AppointmentListController extends ListController {
    /*
    * Overwrite to add onw actions and services
    */
    setup() {
        super.setup(...arguments);
        Object.assign(this, viewButtons(this));
    }
    /*
    * The method to prepare appointment context
    */
    getAppointmentsContext() {
        return this.env.searchModel.globalContext
    }
}
