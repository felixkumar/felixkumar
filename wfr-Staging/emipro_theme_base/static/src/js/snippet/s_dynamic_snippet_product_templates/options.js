odoo.define('emipro_theme_base.s_dynamic_snippet_prod_temp_options', function (require) {
'use strict';

const options = require('web_editor.snippets.options');
const dynamicSnippetOptions = require('website.s_dynamic_snippet_carousel_options');

var wUtils = require('website.utils');


const dynamicSnippetProdTempOptions = dynamicSnippetOptions.extend({
    init: function () {
        this._super.apply(this, arguments);
        this.modelNameFilter = 'product.template';
        this.productCategories = {};
    },
     _computeWidgetVisibility(widgetName, params) {
        return this._super(...arguments);
    },
    _fetchProductTemplateCategories: function () {
        return this._rpc({
            model: 'product.public.category',
            method: 'search_read',
            kwargs: {
                domain: wUtils.websiteDomain(this),
                fields: ['id', 'name'],
            }
        });
    },
    _fetchProductTemplateBrand: function () {
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
        await this._renderProductTemplateCategorySelector(uiFragment);
        await this._renderBrandTemplateSelector(uiFragment);
    },

    _renderProductTemplateCategorySelector: async function (uiFragment) {
        const productCategories = await this._fetchProductTemplateCategories();
        for (let index in productCategories) {
            this.productCategories[productCategories[index].id] = productCategories[index];
        }
        const productCategoriesSelectorEl = uiFragment.querySelector('[data-name="product_category_opt"]');
        return this._renderSelectUserValueWidgetButtons(productCategoriesSelectorEl, this.productCategories);

    },
    _renderBrandTemplateSelector: async function (uiFragment) {
        this.productBrands = {}
        const productBrands = await this._fetchProductTemplateBrand();
        for (let index in productBrands) {
            this.productBrands[productBrands[index].id] = productBrands[index];
        }
        const productBrandsSelectorEl = uiFragment.querySelector('[data-name="product_brand_opt"]');
        return this._renderSelectUserValueWidgetButtons(productBrandsSelectorEl, this.productBrands);
    },

    _setOptionsDefaultValues: function () {
        this._setOptionValue('productCategoryId', 'all');
        this._super.apply(this, arguments);
    },

    _setOptionsDefaultValues: function () {
        this._setOptionValue('productBrandId', 'all');
        this._super.apply(this, arguments);
    }



});

options.registry.dynamic_snippet_prod_temp = dynamicSnippetProdTempOptions;

return dynamicSnippetProdTempOptions;
});
