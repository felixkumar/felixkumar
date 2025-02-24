/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";

import { BankRecWidgetFormEmbeddedListModel } from "@account_accountant/components/bank_reconciliation/bank_rec_widget_form_inner_tab_amls";

const { useState, onWillUnmount } = owl;

export class BankRecWidgetFormInnerTabBatchPaymentsRenderer extends ListRenderer {
    setup() {
        super.setup();
        this.bankRecService = useService("bank_rec_widget");
        this.stLineState = useState(this.bankRecService.getStLineState(this.bankRecService.kanbanState.selectedStLineId));
        onWillUnmount(this.saveSearchState);
    }

    /** @override **/
    getRowClass(record) {
        const classes = super.getRowClass(record);
        if (this.stLineState.selectedBatchPaymentIds.has(record.resId)){
            return `${classes} o_rec_widget_list_selected_item`;
        }
        return classes;
    }

    /** @override **/
    async onCellClicked(record, column, ev) {
        if (this.stLineState.selectedBatchPaymentIds.has(record.resId)) {
            await this.bankRecService.trigger("form-todo-command", `remove_new_batch_payment,${record.resId}`);
        } else {
            await this.bankRecService.trigger("form-todo-command", `add_new_batch_payment,${record.resId}`);
        }
    }

    /** Backup the search facets in order to restore them when the user comes back on this view. **/
    saveSearchState() {
        const searchModel = this.env.searchModel;
        this.stLineState.listBatchPaymentsSearchState = JSON.stringify(searchModel.exportState());
    }
}

export const BankRecWidgetFormInnerTabBatchPayments = {
    ...listView,
    Renderer: BankRecWidgetFormInnerTabBatchPaymentsRenderer,
    Model: BankRecWidgetFormEmbeddedListModel,
}

registry.category("views").add("bank_rec_widget_form_batch_payments_list", BankRecWidgetFormInnerTabBatchPayments);
