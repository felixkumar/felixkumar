/** @odoo-module **/

import { _lt } from "@web/core/l10n/translation";
import { TimeSlots } from "@business_appointment/components/time_slots/time_slots";
import { ComponentWrapper } from "web.OwlCompatibility";
import publicWidget from "web.public.widget";
import rpc from "web.rpc";

var existingTimer = false;
/*
* The method to conver seconds to time duration format
*/
function returnTimeString(second_interval) {
    var finalTime = "";
    const days = Math.floor(second_interval / (3600*24))
    if (days != 0) { finalTime += days + _lt("d ") };
    const hours = Math.floor(second_interval % (3600*24) / 3600);
    if (days != 0 || hours != 0) { finalTime += hours + _lt("h ") }
    const mins = Math.floor(second_interval % 3600 / 60);
    if (days != 0 || hours !=0 || mins != 0) { finalTime += mins + _lt("m ") }
    finalTime += Math.floor(second_interval % 60) + _lt("s ");
    return finalTime;
};
/*
* The method to re-organize the time visible parts as expired
*/
function makeTimerExpired() {
    $(".business-appointment-prereservation-timer-normal").addClass("business-appointment-hidden");
    $(".business-appointment-prereservation-timer-expired").removeClass("business-appointment-hidden");
    $(".business-appointment-prereservation-timer-container").removeClass("alert-info").addClass("alert-danger");
};
/*
* The method to re-organize the timer visible parts as not expired
*/
function makeTimeNormal() {
    $(".business-appointment-prereservation-timer-normal").removeClass("business-appointment-hidden");
    $(".business-appointment-prereservation-timer-expired").addClass("business-appointment-hidden");
    $(".business-appointment-prereservation-timer-container").removeClass("alert-danger").addClass("alert-info");
};
/*
* The method to launch pre-reservation timer
*/
function launchPreTimeer(leftPreTime, preTimer) {
    const timeAlert = $("#business-appointment-prereservation-timer");
    if (existingTimer) { clearInterval(existingTimer) };
    if (!leftPreTime || leftPreTime == 0) { timeAlert.addClass("business-appointment-hidden") }
    else {
        if (leftPreTime > 0) {
            makeTimeNormal();
            existingTimer = setInterval(function () {
                preTimer[0].innerHTML = returnTimeString(leftPreTime);
                if (leftPreTime <= 0) {
                    makeTimerExpired();
                    clearInterval(existingTimer);
                    const reloadPage = function() { window.location.reload() };
                    setTimeout(reloadPage, 5000);
                    preTimer[0].id = "-1";
                };
                leftPreTime -= 1;
            }, 1000)
        }
        else { makeTimerExpired() };
        timeAlert.removeClass("business-appointment-hidden");
    };
};
/*
* Slots widget
*/
publicWidget.registry.timeSlotsContainer = publicWidget.Widget.extend({
    selector: ".business-appointment-website-slots",
    /*
    * Overwrite to load required for the widget params
    */
    willStart: function () {
        return Promise.all([this._super.apply(this, arguments), this._get_session_params()]);
    },
    /*
    * The method to retrieve session params requried for the slots component
    */
    async _get_session_params() {
        this.sessionVals = await rpc.query({ route: "/appointments/get/session" });
        Object.assign(this.sessionVals, {
            onSlotReserved: this.onSlotReserved.bind(this),
            onSlotChange: this.onSlotChange.bind(this),
        });
    },
    /*
    * Re-write to initiate the time slots component
    */
    async start() {
        this.component = new ComponentWrapper(this, TimeSlots, this.sessionVals)
        this.component.mount(this.$("#business-appointment-time-slots-widget")[0]);
    },
    /*
    * The method to add/cancel slot reservation
    */
    async onSlotChange(coreId, chosenComponents, remove=false) {
        await rpc.query({ route: "/appointments/prereserve", params: { core_id: coreId, remove: remove } });
        this._resetPreTimer(remove);
    },
    /*
    * The method to finalize slot reservations
    */
    async onSlotReserved(coreIds, onSlotRemoved) {
        window.location = "/appointments/5?progress_step=5";
    },
    /*
    * The method to trigger timer update if necessary
    * Note: we should always make rpc, since in case even timer is not set, we check whether we should get back from confirmation
    */
    async _resetPreTimer(remove) {
        const timeLeft = await rpc.query({ route: "/appointments/prereservation_timer" });
        if (timeLeft !== false) {
            const timeAlert = $("#business-appointment-prereservation-timer");
            if (timeAlert) {
                const hiddenNow = timeAlert.hasClass("business-appointment-hidden");
                if ( (remove && !hiddenNow) || (!remove && hiddenNow) ) {
                    const preTimer = $(".business-appointment-prereservation-clock");
                    if (preTimer && preTimer.length > 0) {
                        launchPreTimeer(timeLeft, preTimer);
                    };
                };
            };
        }
        else {
            window.location = "/appointments/4?progress_step=4";
        };
    },

});
/*
* Prereservation timer widget
*/
publicWidget.registry.preservationClock = publicWidget.Widget.extend({
    selector: "#business-appointment-prereservation-timer",
    start: function () {
        const preTimer = $(".business-appointment-prereservation-clock");
        launchPreTimeer(parseInt(preTimer[0].id), preTimer);
    },
});
/*
* Confirmation Clock Timer
*/
publicWidget.registry.resendTimer = publicWidget.Widget.extend({
    selector: ".business-appointment-confirmation-timer",
    start: function () {
        const resendTimer = $("span.business-appointment-confirmation-resend");
        var leftTime = parseInt(resendTimer[0].id) - 1;
        if (leftTime >= 0) {
            const resendInterval = setInterval(function () {
                resendTimer[0].innerHTML = leftTime + _lt(" seconds");
                if (leftTime <= 0) {
                    $(".business-appointment-confirmation-resend").removeClass("business-appointment-hidden");
                    $(".business-appointment-confirmation-timer").addClass("business-appointment-hidden");
                    clearInterval(resendInterval);
                }
                leftTime -= 1;
            }, 1000);
        }
        else {
            $(".business-appointment-confirmation-resend").removeClass("business-appointment-hidden");
            $(".business-appointment-confirmation-timer").addClass("business-appointment-hidden");
        };
    },
});
/*
* Full details button on grid
*/
publicWidget.registry.baFullDetailsLink = publicWidget.Widget.extend({
    selector: ".business-appointment-website-grid",
    events: {
        "click .business-appointment-website-grid-box": "_onSchedule",
        "click .business-appointment-website-grid-full-details": "_onOpenFullDetails",
    },
    /*
    * The method to select an item for scheduling
    */
    _onSchedule: function(event) {
        window.location.href = event.currentTarget.id;
    },
    /*
    * The method to open the fill details page
    */
    _onOpenFullDetails: function (event) {
        event.preventDefault();
        event.stopPropagation();
        window.open(event.currentTarget.id);
    },
});
/*
* Cancel re-schedulement process
*/
publicWidget.registry.rescheduleCancel = publicWidget.Widget.extend({
    selector: ".business-appointment-website-cancel-container",
    events: { "click .business-appointment-website-cancel": "_onRemoveReschedulementBtn" },
    async _onRemoveReschedulementBtn(event) {
        await rpc.query({
            route: "/my/business/appointments/cancel_reschedule",
            params: { appointment_id: parseInt(event.currentTarget.id) }
        });
        window.location.reload();
    },
});
