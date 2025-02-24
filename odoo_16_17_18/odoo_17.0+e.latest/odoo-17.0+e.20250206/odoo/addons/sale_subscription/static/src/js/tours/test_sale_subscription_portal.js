/** @odoo-module **/

import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("test_sale_subscription_portal", {
    test: true,
    steps: () => [
        {
            content: "Check that Pay button is enabled",
            trigger: ".o_payment_form button[name='o_payment_submit_button']:not([disabled])",
            run: () => {},
        },
    ],
});

registry.category("web_tour.tours").add("test_optional_products_portal", {
    test: true,
    steps: () => [
        {
            content: "Check optional product are shown",
            trigger: 'div[id="content"] h3[id="quote_3"]',
            run: () => {},
        },
    ],
});
