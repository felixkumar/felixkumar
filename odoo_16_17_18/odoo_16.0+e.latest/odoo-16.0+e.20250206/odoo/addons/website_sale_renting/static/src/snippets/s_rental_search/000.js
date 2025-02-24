/** @odoo-module **/

import publicWidget from 'web.public.widget';
import { momentToLuxon, serializeDateTime } from "@web/core/l10n/dates";


publicWidget.registry.RentalSearchSnippet = publicWidget.Widget.extend({
    selector: '.s_rental_search',
    events: {
        'click .s_rental_search_btn': '_onClickRentalSearchButton',
        'toggle_search_btn .o_website_sale_daterange_picker': 'onToggleSearchBtn',
        'apply.daterangepicker .o_website_sale_daterange_picker': '_onClickRentalSearchButton',
    },

    onToggleSearchBtn(ev) {
        ev.currentTarget.querySelector('.s_rental_search_btn').disabled = Boolean(ev.detail);
    },

    /**
     * This function is triggered when the user clicks on the rental search button.
     * @param ev
     */
    _onClickRentalSearchButton(ev, picker) {
        const rentalSearch = ev.currentTarget.closest('.s_rental_search');
        const searchParams = new URLSearchParams();
        picker = picker || this.$("#s_rental_search_date_input").data("daterangepicker");
        if (picker.startDate && picker.endDate) {
            searchParams.append('start_date', `${serializeDateTime(momentToLuxon(picker.startDate))}`);
            searchParams.append('end_date', `${serializeDateTime(momentToLuxon(picker.endDate))}`);
        }
        const productAttributeId = rentalSearch.querySelector('.product_attribute_search_rental_name').id;

        const productAttributeValueId = rentalSearch.querySelector('.s_rental_search_select').value;
        if (productAttributeValueId) {
            searchParams.append('attrib', `${productAttributeId}-${productAttributeValueId}`);
        }
        window.location = `/shop?${searchParams.toString()}`;
    },
});


export default publicWidget.registry.RentalSearchSnippet;
