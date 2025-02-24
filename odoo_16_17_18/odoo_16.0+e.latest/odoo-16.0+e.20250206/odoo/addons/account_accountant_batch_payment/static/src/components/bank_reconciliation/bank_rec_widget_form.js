/** @odoo-module **/
import { registry } from "@web/core/registry";
import { BankRecWidgetForm, BankRecWidgetFormController } from "@account_accountant/components/bank_reconciliation/bank_rec_widget_form";

export class BankRecWidgetFormControllerInheritBatchPayments extends BankRecWidgetFormController {

    // @override
    setup() {
        super.setup();

        // Allow the reject wizard to trigger the validate button
        this.bankRecService.useTodoCommand("form-validate-next-action", async () => {
            await this.actionMoveToNext();
            await this.actionRefreshStLineData();
        })
    }

    // @override
    onRecordChanged(){
        super.onRecordChanged();

        const record = this.model.root;

        // Update the selected batch payments.
        let selectedBatchPaymentIds = new Set();
        for(const aml of record.data.selected_batch_payment_ids.records){
            selectedBatchPaymentIds.add(aml.data.id);
        }
        this.stLineState.selectedBatchPaymentIds = selectedBatchPaymentIds;
    }

}

export const BankRecWidgetFormInheritBatchPayments = {
    ...BankRecWidgetForm,
    Controller: BankRecWidgetFormControllerInheritBatchPayments,
}

registry.category("views").add('bank_rec_widget_form', BankRecWidgetFormInheritBatchPayments, { force: true });
