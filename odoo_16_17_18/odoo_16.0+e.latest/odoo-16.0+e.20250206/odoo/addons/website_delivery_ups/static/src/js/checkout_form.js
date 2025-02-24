/** @odoo-module */

import publicWidget from 'web.public.widget';
import {_t} from 'web.core';
import 'website_sale_delivery.checkout';

publicWidget.registry.websiteSaleDelivery.include({
    start: function () {
        this.codOptions = document.querySelectorAll('.o_payment_option_card input[type=radio][data-provider="custom"][data-provider-custom-mode="cash_on_delivery"]');
        if (this.codOptions.length > 0) { // Falsy evaluation does not work with NodeList
            this.paymentOptions = document.querySelectorAll('.o_payment_option_card input[type=radio]');

            this.warning = document.createElement('p');
            const boldMsg = document.createElement('b');
            boldMsg.innerText = _t('No suitable payment option could be found.');
            this.warning.innerText = _t('If you believe that it is an error, please contact the website administrator.');
            boldMsg.classList.add('d-block');
            this.warning.prepend(boldMsg);
            this.warning.classList.add('alert-warning', 'p-3', 'm-1', 'd-none');

            this.paymentOptionsContainer = document.querySelector('#payment_method');
            this.paymentOptionsContainer.querySelector('div.card').prepend(this.warning);
        }
        return this._super.apply(this, ...arguments);
    },

    /**
     * Hides or shows a payment option card.
     * @param node the input element of the payment option card
     * @param enabled whether to show or hide the card
     * @private
     */
    _setEnablePaymentOption(node, enabled) {
        if (enabled) {
            node.parentNode.parentNode.classList.remove('d-none');
        } else {
            node.parentNode.parentNode.classList.add('d-none');
            node.checked = false;
        }
    },

    /**
     * Checks all payment options and hides them if it is an COD payment option and the delivery is not ups.
     * @param {Event} ev the triggered document event
     * @private
     * @override
     */
    _onCarrierClick: function (ev) {
        this._super(...arguments);

        if (this.codOptions.length === 0) { // Falsy evaluation does not work with NodeList
            return;
        }

        this.warning.classList.add('d-none');

        const input = ev.currentTarget.querySelector('input');
        let atLeastOneOptionAvailable = false;
        for (let option of this.paymentOptions) {
            if (option.dataset.provider === "custom" &&
                option.dataset.providerCustomMode === "cash_on_delivery" &&
                (input.dataset.deliveryType !== 'ups' || !input.dataset.upsCod)) {
                    this._setEnablePaymentOption(option, false);
            } else {
                if (option.dataset.provider === "custom" &&
                    option.dataset.providerCustomMode === "cash_on_delivery") {
                    this._setEnablePaymentOption(option, true);
                }
                atLeastOneOptionAvailable = true;
            }
        }

        // Jquery because the button does not behave nicely with vanilla dataset.
        let $payButton = $('button[name="o_payment_submit_button"]');
        let disabledReasons = $payButton.data('disabled_reasons') || {};
        disabledReasons.noOptionAvailableCOD = false;

        if (!atLeastOneOptionAvailable) {
            this.warning.classList.remove('d-none');
            disabledReasons.noOptionAvailableCOD = true;
        } else if (this.paymentOptions.length === 1) {
            $(this.paymentOptions[0]).click(); // Make sure the option is selected if that's the only one, because the input is hidden in that case.
        }
        $payButton.data('disabled_reasons', disabledReasons);
    }
});
