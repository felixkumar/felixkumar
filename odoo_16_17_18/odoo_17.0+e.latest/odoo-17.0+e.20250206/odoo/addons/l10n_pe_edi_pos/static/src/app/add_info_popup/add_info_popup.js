/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useState } from "@odoo/owl";

export class AddInfoPopup extends AbstractAwaitablePopup {
    static template = "l10n_pe_edi_pos.AddInfoPopup";

    setup() {
        super.setup();
        this.pos = usePos();
        this.state = useState({
            l10n_pe_edi_refund_reason: this.props.order.l10n_pe_edi_refund_reason || "01",
        });
    }

    async getPayload() {
        return this.state;
    }
}
