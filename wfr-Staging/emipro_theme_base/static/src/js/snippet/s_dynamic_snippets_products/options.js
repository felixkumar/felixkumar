odoo.define('emipro_theme_base.s_dynamic_snippet_products_options_brand', function (require) {
'use strict';

const options = require('web_editor.snippets.options');
const s_dynamic_snippet_products_options = require('website_sale.s_dynamic_snippet_products_options');

var wUtils = require('website.utils');

const alternativeSnippetRemovedOptions = [
    'filter_opt', 'product_category_opt', 'product_tag_opt', 'product_names_opt', 'product_brand_opt'
]

const dynamicSnippetProductsOptionsBrand = s_dynamic_snippet_products_options.extend({

    _fetchProductBrand: function () {
        return this._rpc({
            model: 'product.brand',
            method: 'search_read',
            kwargs: {
                domain: wUtils.websiteDomain(this),
                fields: ['id', 'name'],
            }
        });
    },
    _renderCustomXML: async function (uiFragment) {
        await this._super.apply(this, arguments);
        await this._renderBrandSelector(uiFragment);
    },

    _renderBrandSelector: async function (uiFragment) {
        this.productBrands = {}
        const productBrands = await this._fetchProductBrand();
        for (let index in productBrands) {
            this.productBrands[productBrands[index].id] = productBrands[index];
        }
        const productBrandsSelectorEl = uiFragment.querySelector('[data-name="product_brand_opt"]');
        return this._renderSelectUserValueWidgetButtons(productBrandsSelectorEl, this.productBrands);
    },

    _setOptionsDefaultValues: function () {
        this._setOptionValue('productBrandId', 'all');
        this._super.apply(this, arguments);
    },
});

options.registry.dynamic_snippet_products = dynamicSnippetProductsOptionsBrand;

return dynamicSnippetProductsOptionsBrand;
});
