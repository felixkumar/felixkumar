/** @odoo-module **/

import { ChosenAppointments } from "@business_appointment/components/chosen_appointments/chosen_appointments";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, onMounted, useState } from "@odoo/owl";
import { useChildRef } from "@web/core/utils/hooks";
import { useService } from "@web/core/utils/hooks";
import { View } from "@web/views/view";


export class ChooseCustomerDialog extends Component {
    /*
    * Re-write to import required services and update props on the component start
    */
    setup() {
        super.setup();
        this.state = useState({ chosenAppointments: this.props.chosenAppointments });
        this.modalRef = useChildRef();
        this.rpc = useService("rpc");
        this.orm = useService("orm");
        this.actionService = useService("action");
        const buttonTemplate = "business_appointment.ChooseCustomerDialog.buttons";
        this.viewProps = {
            type: "form",
            buttonTemplate: buttonTemplate,
            context: this.props.context || {},
            display: { controlPanel: false },
            mode: "edit",
            resId: this.props.resId || false,
            resModel: this.props.resModel,
            viewId: this.props.viewId || false,
            preventCreate: this.props.preventCreate || false,
            preventEdit: false,
            discardRecord: () => {
                this.props.close();
            },
            saveRecord: async (record, params) => {
                const chosenAppointments = _.map(this.state.chosenAppointments, function (core) { return { id: core.id } });
                await record.model.root.update(_.object(["reservation_ids"], [{ operation: "ADD_M2M", ids: chosenAppointments }]));
                const saved = await record.save({ stayInEdition: true, noReload: false });
                if (saved) {
                    await this.props.onRecordSaved(record);
                    const action = await this.orm.call(
                        "business.appointment", "action_return_appointments_view", [this.state.chosenAppointments.map(rec => rec.id)]
                    );
                    if (action) { await this.actionService.doAction(action) };
                    this.props.close();
                };
            },
        };
        onMounted(() => {
            // Hide excess buttons
            if (this.modalRef.el.querySelector(".modal-footer").childElementCount > 1) {
                const defaultButton = this.modalRef.el.querySelector(".modal-footer button.o-default-button");
                if (defaultButton) { defaultButton.classList.add("d-none") };
            };
        });
    }
    /*
    * The method to prepare ChosenAppointments
    */
    getChosenAppointmentsProps() {
        return {
            scheduling: false,
            chosenAppointments: this.state.chosenAppointments,
            onSlotReserved: false,
            onSlotRemoved: this.onSlotRemoved.bind(this),
            manageRpc: this.rpc.bind(this),
        }
    }
    /*
    * The method to manage slot unreservation
    */
    async onSlotRemoved(coreId) {
        this.state.chosenAppointments = this.state.chosenAppointments.filter(rec => rec.id != coreId);
        await this.props.onParentSlotRemoved(coreId);
        if (this.state.chosenAppointments <= 0) { this.props.close() };
    }
};

ChooseCustomerDialog.template = "business_appointment.ChooseCustomerDialog";
ChooseCustomerDialog.components = { ChosenAppointments, Dialog, View };
ChooseCustomerDialog.props = {
    close: Function,
    resModel: String,
    context: { type: Object, optional: true },
    chosenAppointments: { type: Array, optional: false },
    mode: {
        optional: true,
        validate: (m) => ["edit", "readonly"].includes(m),
    },
    onRecordSaved: { type: Function, optional: true },
    onParentSlotRemoved: { type: Function, optional: true },
    preventCreate: { type: Boolean, optional: true },
    resId: { type: [Number, Boolean], optional: true },
    title: { type: String, optional: true },
    viewId: { type: [Number, Boolean], optional: true },
    size: Dialog.props.size,
};
ChooseCustomerDialog.defaultProps = {
    onRecordSaved: () => {},
};