/** @odoo-module **/

const { Component, onWillUnmount, useState } = owl;


export class ChosenAppointments extends Component {
    /*
    * The method to finish scheduling in the paret time slots
    */
    async onFinishAppointments() {
        if (this.props.scheduling) {
            await this.props.onSlotReserved();
        }
    }
    /*
    * The method to unreserve the scheduled appointment
    */
    async _onRemoveAppointment(coreId) {
        await this.props.manageRpc("/business_appointment/remove", { "reservation_ids": [coreId] });
        await this.props.onSlotRemoved(coreId);
    }
};
ChosenAppointments.template = "business_appointment.ChosenAppointments";
