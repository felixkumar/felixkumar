/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";

export class BankRecBatchRejectFormController extends FormController {
    setup() {
        super.setup();
        this.bankRecService = useService("bank_rec_widget");
    }

    /**
     * @override
     */
    async afterExecuteActionButton(clickParams) {
        if (clickParams.name != "button_cancel") {
            await this.bankRecService.trigger("form-todo-command", `button_clicked,button_validate_no_batch_payment_wizard`);
            await this.bankRecService.trigger("form-validate-next-action");
        }
    }
}

export const BankRecBatchForm = {
    ...formView,
    Controller: BankRecBatchRejectFormController,
}

registry.category("views").add('bank_rec_batch_reject_wizard', BankRecBatchForm);
