/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget";


patch(OrderWidget.prototype, {
    showUnregisteredProductsWarning(lines) {
        return lines.filter((line) => line.pos?.config.is_kenyan && (!line.product?.checkEtimsFields() || line.tax_ids?.length === 0)).length > 0;
    },
})
