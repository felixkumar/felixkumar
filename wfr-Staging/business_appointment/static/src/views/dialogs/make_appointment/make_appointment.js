/** @odoo-module **/

import { _lt } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, onMounted, onWillUnmount } from "@odoo/owl";
import { useChildRef } from "@web/core/utils/hooks";
import { useService } from "@web/core/utils/hooks";
import { View } from "@web/views/view";


export class MakeAppointmentDialog extends Component {
    /*
    * Re-write to import required services and update props on the component start
    */
    setup() {
        super.setup();
        this.modalRef = useChildRef();
        this.rpc = useService("rpc");
        const buttonTemplate = "business_appointment.MakeAppointmentDialog.buttons";
        this.viewProps = {
            type: "form",
            buttonTemplate: buttonTemplate,
            context: this.props.context || {},
            display: { controlPanel: false },
            mode: "edit",
            resId: this.props.resId || false,
            resModel: this.props.resModel,
            viewId: this.props.viewId || false,
            preventCreate: false,
            preventEdit: false,
            discardRecord: () => {
                this.props.close();
            },
        };
        this.chosenComponents = [];
        onMounted(() => {
            // Hide excess buttons
            if (this.modalRef.el.querySelector(".modal-footer").childElementCount > 1) {
                const defaultButton = this.modalRef.el.querySelector(".modal-footer button.o-default-button");
                if (defaultButton) { defaultButton.classList.add("d-none") };
            };
        });
        onWillUnmount(async () => {
            if (this.chosenComponents.length != 0) {
                await this.rpc("/business_appointment/remove", { "reservation_ids": this.chosenComponents });                
            };
            await this.props.onUnmount();
        });
    }
};

MakeAppointmentDialog.template = "business_appointment.MakeAppointmentDialog";
MakeAppointmentDialog.components = { Dialog, View };
MakeAppointmentDialog.props = {
    close: Function,
    resModel: String,
    context: { type: Object, optional: true },
    mode: {
        optional: true,
        validate: (m) => ["edit", "readonly"].includes(m),
    },
    onRecordSaved: { type: Function, optional: true },
    onUnmount: { type: Function, optional: true },
    preventCreate: { type: Boolean, optional: true },
    resId: { type: [Number, Boolean], optional: true },
    title: { type: String, optional: true },
    viewId: { type: [Number, Boolean], optional: true },
    size: Dialog.props.size,
};
MakeAppointmentDialog.defaultProps = {
    onRecordSaved: () => {},
};
