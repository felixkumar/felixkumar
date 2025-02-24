/** @odoo-module **/

import { registry } from "@web/core/registry";
import tourUtils from "@website_sale/js/tours/tour_utils";

registry.category("web_tour.tours").add('rental_cart_update_duration', {
    test: true,
    url: '/shop',
    steps: () => [
        {
            content: "Search computer write text",
            trigger: 'form input[name="search"]',
            run: "text computer",
        },
        {
            content: "Search computer click",
            trigger: 'form:has(input[name="search"]) .oe_search_button',
        },
        {
            content: "Select computer",
            trigger: '.oe_product_cart:first a:contains("Computer")',
        },
        {
            content: "Open daterangepicker",
            trigger: 'input[name=renting_start_date]',
            run: "click",
        },
        {
            content: "Pick start time",
            trigger: '.o_time_picker_select:nth(0)',
            run: "text 6",
        },
        {
            content: "Pick start time",
            trigger: '.o_time_picker_select:nth(1)',
            run: "text 0",
        },
        {
            content: "Pick end time",
            trigger: '.o_time_picker_select:nth(2)',
            run: "text 12",
        },
        {
            content: "Pick end time",
            trigger: '.o_time_picker_select:nth(3)',
            run: "text 0",
        },
        {
            content: "Apply change",
            trigger: '.o_datetime_buttons button.o_apply',
        },
        {
            content: "click on add to cart",
            trigger: '#product_detail form[action^="/shop/cart/update"] #add_to_cart',
        },
        tourUtils.goToCart(),
        {
            content: "Verify Rental Product is in the cart",
            trigger: '#cart_products div div.css_quantity input[value="1"]',
            isCheck: true,
        },
        {
            content: "Open daterangepicker",
            trigger: 'input[name=renting_start_date]',
            run: "click",
        },
        {
            content: "Pick start time",
            trigger: '.o_time_picker_select:nth(0)',
            run: "text 8",
        },
        {
            content: "Apply change",
            trigger: '.o_datetime_buttons button.o_apply',
        },
        {
            content: "Verify order line rental period start time",
            trigger: 'div.text-muted.small span:contains("08:00")',
            isCheck: true,
        },
        {
            content: "Verify order line rental period return time",
            trigger: 'div.text-muted.small span:contains("12:00")',
            isCheck: true,
        },
    ],
});
