/** @odoo-module **/

import { _lt } from "@web/core/l10n/translation";
import { ComponentWrapper } from "web.OwlCompatibility";
import { SuggestedProductsDialog } from "@business_appointment/components/suggested_products/suggested_products";
import { useService } from "@web/core/utils/hooks";
import publicWidget from "web.public.widget";
import rpc from "web.rpc";
const { Component, xml } = owl;

/*
* The complementaries button relies on the component to trigger the dialog
*/
export class SuggestedButton extends Component {
    /*
    * Overwrite to add required services and actions
    */
    setup() {
        this.dialogService = useService("dialog");
    }
    /*
    * The method to show the suggested products dialog
    */
    async onShowSuggestedProducts(appointmentId) {
        const result = await this.manageRpc(
            "/my/business/appointments/suggested_products",
            { appointment: appointmentId },
        );
        if (result) {
           this.dialogService.add(SuggestedProductsDialog,  {
                suggestedProducts: result.suggested_products,
                fromWebsite: result.website_id,
                pricelist: result.pricelist_id,
                manageRpc: this.manageRpc.bind(this),
                finishReservation: async(suggestedProducts) => {
                    await this.manageRpc(
                        "/my/business/appointments/suggested_products/update",
                        { appointment: appointmentId, extra_product_ids: suggestedProducts },
                    );
                    window.location.reload();
                },
            });
        }
    }
    async manageRpc(route, params = {}) {
        return await rpc.query({ route: route, params: params });
    }
}
SuggestedButton.template = xml`
    <a role="button" class="btn btn-primary w-100 mb8" href="#" t-on-click="() => this.onShowSuggestedProducts(this.props.appointmentId)">
        <i class="fa fa-edit"/> Complementaries
    </a>`;
/*
* The button to manage complementaries (differs from other buttons to use OWL component)
*/
publicWidget.registry.SuggestedButton = publicWidget.Widget.extend({
    selector: ".business-appoinment-portal-complementaries",
    /*
    * Re-write to initiate the suggested button component
    */
    async start() {
        this.component = new ComponentWrapper(this, SuggestedButton, {"appointmentId": parseInt(this.el.id)})
        this.component.mount(this.el);
    },
});
/*
* Functional buttons for portal (except managing complementaries)
*/
publicWidget.registry.baFunctionalButtons = publicWidget.Widget.extend({
    selector: "#business-appointments-portal-buttons",
    events: {
        "click .business-appoinment-portal-video": "_onJoinConference",
        "click .business-appoinment-portal-repeat": "_onRepeatBtn",
        "click .business-appoinment-portal-reschedule": "_onReScheduleBtn",
        "click .business-appoinment-portal-cancel": "_onCancelAppointment",
    },
    /*
    * Join video button button
    */
    async _onJoinConference(event) {
        const videoRef = rpc.query({
            route: "/my/business/appointments/join_video",
            params: { appointment_id: parseInt(event.currentTarget.id) },
        });
        window.open(videoRef);
    },
    /*
    * Repeat button
    */
    async _onRepeatBtn(event) {
        await rpc.query({
            route: "/my/business/appointments/reschedule",
            params: { appointment_id: parseInt(event.currentTarget.id), should_be_cancelled: false },
        });
        window.open("/appointments/4");
    },   
    /*
    * Reschedule button
    */
    async _onReScheduleBtn(event) {
        await rpc.query({
            route: "/my/business/appointments/reschedule",
            params: { appointment_id: parseInt(event.currentTarget.id), should_be_cancelled: true },
        });
        window.open("/appointments/4");
    },    
    /*
    * Cancel button
    */
    async _onCancelAppointment(event) {
        if (confirm(_lt("Are you sure you want to cancel this appointment?"))) {
            await rpc.query({
                route: "/my/business/appointments/cancel",
                params: { appointment_id: parseInt(event.currentTarget.id) },
            });
            window.location.reload();
        };  
    },
});
