import * as Chrome from "@point_of_sale/../tests/tours/utils/chrome_util";
import * as Dialog from "@point_of_sale/../tests/tours/utils/dialog_util";
import * as ProductScreen from "@point_of_sale/../tests/tours/utils/product_screen_util";
import * as PaymentScreen from "@point_of_sale/../tests/tours/utils/payment_screen_util";
import * as ReceiptScreen from "@point_of_sale/../tests/tours/utils/receipt_screen_util";
import { registry } from "@web/core/registry";

export function addDocument(documentParams) {
    const steps = [];
    for (const values of documentParams) {
        steps.push(...ProductScreen.addOrderline(values.product, values.quantity));
    }
    steps.push(
        ...[
            ProductScreen.clickPartnerButton(),
            ProductScreen.clickCustomer("AAAAAA"),
            ProductScreen.clickPayButton(),
        ]
    );
    return steps;
}

export function assertTaxTotals(baseAmount, taxAmount, totalAmount) {
    return [
        PaymentScreen.totalIs(totalAmount),
        PaymentScreen.clickPaymentMethod("Bank"),
        PaymentScreen.remainingIs("0.0"),

        PaymentScreen.clickInvoiceButton(),
        PaymentScreen.clickValidate(),

        ReceiptScreen.receiptAmountTotalIs(totalAmount),
        ReceiptScreen.clickNextOrder(),
    ];
}

registry.category("web_tour.tours").add("test_taxes_l10n_it_epson_printer_pos", {
    steps: () =>
        [
            Chrome.startPoS(),
            Dialog.confirm("Open Register"),

            // Order.
            ...addDocument([{ product: "product_5_16_22", quantity: "3" }]),
            ...assertTaxTotals("15.49", "3.41", "18.90"),
        ].flat(),
});
