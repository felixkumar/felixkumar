/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { qrCodeSrc } from "@point_of_sale/utils";

patch(PaymentScreen.prototype, {
    async _postPushOrderResolve(order, order_server_ids) {
        if (this.pos.config.is_kenyan) {
            this.env.services.ui.block();
            try {
                await this.orm.call(
                    "pos.order",
                    "action_post_order",
                    [order_server_ids],
                    {}
                );
            } catch (error) {
                this.popup.add(ErrorPopup, {
                    title: _t("Error"),
                    body: _t(error.data.message),
                });
            } finally {
                const l10n_ke_edi_oscu_pos_data = await this.orm.call(
                    "pos.order",
                    "get_l10n_ke_edi_oscu_pos_data",
                    [order_server_ids],
                    {}
                );

                order.l10n_ke_edi_oscu_pos_qrsrc = l10n_ke_edi_oscu_pos_data.l10n_ke_edi_oscu_pos_qrurl ? qrCodeSrc(l10n_ke_edi_oscu_pos_data.l10n_ke_edi_oscu_pos_qrurl) : undefined;
                order.l10n_ke_edi_oscu_pos_date = l10n_ke_edi_oscu_pos_data.l10n_ke_edi_oscu_pos_date;
                order.l10n_ke_edi_oscu_pos_receipt_number = l10n_ke_edi_oscu_pos_data.l10n_ke_edi_oscu_pos_receipt_number;
                order.l10n_ke_edi_oscu_pos_internal_data = l10n_ke_edi_oscu_pos_data.l10n_ke_edi_oscu_pos_internal_data;
                order.l10n_ke_edi_oscu_pos_signature = l10n_ke_edi_oscu_pos_data.l10n_ke_edi_oscu_pos_signature;
                order.l10n_ke_edi_oscu_pos_order_json = l10n_ke_edi_oscu_pos_data.l10n_ke_edi_oscu_pos_order_json;
                order.l10n_ke_edi_oscu_pos_serial_number = l10n_ke_edi_oscu_pos_data.l10n_ke_edi_oscu_pos_serial_number;
                order.refunded_order_ids = l10n_ke_edi_oscu_pos_data.refunded_order_ids;

                this.env.services.ui.unblock();
            }
        }

        return super._postPushOrderResolve(...arguments);
    },

    async validateOrder(isForceValidate) {
        if (this.pos.config.is_kenyan) {
            let errorMessage = "";
            const unregisteredProducts = this.currentOrder.get_orderlines().filter((line) => !line.product.checkEtimsFields())

            if (unregisteredProducts.length > 0) {
                errorMessage += _t(
                    "All product have to be registered to eTIMS, you can register them in the product view.\n"
                );
            }

            if (
                ![0, this.currentOrder.get_orderlines().length].includes(
                    this.currentOrder
                        .get_orderlines()
                        .filter((line) => line.refunded_orderline_id !== undefined).length
                )
            ) {
                errorMessage += _t("You can't mix refund lines and order lines.\n");
            }

            if (errorMessage) {
                this.popup.add(ErrorPopup, {
                    title: _t("Error"),
                    body: _t(errorMessage),
                });
                return false;
            }
        }

        await super.validateOrder(isForceValidate);
    },

    shouldDownloadInvoice() {
        return this.pos.config.is_kenyan ? false : super.shouldDownloadInvoice();
    },
});
