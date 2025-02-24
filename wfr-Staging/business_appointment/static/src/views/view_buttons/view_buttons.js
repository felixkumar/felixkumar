/** @odoo-module **/

import { _lt } from "@web/core/l10n/translation";
import { MakeAppointmentDialog } from "@business_appointment/views/dialogs/make_appointment/make_appointment";
import { useService } from "@web/core/utils/hooks";


async function onReloadParent(parentRef) {
    if (parentRef.model) { await parentRef.model.load() }
    else { await parentRef.load() };
};

export function viewButtons(parentRef) {
    /*
    * The function to prepare methods and params common to all appointment controllers
    */
    const dialogService = useService("dialog");
    const orm = useService("orm");
    return {
        dialogService,
        startScheduling: async (localCtx = false) => {
            const dialogContext = localCtx || parentRef.getAppointmentsContext();
            if (dialogContext.default_appointment_id) {
                await onReloadParent(parentRef);
                const allowed = await orm.call(
                    "business.appointment", "check_access_rule", [[dialogContext.default_appointment_id], "write"],
                );
            };
            const dialogTitle = dialogContext.default_appointment_id ? _lt("Reschedule Appointment") : _lt("Schedule Appointment");
            dialogService.add(MakeAppointmentDialog, {
                resModel: "make.business.appointment",
                title: dialogTitle,
                context: dialogContext,
                onRecordSaved: async (formRecord) => { await onReloadParent(parentRef) },
                onUnmount: async() => { await onReloadParent(parentRef) },
            });
        },
    }
}
