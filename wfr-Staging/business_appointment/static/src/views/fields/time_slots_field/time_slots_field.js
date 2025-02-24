/** @odoo-module **/

import { _lt } from "@web/core/l10n/translation";
import { ChooseCustomerDialog } from "@business_appointment/views/dialogs/choose_customer/choose_customer";
import { MakeAppointmentDialog } from "@business_appointment/views/dialogs/make_appointment/make_appointment";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { TimeSlots } from "@business_appointment/components/time_slots/time_slots";

const { Component, onMounted, onPatched, onWillStart } = owl;


export class TimeSlotsField extends Component {
    /*
    * Re-write to import required services and update props on the component start
    */
    setup() {
        this.dialogService = useService("dialog");
        this.orm = useService("orm");
    }
    /*
    * The getter method to get MakeAppointmentDialog
    */
    get appointmentDialog() {
        var parentRef = this.__owl__.parent;
        while (parentRef && parentRef.component && !(parentRef.component instanceof MakeAppointmentDialog)) {
            parentRef = parentRef.parent;
        };
        return parentRef
    }
    /*
    * The getter method to get appointment_id
    */
    get appointmentId() {
        return this._convertFormData("many2one", this.props.record.data.appointment_id)
    }
    /*
    * The getter method to get appointment_id
    */
    get pricelistId() {
        return this._convertFormData("many2one", this.props.record.data.pricelist_id)
    }
    /*
    * The method to prepare TimeSlots props
    */
    getTimeSlotsProps() {
        const recordData = this.props.record.data;
        return {
            fromWebsite: false,
            resourceTypeID: this._convertFormData("many2one", recordData.resource_type_id),
            resourceIDS: this._convertFormData("many2many", recordData.resource_ids),
            serviceID: this._convertFormData("many2one", recordData.service_id),
            pricelistID: this.pricelistId,
            dateStart: this.props.record.context.default_date_start,
            dateEnd: this.props.record.context.default_date_end,
            calendarDuration: this.props.record.context.default_duration,
            appointmentId: this.appointmentId,
            numberOfAppointments: recordData.number_of_appointments,
            autoResources: recordData.allocation_type == "automatic",
            onSlotReserved: this.onSlotReserved.bind(this),
            onSlotChange: this.onSlotChange.bind(this),
        }
    }
    /*
    * The method to add or cancel slot reservation
    */
    async onSlotChange(coreId, chosenComponents, remove=false) {
        this.appointmentDialog.component.chosenComponents = chosenComponents.map(rec => rec.id);
    }
    /*
    * The method to finalize slots reservation and move forward
    */
    async onSlotReserved(coreIds, onSlotRemoved) {
        const preReservations = coreIds.map(rec => rec.id);
        const resourceTypes = await this.orm.call("choose.appointment.customer", "action_return_resource_types", [preReservations]);
        this.dialogService.add(ChooseCustomerDialog, {
            resModel: "choose.appointment.customer",
            title: _lt("Confirm Reservation"),
            context: {
                default_appointment_id: this.appointmentId,
                default_pricelist_id: this.pricelistId,
                default_resource_type_id: [[6, 0, resourceTypes]],
                default_partner_id: this.env.searchModel.globalContext.default_partner_id,
            },
            chosenAppointments: coreIds,
            onParentSlotRemoved: onSlotRemoved,
            onRecordSaved: async (formRecord) => {
                if (this.appointmentDialog) {
                    this.appointmentDialog.component.chosenComponents = [];
                    this.appointmentDialog.props.close();
                    this.appointmentDialog.props.onRecordSaved();
                }; 
            },
        });
    }
    /*
    * The method to convert form data to real ids
    */
    _convertFormData(fieldType, fieldValue) {
        if (fieldType == "many2one") {
            return fieldValue && fieldValue.length != 0 ? fieldValue[0] : false  
        }
        else if (fieldType == "many2many") {
            return fieldValue.records.map((record) => record.resId);
        };
    }
};

TimeSlotsField.components = { TimeSlots };
TimeSlotsField.supportedTypes = ["char"];
TimeSlotsField.template = "business_appointment.TimeSlotsField";
TimeSlotsField.props = { ...standardFieldProps };
registry.category("fields").add("timeSlotsWidget", TimeSlotsField);
