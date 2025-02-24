/** @odoo-module **/

import tour from 'web_tour.tour';
import tourUtils from 'website_sale.tour_utils';

tour.register('shop_buy_accessory_rental_product', {
    test: true,
    url: '/shop',
},
    [
        {
            content: "Search parent product write text",
            trigger: 'form input[name="search"]',
            run: "text Parent product",
        },
        {
            content: "Search parent product click",
            trigger: 'form:has(input[name="search"]) .oe_search_button',
        },
        {
            content: "Select parent product",
            trigger: '.oe_product_cart:first a:contains("Parent product")',
        },
        {
            content: "click on add to cart",
            trigger: '#product_detail form[action^="/shop/cart/update"] #add_to_cart',
        },
        tourUtils.goToCart({quantity: 1}),
        {
            content: "Verify there are 1 quantity of Parent product",
            trigger: '#cart_products tbody td.td-qty div.css_quantity input[value=1]',
            run: function () {}, // it's a check
        },
        {
            content: "Add Accessory product to cart via the quick add button",
            trigger: 'a:contains("Add to Cart")',
        },
    ]
);
