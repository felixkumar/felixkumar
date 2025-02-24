/** @odoo-module **/

import { onWillStart } from "@odoo/owl";
import { TimesheetLeaderboard } from "@sale_timesheet_enterprise/components/timesheet_leaderboard/timesheet_leaderboard";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";

export function patchRenderer(Renderer) {
    patch(Renderer.components, { TimesheetLeaderboard });
    patch(Renderer.prototype, {
        setup() {
            super.setup()
            const user = useService('user');
            const orm = useService('orm');
            onWillStart(async () => {
                const [userHasBillingRateGroup, showLeaderboard, result] = await Promise.all([
                    user.hasGroup('sale_timesheet_enterprise.group_timesheet_leaderboard_show_rates'),
                    user.hasGroup('sale_timesheet_enterprise.group_use_timesheet_leaderboard'),
                    orm.call("hr.employee", "get_billable_time_target", [[user.userId]]),
                ])
                this.userHasBillingRateGroup = userHasBillingRateGroup;
                this.showLeaderboard = showLeaderboard;
                const billableTimeTarget = result.length ? result[0].billable_time_target : 0;
                this.showIndicators = billableTimeTarget > 0;
                this.showLeaderboardComponent = (this.userHasBillingRateGroup && this.showIndicators) || this.showLeaderboard;
            });
        },

        get isMobile() {
            return this.env.isSmall;
        },
    });
}
