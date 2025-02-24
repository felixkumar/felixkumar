odoo.define('header_layout.s_dynamic_snippet_custom_carousel', function (require) {
'use strict';

const publicWidget = require('web.public.widget');
const DynamicSnippet = require('website.s_dynamic_snippet');
const config = require('web.config');
var OwlMixin =require('header_layout.mixins');
var ajax = require('web.ajax');




const DynamicSnippetOwlCarousel= DynamicSnippet.extend(OwlMixin, {
    selector: '.s_dynamic_owl_carousel',
     events: {
        'click .owl-prev': '_onClickPrev',
        'click .owl-next': '_onClickNext',
    },
    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        this.template_key = 'header_layout.s_dynamic_snippet.owl_carousel';
        this.uniqueId = _.uniqueId('s_dynamic_snippet_owl_carousel_');


    },

    start: function () {
        return this._super.apply(this, arguments).then(() => {
              $('.owl_carousel_slide_container .owl-carousel').each(function(index){
                debugger;
                var $items = $(this);
                var item = $items.attr('data-slide-size') || 1;
                var responsive = { 0: {items: 1}, 576: {items: 2}, 991: {items: 3}, 1200: {items: 3} };
                var margin = 34;
                if (config.device.isMobile){
                    margin = 16;
                }
                OwlMixin.initOwlCarousel('.owl_carousel_slide_container .owl-carousel', margin, responsive, false, 1, false, false, true, false, true, false, false, false);
        });
        })
    },
    _onClickPrev: function (ev) {
        ev.preventDefault();
        $(ev.currentTarget.hash).trigger('prev.owl.carousel');
    },
    _onClickNext: function (ev) {
        ev.preventDefault();
        $(ev.currentTarget.hash).trigger('next.owl.carousel');
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _getQWebRenderOptions: function () {
        return Object.assign(
            this._super.apply(this, arguments),
            {
                interval: parseInt(this.$target[0].dataset.carouselInterval),
                heading_name: this.$target[0].dataset.carouselName,
                sub_name: this.$target[0].dataset.carouselSubName,
                rowPerSlide: parseInt(config.device.isMobile ? 1 : this.$target[0].dataset.rowPerSlide || 1),
                arrowPosition: this.$target[0].dataset.arrowPosition || '',
            },
        );
    },
});

publicWidget.registry.dynamic_snippet_owl_carousel = DynamicSnippetOwlCarousel;

return DynamicSnippetOwlCarousel;


});
