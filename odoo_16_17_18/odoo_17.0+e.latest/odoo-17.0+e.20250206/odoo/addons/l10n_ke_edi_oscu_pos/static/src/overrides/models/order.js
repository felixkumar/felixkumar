/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    //@override
    export_for_printing() {
        return {
            ...super.export_for_printing(...arguments),
            l10n_ke_edi_oscu_pos_qrsrc: this.l10n_ke_edi_oscu_pos_qrsrc,
            l10n_ke_edi_oscu_pos_date: this.l10n_ke_edi_oscu_pos_date,
            l10n_ke_edi_oscu_pos_receipt_number: this.l10n_ke_edi_oscu_pos_receipt_number,
            l10n_ke_edi_oscu_pos_internal_data: this.l10n_ke_edi_oscu_pos_internal_data,
            l10n_ke_edi_oscu_pos_signature: this.l10n_ke_edi_oscu_pos_signature,
            l10n_ke_edi_oscu_pos_order_json: this.l10n_ke_edi_oscu_pos_order_json,
            l10n_ke_edi_oscu_pos_serial_number: this.l10n_ke_edi_oscu_pos_serial_number,
            refunded_order_ids: this.refunded_order_ids,
        };
    },

    wait_for_push_order() {
        return this.pos.config.is_kenyan ? true : super.wait_for_push_order(...arguments);
    },
});
