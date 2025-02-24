/** @odoo-module **/
import { ForecastedDetails } from "@stock/stock_forecasted/forecasted_details";
import { patch } from '@web/core/utils/patch';
import { useService } from "@web/core/utils/hooks";
import { useState, onWillStart } from "@odoo/owl";


patch(ForecastedDetails.prototype, 'wfr_changes_ls.ForecastedDetails_js',{
    setup() {
        this._super.apply()
        this.user = useService("user");
        this.canSeeBut = false;

        onWillStart(async () => {
            let has_group = await this.user.hasGroup('user_warehouse_restriction.user_carote_restriction_group_user');
            this.canSeeBut = has_group == false;
        })
  }
});