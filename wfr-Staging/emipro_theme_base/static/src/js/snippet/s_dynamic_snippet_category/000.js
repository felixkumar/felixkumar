odoo.define('emipro_theme_base.s_dynamic_snippet_category', function (require) {
'use strict';

const publicWidget = require('web.public.widget');
const DynamicSnippetCarousel = require('website.s_dynamic_snippet_carousel');
var wSaleUtils = require('website_sale.utils');

const DynamicSnippetCategory = DynamicSnippetCarousel.extend({
    selector: '.s_dynamic_snippet_category',
    _getSelectedCategorySearchDomain() {
        const searchDomain = [];
        let productCategoryIds = this.$el.get(0).dataset.productCategoryIds;
        if (productCategoryIds && productCategoryIds != '[]') {
            searchDomain.push(['id', 'in', JSON.parse(productCategoryIds).map(productCategory => productCategory.id)]);
        }
        return searchDomain;
    },
    _getSearchDomain: function () {
        const searchDomain = this._super.apply(this, arguments);
        searchDomain.push(...this._getSelectedCategorySearchDomain());
        return searchDomain;
    },
    _getRpcParameters: function () {
        return {}
    },
});
publicWidget.registry.dynamic_snippet_category = DynamicSnippetCategory;

return DynamicSnippetCategory;
});
