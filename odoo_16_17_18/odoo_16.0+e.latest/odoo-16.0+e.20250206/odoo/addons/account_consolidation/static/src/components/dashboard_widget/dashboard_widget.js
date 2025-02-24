/** @odoo-module **/

import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { pick } from "@web/core/utils/objects";

const { Component } = owl;

class ConsolidationDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
    }

    get datas() {
        return JSON.parse(this.props.value);
    }


    async onUnmappedAccountClick(company_id) {
        await this.env.onClickViewButton({
            clickParams: {
                type: "object",
                name: "action_open_mapping",
            },
            getResParams: () => ({
                ...pick(this.props.record, "context", "evalContext", "resModel", "resId", "resIds"),
                context: { company_id: company_id },
            }),
        });
    }    
}
ConsolidationDashboard.template = "account_consolidation.ConsolidatedDashboardTemplate";
ConsolidationDashboard.supportedTypes = ["char"];

registry.category("fields").add("consolidation_dashboard_field", ConsolidationDashboard);
