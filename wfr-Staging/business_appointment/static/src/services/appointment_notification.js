/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { ConnectionLostError } from "@web/core/network/rpc_service";
import { registry } from "@web/core/registry";

/*
* Implemented based on standard Odoo calendar notifications
*/
export const appointmentNotification = {
    dependencies: ["action", "bus_service", "notification", "rpc"],
    start(env, { action, bus_service, notification, rpc }) {
        let calendarNotifAppointmentTimeouts = {};
        let nextAppointmentCalendarNotifTimeout = null;
        const displayedAppointmentNotifications = new Set();
        /*
        * Add the bus trigger to show user popup
        */
        bus_service.addEventListener("notification", ({ detail: notifications }) => {
            for (const { payload, type } of notifications) {
                if (type === "alarm.task") { displayAppointmentCalendarNotification(payload) }
            };
        });
        bus_service.start();
        /*
        * Show user popup
        */
        function displayAppointmentCalendarNotification(notifications) {
            let lastNotifTimer = 0;
            browser.clearTimeout(nextAppointmentCalendarNotifTimeout);
            Object.values(calendarNotifAppointmentTimeouts).forEach((notif) => browser.clearTimeout(notif));
            calendarNotifAppointmentTimeouts = {};
            notifications.forEach(function (notif) {
                const key = notif.event_id + "," + notif.alarm_id;
                if (displayedAppointmentNotifications.has(key)) {
                    return;
                }
                calendarNotifAppointmentTimeouts[key] = browser.setTimeout(function () {
                    const notificationRemove = notification.add(notif.message, {
                        title: notif.title,
                        type: "warning",
                        sticky: true,
                        onClose: () => { displayedAppointmentNotifications.delete(key) },
                        buttons: [
                            {
                                name: env._t("OK"),
                                primary: true,
                                onClick: async () => {
                                    await rpc("/business/appointment/alarm/delete", {"alarm_id": notif.alarm_id}, { silent: true });
                                    notificationRemove();
                                },
                            },
                            {
                                name: env._t("Details"),
                                onClick: async () => {
                                    await action.doAction({
                                        type: "ir.actions.act_window",
                                        res_model: "business.appointment",
                                        res_id: notif.event_id,
                                        views: [[false, "form"]],
                                    });
                                    await rpc("/business/appointment/alarm/delete", {"alarm_id": notif.alarm_id}, { silent: true });
                                    notificationRemove();
                                },
                            },
                            {
                                name: env._t("Snooze"),
                                onClick: () => {
                                    notificationRemove();
                                },
                            },
                        ],
                    });
                    displayedAppointmentNotifications.add(key);
                }, notif.timer * 1000);
                lastNotifTimer = Math.max(lastNotifTimer, notif.timer);
            });
            if (lastNotifTimer > 0) {
                nextAppointmentCalendarNotifTimeout = browser.setTimeout(getNextAppointmentCalendarNotif, lastNotifTimer * 1000);
            };
        };
        /*
        * The method to update user popup queue
        */
        async function getNextAppointmentCalendarNotif() {
            try {
                const result = await rpc("/business/appointment/popup/notify", {}, { silent: true });
                displayAppointmentCalendarNotification(result);
            } catch (error) {
                if (!(error instanceof ConnectionLostError)) { throw error };
            }
        }
    },
};

registry.category("services").add("appointmentNotification", appointmentNotification);
