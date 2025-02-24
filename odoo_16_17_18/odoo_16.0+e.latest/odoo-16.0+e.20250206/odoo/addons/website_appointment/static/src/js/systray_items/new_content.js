/** @odoo-module **/

import { NewContentModal, MODULE_STATUS } from '@website/systray_items/new_content';
import { patch } from 'web.utils';

patch(NewContentModal.prototype, 'website_appointment_new_content', {
    setup() {
        this._super();

        const newAppointmentTypeElement = this.state.newContentElements.find(element => element.moduleXmlId === 'base.module_website_appointment');
        newAppointmentTypeElement.createNewContent = () => this.onAddContent('website_appointment.appointment_type_action_add_simplified');
        newAppointmentTypeElement.status = MODULE_STATUS.INSTALLED;
        newAppointmentTypeElement.model = 'appointment.type';
    },
});
