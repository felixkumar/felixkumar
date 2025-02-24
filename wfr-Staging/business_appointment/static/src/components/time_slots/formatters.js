/** @odoo-module **/

/*
* We have to copy 'formatFloatTime' from web/views/fields/formatters, since the latter is not available on website
* Otherwise, it might be replace with direct import
*/

export function formatFloatTime(value, options = {}) {
    if (value === false) { return "" };
    const isNegative = value < 0;
    value = Math.abs(value);
    let hour = Math.floor(value);
    const milliSecLeft = Math.round(value * 3600000) - hour * 3600000;
    let min = Math.floor(milliSecLeft / 60000);
    if (min === 60) {
        min = 0;
        hour = hour + 1;
    }
    min = String(min).padStart(2, "0");
    if (!options.noLeadingZeroHour) {
        hour = String(hour).padStart(2, "0");
    }
    let sec = "";
    if (options.displaySeconds) {
        sec = ":" + String(Math.floor((milliSecLeft % 60000) / 1000)).padStart(2, "0");
    }
    return `${isNegative ? "-" : ""}${hour}:${min}${sec}`;
}
