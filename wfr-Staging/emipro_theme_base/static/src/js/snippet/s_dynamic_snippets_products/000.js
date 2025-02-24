odoo.define('emipro_theme_base.s_dynamic_snippet_products', function (require) {
'use strict';


const DynamicSnippetProducts = require("website_sale.s_dynamic_snippet_products")

const publicWidget = require('web.public.widget');
//const DynamicSnippetCarousel = require('website.s_dynamic_snippet_carousel');
var wSaleUtils = require('website_sale.utils');

const DynamicSnippetProductsBrand = DynamicSnippetProducts.extend({
    _getBrandDomain() {
        const searchDomain = [];
        let productBrandId = this.$el.get(0).dataset.productBrandId;
        if (productBrandId && productBrandId !== 'all') {
            if (productBrandId === 'current') {
                productBrandId = undefined;
                const productBrandField = $("#product_details").find(".product_brand_id");
                if (productBrandField && productBrandField.length) {
                    productBrandId = parseInt(productBrandField[0].value);
                }
                if (!productBrandId) {
                    this.trigger_up('main_object_request', {
                        callback: function (value) {
                            if (value.model === "product.brand") {
                                productBrandId = value.id;
                            }
                        },
                    });
                }
            }
            if (productBrandId) {
                searchDomain.push(['product_brand_id', '=', parseInt(productBrandId)]);
            }
        }
        return searchDomain;
    },
    _getSearchDomain: function () {
        const searchDomain = this._super.apply(this, arguments);
        searchDomain.push(...this._getBrandDomain());
        return searchDomain;
    },
});

publicWidget.registry.dynamic_snippet_products = DynamicSnippetProductsBrand;

return DynamicSnippetProductsBrand;
});
