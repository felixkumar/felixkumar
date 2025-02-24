odoo.define('emipro_theme_base.s_dynamic_snippet_brand', function (require) {
'use strict';

const publicWidget = require('web.public.widget');
const DynamicSnippetCarousel = require('website.s_dynamic_snippet_carousel');
var wSaleUtils = require('website_sale.utils');

const DynamicSnippetBrand = DynamicSnippetCarousel.extend({
    selector: '.s_dynamic_snippet_brand',
    _getSelectedBrandSearchDomain() {
        const searchDomain = [];
        let productBrandIds = this.$el.get(0).dataset.productBrandIds;
        if (productBrandIds && productBrandIds != '[]') {
            searchDomain.push(['id', 'in', JSON.parse(productBrandIds).map(productBrand => productBrand.id)]);
        }
        return searchDomain;
    },
    _getSearchDomain: function () {
        const searchDomain = this._super.apply(this, arguments);
        searchDomain.push(...this._getSelectedBrandSearchDomain());
        return searchDomain;
    },
    _getRpcParameters: function () {
        return {}
    },
});
publicWidget.registry.dynamic_snippet_brand = DynamicSnippetBrand;

return DynamicSnippetBrand;
});
