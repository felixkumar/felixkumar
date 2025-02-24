odoo.define('header_layout.content.mega_menu_slider', function (require) {
'use strict';

const config = require('web.config');
var publicWidget = require('web.public.widget');
var animations = require('website.content.snippets.animation');
const weUtils = require('web_editor.utils');
require('website.content.menu');
const dom = require('web.dom');

publicWidget.registry.menuDirection.include({

    start: function () {
        $('.o_mega_menu > *').on('click', function (ev) {
            ev.stopPropagation();
        });
        return this._super.apply(this, arguments);
    },
   });
publicWidget.registry.OwlCarouselSlider = publicWidget.Widget.extend({
    selector: '#wrapwrap',

    start: function () {
        $('.owl-prev').on('click', function (ev) {
            ev.preventDefault();
        });
        $('.owl-next').on('click', function (ev) {
            ev.preventDefault();
        });
        return this._super.apply(this, arguments);
    },
   });
   return publicWidget.registry.OwlCarouselSlider;
});