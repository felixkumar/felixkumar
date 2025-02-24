/** @odoo-module **/

import { BankRecWidget } from "@account_accountant/components/bank_reconciliation/bank_rec_widget_service";
import { patch } from '@web/core/utils/patch';


patch(BankRecWidget.prototype, "account_accountant_batch_payment", {

    // @override
    getDefaultStLineState(){
        return {
            ...this._super(),
            selectedBatchPaymentIds: new Set(),
            listBatchPaymentsSearchState: null,
        }
    },

    // @override
    getSearchState(stLineId, modelName) {
        if (modelName === 'account.batch.payment') {
            return { searchModel: this.stLineStates[stLineId].listBatchPaymentsSearchState };
        } else {
            return this._super(...arguments);
        }
    }

});
