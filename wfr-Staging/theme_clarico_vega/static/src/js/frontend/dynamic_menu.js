odoo.define('theme_clarico_vega.dynamic_menu', function(require) {
    "use strict";

    const publicWidget = require('web.public.widget');
    //-----------------------------------------
    // Dynamic Category Mega Menu
    //------------------------------------------
    publicWidget.registry.dynamicCategoryMegaMenu = publicWidget.Widget.extend({
        selector: '#wrapwrap',
        read_events: {
            'mouseenter .o_hoverable_dropdown .te_dynamic_ept': '_callScript',
            'click .te_dynamic_ept': '_callScript',
            'mouseenter .o_hoverable_dropdown .te_all_dynamic_ept': '_callFirstEle',
            'click .te_all_dynamic_ept': '_callFirstEle',
        },

        _callFirstEle: function() {
            if ($(window).width() >= 992) {
                var has_parent_content = $('.menu-categories-container li.nav-item.parent-category').find('.main_category_child').first()
                var get_parent = $(has_parent_content).parents('.parent-category');
                $(get_parent).find('.sub-menu-dropdown').css({"visibility": "visible","opacity": "1",});
            }
        },
        _callScript: function(ev) {
            $("#custom_menu li").each(function() {
                var ul_index = 0;
                $(document).on('mouseenter', "#custom_menu_li", function(ev) {
                    var li_place = $(this).position().top;
                    $(this).children("#custom_recursive").css("top", li_place);
                    var self = $(this).children("#custom_recursive");
                    if ($(this).children("#custom_recursive").length > 0) {
                        ul_index = $(self).parents("ul").length == 0 ? $(self).parents("ul").length : ul_index + 1;
                        $(self).css({"opacity": "1","visibility": "visible","transform": "translateX(-10px)","transition": "all 0.2s",});
                    }
                });
                $(document).on('mouseleave', "#custom_menu_li", function(ev) {
                    $(this).children("ul#custom_recursive").css({"opacity": "0","visibility": "hidden","transform": "translateX(20px)",});
                });
            })
        },
    });

    //------------------------------------------
    // Dynamic Category Animation
    //------------------------------------------
    publicWidget.registry.dynamicCategory = publicWidget.Widget.extend({
        selector: '#top_menu_collapse',
        read_events: {
            'mouseenter .parent-category': '_onMouseEnter',
            'click .main_category_child': '_onMouseEnter',
            'click .sub-menu-dropdown': '_preventClick',
            'click .ctg_arrow': '_onClickOnArrow',
            'click #top_menu .dropdown': '_onClickDynamicMenu',
        },
        _onMouseEnter: function(ev) {
            ev.preventDefault();
            ev.stopPropagation();
            var self = $(ev.currentTarget)
            if (!self.find('.dynamic_mega_menu_child').length == 1) {
                self.find('.sub-menu-dropdown').css({"opacity": "1", "z-index":"99"});
            }
        },
        _preventClick: function(ev) {
            ev.stopPropagation();
        },
        _onClickDynamicMenu: function(ev) {
            var self = $(ev.currentTarget)
            if ($(window).width() < 992) {
                if ($(self).hasClass('show')) {
                    self.removeClass('show');
                    self.find(".dropdown-menu").removeClass('show');
                } else {
                    self.addClass('show');
                    self.find(".dropdown-menu").addClass('show');
                }
            }
        },
        _onClickOnArrow: function(ev) {
            if ($(window).width() <= 991) {
                $(ev.currentTarget).toggleClass('te_down_ctg_icon');
                if ($(ev.currentTarget).hasClass('te_down_ctg_icon')) {
                    ev.preventDefault();
                    $(ev.currentTarget).siblings("ul#custom_recursive").slideDown('slow');
                    return false;
                } else {
                    $(ev.currentTarget).siblings("ul#custom_recursive").slideUp('slow');
                    return false;
                }
            }
        },
    });

    $(document).ready(function() {
        if ($('header#top').hasClass('o_hoverable_dropdown')){
            if($(window).width() <= 991){
                $('#top_menu').find('.o_mega_menu_toggle').attr('data-bs-toggle', 'dropdown');
            } else {
                $('#top_menu').find('.o_mega_menu_toggle').removeAttr('data-bs-toggle');
            }
        }
    });
});

