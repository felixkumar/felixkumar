/** @odoo-module **/
import "@theme_prime/js/website_sale";
import publicWidget from "web.public.widget";
import { device } from 'web.config';
import OwlMixin from "header_layout.mixins";
import ajax from 'web.ajax';
const { qweb } = require("web.core");
import { markup } from "@odoo/owl";




publicWidget.registry.WebsiteSale.include({
    _onChangeCombination: function (ev, $parent, combination){
        this._super.apply(this, arguments);
        $('.tp-discount-percentage').addClass('d-md-none');
    },
});

publicWidget.registry.CategoryOwlCarousel = publicWidget.Widget.extend(OwlMixin,{
    selector: '.website_shop_sale',
    events: {
        'click .owl-prev': '_onClickPrev',
        'click .owl-next': '_onClickNext',
    },
    init: function () {
        this._super.apply(this, arguments);
        $('.product-category-container .owl-carousel').each(function(index){
            debugger;
            var $items = $(this);
            var item = $items.attr('data-slide-size') || 1;
            var margin = 34;
            if (device.isMobile){
                margin = 16;
            }
            var responsive = { 0: {items: 1}, 576: {items: 2}, 991: {items: 3}, 1200: {items: 3} };
            OwlMixin.initOwlCarousel('.product-category-container .owl-carousel',margin, responsive, false, 1, false, false, true, false, true, false, false, false);

        });

    },
    _onClickPrev: function (ev) {
        $(ev.currentTarget.hash).trigger('prev.owl.carousel');
    },
    _onClickNext: function (ev) {
        $(ev.currentTarget.hash).trigger('next.owl.carousel');
    },
});

publicWidget.registry.AccessoryProductOwlCarousel = publicWidget.Widget.extend(OwlMixin,{
    selector: '#products_slider',
    events: {
        'click .owl-prev': '_onClickPrev',
        'click .owl-next': '_onClickNext',
    },
    init: function () {
        this._super.apply(this, arguments);
        $('.slider-product-container .owl-carousel').each(function(index){
            debugger;
            var $items = $(this);
            var item = $items.attr('data-slide-size') || 1;
            var responsive = { 0: {items: 1}, 576: {items: 2}, 991: {items: 3}, 1200: {items: 3} };
            var margin = 34;
            if (device.isMobile){
                margin = 16;
            }
            OwlMixin.initOwlCarousel('.slider-product-container .owl-carousel', margin, responsive, false, 1, false, false, true, false, true, false, false, false);

        });

    },
    _onClickPrev: function (ev) {
        $(ev.currentTarget.hash).trigger('prev.owl.carousel');
    },
    _onClickNext: function (ev) {
        $(ev.currentTarget.hash).trigger('next.owl.carousel');
    },
});

//publicWidget.registry.HomeProductOwlCarousel = publicWidget.Widget.extend(OwlMixin,{
//    selector: '.products_home_slider',
//    events: {
//        'click .owl-prev': '_onClickPrev',
//        'click .owl-next': '_onClickNext',
//    },
//    init: function () {
//        this._super.apply(this, arguments);
//            $('.product_slide_container .owl-carousel').each(function(index){
//            debugger;
//            var $items = $(this);
//            var item = $items.attr('data-slide-size') || 1;
//            var responsive = { 0: {items: 1}, 576: {items: 2}, 991: {items: 3}, 1200: {items: 3} };
//            var margin = 34;
//            if (device.isMobile){
//                margin = 16;
//            }
//            OwlMixin.initOwlCarousel('.product_slide_container .owl-carousel', margin, responsive, false, 1, false, false, true, false, true, false, false, false);
//
//        });
//
//    },
//
//    _onClickPrev: function (ev) {
//        $(ev.currentTarget.hash).trigger('prev.owl.carousel');
//    },
//    _onClickNext: function (ev) {
//        $(ev.currentTarget.hash).trigger('next.owl.carousel');
//    },
//
//});
publicWidget.registry.HomeCategoryOwlCarousel = publicWidget.Widget.extend(OwlMixin,{
    selector: '#categories_home_slider',
    events: {
        'click .owl-prev': '_onClickPrev',
        'click .owl-next': '_onClickNext',
    },
    init: function () {
        this._super.apply(this, arguments);
        $('.category_slide_container .owl-carousel').each(function(index){
            var $items = $(this);
            var item = $items.attr('data-slide-size') || 1;
            var responsive = { 0: {items: 2}, 576: {items: 2}, 991: {items: 3}, 1200: {items: 4} };
            var margin = 20;
            if (device.isMobile){
                margin = 8;
            }
            OwlMixin.initOwlCarousel('.category_slide_container .owl-carousel', margin, responsive, false, 1, false, false, true, false, true, false, false, false);

        });

    },
    _onClickPrev: function (ev) {
        $(ev.currentTarget.hash).trigger('prev.owl.carousel');
    },
    _onClickNext: function (ev) {
        $(ev.currentTarget.hash).trigger('next.owl.carousel');
    },
});

publicWidget.registry.MegaMenuCategoryOwlCarousel = publicWidget.Widget.extend(OwlMixin,{
    selector: '.mega_menu_owl_carousel',
    events: {
        'click .owl-prev': '_onClickPrev',
        'click .owl-next': '_onClickNext',
    },
    init: function () {
        this._super.apply(this, arguments);
        $('.mega_menu_container .owl-carousel').each(function(index){
            var $items = $(this);
            var item = $items.attr('data-slide-size') || 1;
            var responsive = { 0: {items: 2}, 576: {items: 2}, 991: {items: 4}, 1200: {items: 5} };
            OwlMixin.initOwlCarousel('.mega_menu_container .owl-carousel',15, responsive, false, 1, false, false, true, false, true, false, false, false);

        });

    },
    _onClickPrev: function (ev) {
        ev.preventDefault();
        $(ev.currentTarget.hash).trigger('prev.owl.carousel');
    },
    _onClickNext: function (ev) {
        ev.preventDefault();
        $(ev.currentTarget.hash).trigger('next.owl.carousel');
    },
});

publicWidget.registry.RatingOwlCarousel = publicWidget.Widget.extend(OwlMixin,{
    selector: '.s_product_rating_container',
    init: function () {
        this._super.apply(this, arguments);
        $('.owl-carousel').each(function(index){
            debugger;
            var $items = $(this);
            var item = $items.attr('data-slide-size') || 1;
            var responsive = { 0: {items: 1}, 576: {items: 1}, 991: {items: 2}, 1200: {items: 2} };
            var margin = 32;
            if (device.isMobile){
                margin = 8;
            }
            OwlMixin.initOwlCarousel('.owl-carousel',margin, responsive, true, 1, false, false, true, false, true, false, true, false);

        });

    },
});


