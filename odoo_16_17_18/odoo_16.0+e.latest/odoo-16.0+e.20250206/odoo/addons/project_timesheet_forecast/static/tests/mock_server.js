/** @odoo-module */

import MockServer from 'web.MockServer';

MockServer.include({
    async _performRpc(route, args) {
        if (args.method === "gantt_company_hours_per_day") {
            // by default we say that a company has an average of 8h/day workweek
            return 8;
        } else if (args.method === "gantt_resource_work_interval") {
            // by default we return no work intervals, and no flexible hours
            return [{}, {}];
        }
        return this._super(...arguments);
    }
});
