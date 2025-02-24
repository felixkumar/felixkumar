odoo.define('header_layout.content.add_to_cart', function (require) {
'use strict';

const config = require('web.config');
var publicWidget = require('web.public.widget');
var animations = require('website.content.snippets.animation');
const weUtils = require('web_editor.utils');
require('website_sale.website_sale');
const dom = require('web.dom');

animations.registry.AddToCartSticky = animations.Animation.extend({
     selector: '.o_wsale_product_page',
        effects: [{
            startEvents: 'scroll',
            update: '_sticky_add_to_cart',
        }],

     init: function() {
        this._super(...arguments);
        var getClass = $('body').find('.custom_product_bottom');
        this.scrolledPoint = 0;
    },
     destroy: function () {
//        this._toggleFixedHeader(false);
        this.$el.find('.custom_product_bottom').removeClass('add_to_cart_inner');
        this._super(...arguments);
    },
     _sticky_add_to_cart: function(scroll) {
        var add_to_cart_bottom = $('.custom_product_bottom');
        if (add_to_cart_bottom.length){

        const pageIsScrolled = (scroll > this.scrolledPoint);
        if (pageIsScrolled) {
                       this.$el.find('.custom_product_bottom').addClass('add_to_cart_inner');

            if($('.custom_product_bottom').offset().top + $('.custom_product_bottom').height() >= $('#bottom').offset().top - 10){
               this.$el.find('.custom_product_bottom').removeClass('add_to_cart_inner');
            }
//            if ($(document).scrollTop() + $('.custom_product_bottom').height() < $('#bottom').offset().top){
//               this.$el.find('.custom_product_bottom').addClass('add_to_cart_inner');
//            }

            this.pageIsScrolled = pageIsScrolled;
            this.$el.trigger('odoo-transitionstart');

        }
        else{
            this.$el.find('.custom_product_bottom').removeClass('add_to_cart_inner');
            this.pageIsScrolled = pageIsScrolled;
        }
        }
        },

});
/*
 CART JS
*/
publicWidget.registry.websiteSaleCart.include({
    _onClickDeleteProduct: function (ev) {
            ev.preventDefault();
            this._super(...arguments);
            $(ev.currentTarget.parentElement.previousElementSibling).find('.js_quantity').val(0).trigger('change');
 }
 });
publicWidget.registry.WebsiteSale.include({
    _changeCountry: function () {
        if (!$("#country_id").val()) {
            return;
        }
        this._rpc({
            route: "/shop/country_infos/" + $("#country_id").val(),
            params: {
                mode: $("#country_id").attr('mode'),
            },
        }).then(function (data) {
            // placeholder phone_code
            $("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+'+ data.phone_code : '');

            // populate states and display
            var selectStates = $("select[name='state_id']");
            // dont reload state at first loading (done in qweb)
            if (selectStates.data('init')===0 || selectStates.find('option').length===1) {
                if (data.states.length || data.state_required) {
                    selectStates.html('');
                    _.each(data.states, function (x) {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0])
                            .attr('data-code', x[2]);
                        selectStates.append(opt);
                    });
                    selectStates.parent('div').show();
                } else {
                    selectStates.val('').parent('div').hide();
                }
                selectStates.data('init', 0);
            } else {
                selectStates.data('init', 0);
            }

            // manage fields order / visibility
            if (data.fields) {
                var all_fields = ["street", "zip", "city", "country_name"]; // "state_code"];
                _.each(all_fields, function (field) {
                    debugger;
                    $(".checkout_autoformat .div_" + field.split('_')[0]).toggle($.inArray(field, data.fields)>=0);
                });
            }

            if ($("label[for='zip']").length) {
                $("label[for='zip']").toggleClass('label-optional', !data.zip_required);
                $("label[for='zip']").get(0).toggleAttribute('required', !!data.zip_required);
            }
            if ($("label[for='zip']").length) {
                $("label[for='state_id']").toggleClass('label-optional', !data.state_required);
                $("label[for='state_id']").get(0).toggleAttribute('required', !!data.state_required);
            }
        });
    },


});

});