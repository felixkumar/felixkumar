odoo.define('emipro_theme_base.website_sale_options', function(require) {
    'use strict';

    const publicWidget = require('web.public.widget');
    var WebsiteSale = require('website_sale.website_sale');
    var WebsiteSaleOptional = require('website_sale_options.website_sale');
    var VariantMixin = require('sale.VariantMixin');
    var timer;
    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;
    const { OptionalProductsModal } = require('@sale_product_configurator/js/product_configurator_modal');

    publicWidget.registry.WebsiteSale.include({
        start: function () {
            this.$el.popover({
                trigger: 'manual',
                animation: true,
                html: true,
                title: function () {
                    return _t("My Cart");
                },
                container: 'body',
                placement: 'auto',
                template: '<div class="popover mycart-popover te_open" role="tooltip"><div class="tooltip-arrow"></div><h3 class="popover-header"></h3><div class="te_cross"></div><div class="popover-body"></div></div>'
            });
            return this._super.apply(this, arguments);
        },
        _onProductReady: function() {
            return this._submitForm();
        },
    });
    OptionalProductsModal.include({
        _onChangeCombination: function (ev, $parent, combination) {
        this._super.apply(this, arguments);
        $parent.find('.td-price .te_discount').addClass('d-none')
        $parent.find('.td-price .te_discount_option').addClass('d-none')
        if (combination.has_discounted_price) {
            var difference = combination.list_price - combination.price;
            var discount = difference * 100 / combination.list_price;
                if (discount > 0) {
                    $parent.find('.td-price .te_discount').removeClass('d-none')
                    $parent.find('.td-price .te_discount_option').removeClass('d-none')
                    $parent.find('.te_discount .percent_val').html(discount.toFixed(2));
                    $parent.find('.te_discount_option .percent_val_option').html(discount.toFixed(2));
                }
            }
        },
    });
});
