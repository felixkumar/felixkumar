/** @odoo-module **/

import {
    formatDate,
    formatDateTime,
    parseDate,
    parseDateTime,
    strftimeToLuxonFormat,
    serializeDate,
    serializeDateTime,
    deserializeDate,
    deserializeDateTime,
    momentToLuxon,
    luxonToMoment,
} from "@web/core/l10n/dates";

import { PortalChatter } from 'portal.chatter';
import time from "web.time";
import { qweb , _t } from "web.core";

const { DateTime, Settings } = luxon;


/**
 * PortalChatter
 *
 * Include Frontend Chatter to handle rating
 */
PortalChatter.include({

    /**
     * Update the messages format
     *
     * @param {Array<Object>} messages
     * @returns {Array}
     */
    preprocessMessages: function (messages) {
        var self = this;
        messages = this._super.apply(this, arguments);
        _.each(messages, function (m) {
            const oneDay = 24 * 60 * 60 * 1000 ;
            const date = new Date();
            const m_date = new Date(m.date);
            const diffDays = Math.floor(Math.abs(date.getTime() - m_date.getTime())/oneDay) ;
            const diffweeks = Math.floor(diffDays / 7);
            const diffYears = Math.abs(date.getFullYear() - m_date.getFullYear());
            const diffMonths = (date.getFullYear() - m_date.getFullYear()) * 12 + (date.getMonth() - m_date.getMonth());

            if (diffDays == 0){
                m['message_day_from_today'] = 'Today';
            }
            else if (diffDays != 0 && diffDays < 7){
                m['message_day_from_today'] = _.str.sprintf(_t('%s days ago'), diffDays);
            }
            else if(diffDays >= 7 && diffweeks && diffweeks < 4){
                m['message_day_from_today'] = _.str.sprintf(_t('%s week ago'), diffweeks);
            }
            else if(diffweeks > 4 && diffMonths && diffMonths < 12){
                m['message_day_from_today'] = _.str.sprintf(_t('%s month ago'), diffMonths);
            }
            else{
                m['message_day_from_today'] = _.str.sprintf(_t('%s year ago'), diffYears);
            }
        });
        // save messages in the widget to process correctly the publisher comment templates
        this.messages = messages;
        return messages;
    },
});
