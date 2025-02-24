odoo.define('emipro_theme_base.s_dynamic_snippet_category_options', function (require) {
'use strict';

const options = require('web_editor.snippets.options');
const dynamicSnippetOptions = require('website.s_dynamic_snippet_carousel_options');

var wUtils = require('website.utils');


const dynamicSnippetCategoryOptions = dynamicSnippetOptions.extend({
    init: function () {
        this._super.apply(this, arguments);
        this.modelNameFilter = 'product.public.category';
        this.productCategories = {};
    },
     _computeWidgetVisibility(widgetName, params) {
        return this._super(...arguments);
    },
    _fetchProductCategories: function () {
        return this._rpc({
            model: 'product.public.category',
            method: 'search_read',
            kwargs: {
                domain: wUtils.websiteDomain(this),
                fields: ['id', 'name'],
            }
        });
    },
    _renderCustomXML: async function (uiFragment) {
        await this._super.apply(this, arguments);
        await this._renderProductCategorySelector(uiFragment);
    },
    _renderProductCategorySelector: async function (uiFragment) {
        const productCategories = await this._fetchProductCategories();
        for (let index in productCategories) {
            this.productCategories[productCategories[index].id] = productCategories[index];
        }
        const productCategoriesSelectorEl = uiFragment.querySelector('[data-name="product_category_opt"]');
        return this._renderSelectUserValueWidgetButtons(productCategoriesSelectorEl, this.productCategories);
    },
});

options.registry.dynamic_snippet_category = dynamicSnippetCategoryOptions;

return dynamicSnippetCategoryOptions;
});
