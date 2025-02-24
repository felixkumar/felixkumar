odoo.define('emipro_theme_base.s_dynamic_snippet_brand_options', function (require) {
'use strict';

const options = require('web_editor.snippets.options');
const dynamicSnippetOptions = require('website.s_dynamic_snippet_carousel_options');

var wUtils = require('website.utils');


const dynamicSnippetBrandOptions = dynamicSnippetOptions.extend({
    init: function () {
        this._super.apply(this, arguments);
        this.modelNameFilter = 'product.brand';
        this.brands = {};
    },
     _computeWidgetVisibility(widgetName, params) {
        return this._super(...arguments);
    },
    _fetchBrands: function () {
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
        await this._renderProductBrandSelector(uiFragment);
    },
    _renderProductBrandSelector: async function (uiFragment) {
        const brands = await this._fetchBrands();
        for (let index in brands) {
            this.brands[brands[index].id] = brands[index];
        }
        const productBrandsSelectorEl = uiFragment.querySelector('[data-name="product_brand_opt"]');
        return this._renderSelectUserValueWidgetButtons(productBrandsSelectorEl, this.brands);

    }
});

options.registry.dynamic_snippet_brand = dynamicSnippetBrandOptions;

return dynamicSnippetBrandOptions;
});
