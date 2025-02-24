/** @odoo-module **/

/** @odoo-module **/

import { listView } from '@web/views/list/list_view';
import { registry } from "@web/core/registry";
import { ListController } from "@web/views/list/list_controller";
import { StockReportSearchModel } from "@stock/views/search/stock_report_search_model";
import { StockReportSearchPanel } from '@stock/views/search/stock_report_search_panel';



class OpenDailyStockController extends ListController {

    setup() {
        super.setup()
    }

    _openDailyReportAction() {
        var vals = {
                    report_date: this.props.context.report_date || false,
        };
        if (this.props.context.default_warehouse_id)
        {
            console.log(this.props.context.default_warehouse_id);
            vals['default_warehouse_id'] = this.props.context.default_warehouse_id;
        }
        if (this.props.context.default_categ_id)
        {
            vals['default_categ_id'] = this.props.context.default_categ_id;
        }
        this.actionService.doAction("warehouse_inventory_report.action_open_daily_stock_report", {
            additionalContext: vals,
        });
    }
};

export const StockReportListView = {
    ...listView,
    SearchModel: StockReportSearchModel,
    SearchPanel: StockReportSearchPanel,
    Controller: OpenDailyStockController,
    buttonTemplate: "warehouse_inventory_report.ButtonOpenDailyReport.buttons",
};

registry.category("views").add("stock_report_list_view_ext", StockReportListView);
