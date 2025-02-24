/** @odoo-module **/

import { _lt } from "@web/core/l10n/translation";
import { ChosenAppointments } from "@business_appointment/components/chosen_appointments/chosen_appointments";
import { DatePicker } from "@web/core/datepicker/datepicker";
import { formatDate, parseDate } from "@web/core/l10n/dates";
import { formatFloatTime } from "@business_appointment/components/time_slots/formatters";
import { SuggestedProductsDialog } from "@business_appointment/components/suggested_products/suggested_products";
import { useService } from "@web/core/utils/hooks";

const { Component, onWillStart, onWillUpdateProps, useState } = owl;
const SERVER_DATE_FORMAT = "yyyy-MM-dd";


export class TimeSlots extends Component {
    /*
    * Re-write to import required services and update props on the component start
    */
    setup() {
        this.state = useState({
            dateSlots: null,
            dateStart: null,
            dateEnd: null,
            tzOptions: null,
            defaultTz: null,
            activeYear: null,
            activeMonth: null,
            tzInfo: {
                timeZoneOffset: -(new Date().getTimezoneOffset()),
                timeZoneName: Intl.DateTimeFormat().resolvedOptions().timeZone,
            },
            chosenAppointments: [],
        });
        this.appointmentVals = {};
        this.slotTitle = "";
        this.activeYear = null;
        this.activeMonth = null;
        this.originServiceId = null;
        this.rpc = useService("rpc");
        this.dialogService = useService("dialog");
        onWillStart(async () => {
            await this._getAppointmentDetaults(this.props); // influence calculation, so should be finished before that
            await this._calculateSlots(this.props);
        });
        onWillUpdateProps(async (nextProps) => {
            await this._calculateSlots(nextProps);
        })
    }
    /*
    * The method to get the current locale
    */
    get thisLocale() {
        return moment.locale()
    }
    /*
    * Getter for the dateStartLocal to parse the dateStart in the correct locale
    */
    get dateStartLocal() {
        return this.state.dateStart ? parseDate(this.state.dateStart) : false;
    }
    /*
    * Getter for the dateEndLocal to parse the dateEnd in the correct locale
    */
    get dateEndLocal() {
        return this.state.dateEnd ? parseDate(this.state.dateEnd) : false;
    }
    /*
    * The method to prepare ChosenAppointments
    */
    getChosenAppointmentsProps() {
        return {
            scheduling: true,
            chosenAppointments: this.state.chosenAppointments,
            onSlotReserved: this.onSlotReserved.bind(this),
            onSlotRemoved: this.onSlotRemoved.bind(this),
            manageRpc: this.manageRpc.bind(this),
        }
    }
    /*
    * The method to get default values from props (if sent) or calculate those (otherwise)
    */
    async _getAppointmentDetaults(props) {
        const appointmentDefaults = await this.manageRpc("/business_appointment/defaults");
        Object.assign(this.state, {
            dateStart: props.dateStart ? props.dateStart : appointmentDefaults.date_start,
            dateEnd: props.dateEnd ? props.dateEnd : appointmentDefaults.date_end,
            numberOfAppointments: props.appointmentId ? 1 : props.numberOfAppointments,
            chosenAppointments: props.chosenAppointments || [],
        });
    }
    /*
    * The method to calculate slots based on the props
    */
    async _calculateSlots(props) {
        if (!props.resourceTypeID || !props.serviceID) {
            return
        };
        var resourceIDS = [];
        if (props.autoResources) {
            resourceIDS = await this.manageRpc(
                "/business_appointment/auto/resources", { resource_type_id: props.resourceTypeID }
            );
        }
        else { resourceIDS = props.resourceIDS };
        if (resourceIDS.length == 0) {
            return
        };
        if (props.serviceID != this.originServiceId) {
            const durationVals = await this.manageRpc(
                "/business_appointment/duration",
                { service_id: props.serviceID, preduration: props.calendarDuration || false },
            );
            Object.assign(this.state, durationVals);
            this.originServiceId = props.serviceID;
        };
        const timeSlotsDict = await this.manageRpc(
            "/business_appointment/slots",
            {
                resource_type_id: props.resourceTypeID,
                resource_ids: resourceIDS,
                service_id: props.serviceID,
                duration: this.state.duration_uom == "hours" ? this.state.duration : this.state.duration * 24,
                date_start: this.state.dateStart,
                date_end: this.state.dateEnd,
                active_month: this.activeMonth,
                active_year: this.activeYear,
                tz_info: this.state.tzInfo,
                chosen_cores: this.state.chosenAppointments,
            },
        );
        this._setActiveYearAndMonth(timeSlotsDict)
        Object.assign(this.state, {
            dateSlots: timeSlotsDict.day_slots,
            tzOptions: timeSlotsDict.tz_options,
            defaultTz: timeSlotsDict.default_tz,
            activeMonth: this.activeMonth,
            activeYear: this.activeYear,
            uniqueMonths: timeSlotsDict.unique_months,
            uniqueYears: timeSlotsDict.unique_years,
            chosenAppointments: timeSlotsDict.chosen_cores,
        });
        $("html,body").animate({ scrollTop: 0 }, 400);
        $(".modal-body").animate({ scrollTop: 0 }, 400);
    }
    /*
    * The method to reserve the slot
    */
    async _onAddSlot(slotTitle, dateTimeStart, resourceIds, extraIds=false) {
         if (this.state.numberOfAppointments != 1 && this.state.chosenAppointments.length >= this.state.numberOfAppointments) {
            return this._showWarning(
                _lt("The maximum number of appointments is reached"),
                _lt("Sorry, you can not schedule more appointments. The maximum number is reached"),
            );
        };
        var reservation_for_group_id = false;
        if (this.state.numberOfAppointments != 1 && this.state.chosenAppointments.length != 0) {
            reservation_for_group_id = this.state.chosenAppointments[0].id;
        };
        this.appointmentVals = {
            from_website_id: this.props.fromWebsite,
            start_utc: dateTimeStart,
            duration: this.state.duration_uom == "hours" ? this.state.duration : this.state.duration * 24, 
            service_id: this.props.serviceID,
            resource_ids_list: resourceIds,
            reservation_for_group_id: reservation_for_group_id,
            pricelist_id: this.props.pricelistID,
            extra_ids_list: extraIds,
            tz_info: this.state.tzInfo,
        };
        this.slotTitle = slotTitle;
        const suggestedProducts = await this.manageRpc(
            "/business_appointment/suggested_products",
            {
                service_id: this.props.serviceID,
                from_website_id: this.props.fromWebsite,
                appointment_id: this.props.appointmentId,
                pricelist_id: this.props.pricelistID,
            }
        );
        if (suggestedProducts) {
            this.dialogService.add(SuggestedProductsDialog, {
                suggestedProducts: suggestedProducts,
                fromWebsite: this.props.fromWebsite,
                pricelist: this.props.pricelistID,
                manageRpc: this.manageRpc.bind(this),
                finishReservation: this._finishReservation.bind(this),
            });
        }
        else {
            this._finishReservation(false);
        };
    }
    /*
    * The method to finalize slot reservations and move forward
    */
    async _finishReservation(suggestedProducts) {
        this.appointmentVals.extra_product_ids = suggestedProducts;
        this.appointmentVals.reschedule_id = this.props.appointmentId;
        const creationResult = await this.manageRpc("/business_appointment/add", this.appointmentVals);
        if (creationResult) {
            if (this.state.numberOfAppointments == 1 && this.state.chosenAppointments.length != 0) {
                // if only a single appointment is possible (including reschedule) > remove old one firstly
                const toRemovePreReservation = this.state.chosenAppointments[0].id
                await this.manageRpc("/business_appointment/remove", { "reservation_ids": [toRemovePreReservation] });
                await this.onSlotRemoved(toRemovePreReservation);
            };
            this.state.chosenAppointments.push({ id: creationResult.id, title: creationResult.resource_name + ": " + this.slotTitle });
            await this.props.onSlotChange(creationResult.id, this.state.chosenAppointments, false);
            if (this.state.chosenAppointments.length >= this.state.numberOfAppointments) {
                await this.onSlotReserved(this.state.chosenAppointments);
            };
            await this._calculateSlots(this.props);
        }
        else if (creationResult === false) {
            await this._calculateSlots(this.props);
            return this._showWarning(
                _lt("Sorry, this time slot has been just reserved or there are overlapping reservations for the same contact"),
                _lt("Please try another one"),
            );
        }
        else {
            await this._calculateSlots(this.props);
            return this._showWarning(
                _lt("Sorry, but you do not have enough rights to schedule an appointment for this resource"),
                _lt("Please contact your system administrator"),
            );
        }
    }
    /*
    * The method to finish slots reservation and move forward
    */
    async onSlotReserved(coreIds) {
        await this.props.onSlotReserved(this.state.chosenAppointments, this.onSlotRemoved.bind(this));
    }
    /*
    * The method to unreserve the slot
    */
    async onSlotRemoved(coreId) {
        this.state.chosenAppointments = this.state.chosenAppointments.filter(rec => rec.id != coreId);
        await this.props.onSlotChange(coreId, this.state.chosenAppointments, true);
        await this._calculateSlots(this.props);
    }
    /*
    * The method to process the period start change
    */
    async _onDateStartChange(date) {
        this.state.dateStart = date ? formatDate(date, { format: SERVER_DATE_FORMAT }) : false;
        await this._calculateSlots(this.props);
    }
    /*
    * The method to process the period end change
    */
    async _onDateEndChange(date) {
        this.state.dateEnd = date ? formatDate(date, { format: SERVER_DATE_FORMAT }) : false;
        await this._calculateSlots(this.props);
    }
    /*
    * The method to process the duration change
    */
    async _onChangeDuration(event) {
        this.state.duration = parseFloat(event.currentTarget.value);
        await this._calculateSlots(this.props);
    }
    /*
    * The method to process the timezone change
    */
    async _onChangeTz(event) {   
        this.state.tzInfo = { targetTz : event.currentTarget.value };
        await this._calculateSlots(this.props);
    }
    /*
    * The method to process the year change
    */
    async _onChangeYear(event) {
        this.activeYear = event.currentTarget.value;
        this.activeMonth = null;
        await this._calculateSlots(this.props);
    }
    /*
    * The method to process the month change
    */
    async _onChangeMonth(chosenMonth) {
        this.activeMonth = chosenMonth;
        await this._calculateSlots(this.props);
    }
    /*
    * The method to assign active year and month
    */
    _setActiveYearAndMonth(timeSlotsDict) {
        this.activeMonth = timeSlotsDict.active_month;
        if (timeSlotsDict.unique_years) {
            if (!this.activeYear || (this.activeYear && !timeSlotsDict.unique_years.includes(parseInt(this.activeYear)))) {
                this.activeYear = timeSlotsDict.unique_years[0]
            }
        }
        else { this.activeYear = false }
    }
    /*
    * The wrapper method for the rpc since it might be triggered both from legacy (fromWebsite) and OWL
    */
    async manageRpc(route, params = {}) {
        if (this.props.fromWebsite) { return await this.rpc({ route: route, params: params }) }
        else { return await this.rpc(route, params) };
    }
    /*
    * The method to convert date to a localized date
    */
    constructDate(target_date, date_format) {
        const resDate = new Date(target_date);
        if (date_format == "year") { return resDate.getUTCFullYear() }
        else if (date_format == "month") { return moment.monthsShort()[resDate.getUTCMonth()] }
        else if (date_format == "weekday") { return moment.weekdaysShort()[resDate.getUTCDay()] }
    }
    /*
    * The method to make time option in selections nice looking
    */
    formatDuration(value) {
        return this.state.duration_uom == "hours" ? formatFloatTime(value) : value
    }
    /*
    * The method to show browser alert
    */
    _showWarning(title, message) {
        alert(title + "\n" + message);
    }
};

TimeSlots.components = { ChosenAppointments, DatePicker };
TimeSlots.template = "business_appointment.TimeSlots";
