/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    //@override
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        if (this.pos.company.account_fiscal_country_id.code === "PE") {
            json["l10n_pe_edi_refund_reason"] = this.l10n_pe_edi_refund_reason;
        }
        return json;
    },
});
