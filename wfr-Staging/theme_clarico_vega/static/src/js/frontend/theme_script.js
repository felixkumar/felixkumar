odoo.define('theme_clarico_vega.theme_script', function(require) {
    'use strict';

    var sAnimations = require('website.content.snippets.animation');
    var publicWidget = require('web.public.widget');
    var Widget = require('web.Widget');
    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t
    var ajax = require('web.ajax');
    var config = require('web.config');
    var OwlMixin = require('theme_clarico_vega.mixins');
    var sale = publicWidget.registry.WebsiteSale;
    var dynamic_snippet = publicWidget.registry.dynamic_snippet;
    var ProductWishlist = new publicWidget.registry.ProductWishlist();
    var wSaleUtils = require('website_sale.utils');
    var multirangePriceSelector = publicWidget.registry.multirangePriceSelector;
    var ProductCategoriesLinks = publicWidget.registry.ProductCategoriesLinks;
    require('website_sale.website_sale');

    const { OptionalProductsModal } = require('@sale_product_configurator/js/product_configurator_modal');

    // 01. Search in Header
    publicWidget.registry.searchBar.include ({
        xmlDependencies: (publicWidget.registry.searchBar.prototype.xmlDependencies || []).concat(['/theme_clarico_vega/static/src/xml/search.xml']),
        _render: function (res) {
            if (this._scrollingParentEl) {
                this._scrollingParentEl.removeEventListener('scroll', this._menuScrollAndResizeHandler);
                window.removeEventListener('resize', this._menuScrollAndResizeHandler);
                delete this._scrollingParentEl;
                delete this._menuScrollAndResizeHandler;
            }
            const $prevMenu = this.$menu;
            this.$el.toggleClass('dropdown show', !!res);
            if (res && this.limit) {
                const results = res['results'];
                const categories = res['categories'];
                const quickLink = res['is_quick_link'];
                let template = 'website.s_searchbar.autocomplete';
                const candidate = template + '.' + this.searchType;
                if (qweb.has_template(candidate)) {
                    template = candidate;
                }
                this.$menu = $(qweb.render(template, {
                    results: results,
                    categories: categories,
                    quickLink: quickLink,
                    parts: res['parts'],
                    hasMoreResults: results.length < res['results_count'],
                    search: this.$input.val(),
                    fuzzySearch: res['fuzzy_search'],
                    widget: this,
                }));

                this.$menu.css('min-width', this.autocompleteMinWidth);
                const megaMenuEl = this.el.closest('.o_mega_menu');
                if (megaMenuEl) {
                    const navbarEl = this.el.closest('.navbar');
                    const navbarTogglerEl = navbarEl ? navbarEl.querySelector('.navbar-toggler') : null;
                    if (navbarTogglerEl && navbarTogglerEl.clientWidth < 1) {
                        this._scrollingParentEl = megaMenuEl;
                        this._menuScrollAndResizeHandler = () => this._adaptToScrollingParent();
                        this._scrollingParentEl.addEventListener('scroll', this._menuScrollAndResizeHandler);
                        window.addEventListener('resize', this._menuScrollAndResizeHandler);
                        this._adaptToScrollingParent();
                    }
                }
                this.$el.append(this.$menu);
                this.$el.find('button.extra_link').on('click', function (event) {
                    event.preventDefault();
                    window.location.href = event.currentTarget.dataset['target'];
                });
                this.$el.find('.s_searchbar_fuzzy_submit').on('click', (event) => {
                    event.preventDefault();
                    this.$input.val(res['fuzzy_search']);
                    const form = this.$('.o_search_order_by').parents('form');
                    form.submit();
                });
            }
            if ($prevMenu) {
                $prevMenu.remove();
            }
        },
        _onKeydown: function (ev) {
            switch (ev.which) {
                case $.ui.keyCode.DOWN:
                    ev.preventDefault();
                    if (this.$menu) {
                        let $element = ev.which === $.ui.keyCode.UP ? this.$menu.children('.dropdown-item').last() : this.$menu.children('.categ_search').length ? this.$menu.find('.categ_search .dropdown-item:nth-child(2)'): this.$menu.children('.dropdown-item').first();
                        $element.focus();
                    }
                    break;
            }
            this._super.apply(this, arguments);
        },
    })
    sAnimations.registry.themeSearch = sAnimations.Class.extend({
        selector: '#wrapwrap',
        read_events: {
            'click .te_srch_icon': '_onSearchClickOpen',
            'keyup input[name="search"]': '_onSearchClickData',
            'click .te_srch_close': '_onSearchClickClose',
            'click .te_srch_close_ept': '_onSearchClickCloseEpt',
            'click .mycart-popover .js_delete_product': '_onClickDeleteProduct',
            'keydown .te_search_popover .o_dropdown_menu a':'_onKeydown',
            'keydown .te_search_popover .o_dropdown_menu button':'_onKeydown',
        },
        start: function() {
            $('.variant_attribute  .list-inline-item').find('.active').parent().addClass('active_li');
            $(".list-inline-item .css_attribute_color").change(function(ev) {
                var $parent = $(ev.target).closest('.js_product');
                $parent.find('.css_attribute_color').parent('.list-inline-item').removeClass("active_li");
                $parent.find('.css_attribute_color').filter(':has(input:checked)').parent('.list-inline-item').addClass("active_li");
            });

            $(document).on('click', '.validate-sign-in', function(e) {
                $('.quick_view_modal > .quick_close').trigger('click');
                $("#loginRegisterPopup").modal();
                var tab = $(e.currentTarget).attr('href');
                $('.nav-tabs a[href="' + tab + '"]').tab('show')
            });

            var input_val = $('input[name="search"]').val();
            if (input_val) {
                $('.te_srch_close_ept').css("display", "block");
            }
        },
        _onKeydown: function (ev) {
        var temp = $('.te_search_popover .o_dropdown_menu');
        var tempval;
            switch (ev.which) {
                case $.ui.keyCode.DOWN:
                    ev.preventDefault();
                    if (temp && ev.currentTarget) {
                        let $element = ev.currentTarget.nextElementSibling;
                        if($element == null){
                            $element = $('.categ_search').next();
                        }
                        $element.focus();
                    }
                    break;
                case $.ui.keyCode.UP:
                    ev.preventDefault();
                    if(temp){
                        let $element = ev.currentTarget.previousElementSibling;
                        if($('.categ_search').length != 0 && ev.currentTarget == $('.o_dropdown_menu').children()[1]){
                            $element = $('.categ_search a')[$('.categ_search a').length-1];
                        }
                        if($element !=null)
                            $element.focus();
                    }
                    break;
            }
        },
        _onSearchClickData: function(ev) {
            var self = ev.currentTarget;
            var input_val = $('input[name="search"]').val();
            if (input_val) {
                $('.te_srch_close_ept').css("display", "block");
            }
        },
        _onSearchClickCloseEpt:function(ev) {
            var params = new URLSearchParams(window.location.search);
            $('input[name="search"]').val('');
            const classExists = $('.te_searchform__body, .te_sub_search').length;
            if (classExists) {
                $('.te_srch_close_ept').css("display", "none");
            }
            else if (params.get('search')){
                $('button[type="submit"]').trigger('click');
            }
            else {
                $('.te_srch_close_ept').css("display", "none");
                $(".search_btn_close").trigger('click');
            }
        },
        _onSearchClickOpen: function(ev){
            var self = ev.currentTarget;
            if ($('.te_header_style_right').length) {
                $(".te_search_popover").addClass("visible");
                $(self).hide()
                $(".te_srch_close").css('display', 'block');
                setTimeout(function() {
                    $('.o_searchbar_form input[name="search"]').focus();
                }, 500);
            } else if ($(".te_searchform__popup").length) {
                $(".te_searchform__popup").addClass("open");
                $(".te_srch_close").show();
                setTimeout(function() {
                    $('.o_searchbar_form input[name="search"]').focus();
                }, 500);
            }
        },
        _onSearchClickClose: function(ev){
            var self = ev.currentTarget;
            if ($('.te_header_style_right').length) {
                $(".te_search_popover").removeClass("visible");
                $(self).hide();
                $(".te_srch_icon").show();
            } else if ($(".te_searchform__popup").length) {
                $(".te_searchform__popup").removeClass("open");
                $(".te_srch_icon").show();
            }
        }
    });

    // see all functionality in filter
    publicWidget.registry.SeeAllProcess = publicWidget.Widget.extend({
        selector: '#wrapwrap',
        read_events: {
            'click .see_all_attr_btn': '_get_see_all_data',
        },
        _get_see_all_data: function(ev) {
            const $target = $(ev.currentTarget);
            var self = this;
            var attr_id = $target.attr('attr-id');
            var search= $("input[name=search]").val();
            var category= $("input[name=category]").val();
            var is_mobile = $target.attr('data-is_mobile');
            var domain_qs= $("input[name=domain_qs]").val();
            var brand_val = $("input[name=brand_val]").val();

            var params = {'attr_id': attr_id,'is_mobile': is_mobile, 'category': category, 'brand_val':brand_val, 'search': search, 'domain_qs':domain_qs};
            ajax.jsonRpc('/see_all', 'call', params).then(function (data){
                if(typeof(attr_id) == 'undefined'){
                    if(is_mobile == 'True'){
                        $('#o_wsale_offcanvas_attribute_0').html(data);
                    }
                    else{
                        $('#o_products_attributes_0').html(data);
                    }
                    $('.see_all_attr_0').hide()
                }
                else{
                    if(is_mobile == 'True'){
                        $('#o_wsale_offcanvas_attribute_'+attr_id).html(data);
                    }
                    else{
                        $('#o_products_attributes_'+attr_id).html(data);
                    }
                    $('.see_all_attr_'+attr_id).hide()
                }

            });
        }
    });
    //------------------------------------------
    // Shop Events
    //------------------------------------------
    publicWidget.registry.ThemeEvent = publicWidget.Widget.extend(OwlMixin, {
        selector: '.oe_website_sale',
        read_events: {
            'click .te_clear_all_variant': '_onClearAttribDiv',
            'click .te_clear_attr_a':  '_onClearAttribInd',
            'click .te_clear_all_form_selection': '_onClearAttribAll',
            'click .te_clear_all_variant_off_canvas': '_onClearAttribDiv',
        },
        start: function() {
            this._super.apply(this, arguments);
            this.onShowClearVariant();
            this._onslide();
            if ($('#id_lazyload').length) {
                $("img.lazyload").lazyload();
            }
        },
        _onslide: function(){
            $('.js_attributes .main_attr').each(function (){
                if (this.getElementsByTagName('li').length > 6) {
                    $(this).find('ul').mCustomScrollbar({ axis: "y", theme: "dark-thin", alwaysShowScrollbar: 1});
                }
            });
        },
        onShowClearVariant: function() {
            if ($(window).width() < 991) {
                $("#o_wsale_offcanvas form.js_attributes input:checked").each(function() {
                    var self = $(this);
                    var type = ($(self).prop("tagName"));
                    var target_select = self.parents(".nav-item").find("a.te_clear_all_variant_off_canvas");
                    var type_value;
                    if ($(type).is("input")) {
                        type_value = this.value;
                        var first_li = self.closest("ul").find("li").first();
                        var selected_li = self.closest("li.nav-item").find(".nav-link .active");
                        $(first_li).before(selected_li);
                    } else if ($(type).is("select")) {
                        type_value = self.find("option:selected").val();
                    }
                    if (type_value) {
                        target_select.css("display", "inline-block");
                    }
                });
            }
            else {
                $("#products_grid_before form.js_attributes input:checked, #products_grid_before form.js_attributes select").each(function() {
                    var self = $(this);
                    var type = ($(self).prop("tagName"));
                    var type_value, attr_value, attr_value_str, attr_name, target_select, curr_parent, attr_title
                    var target_select = self.parents(".accordion-item.nav-item").find("a.te_clear_all_variant");
                    if ($(type).is("input")) {
                        type_value = this.value;
                        attr_value = $(this).siblings("label").length ? $(this).siblings("label").html() : $(this).parents('label').siblings('label').html();
                        if (attr_value) {
                            attr_value_str = attr_value.toLowerCase();
                            attr_value_str = attr_value_str.replace(/(^\s+|[^a-zA-Z0-9 ]+|\s+$)/g, "");
                            attr_value_str = attr_value_str.replace(/\s+/g, "-");
                        }
                        curr_parent = self.parents(".accordion-item");
                        target_select = curr_parent.find("a.te_clear_all_variant");
                        attr_name = curr_parent.find('.te_clear_all_variant').attr('attribute-name')
                        attr_title = curr_parent.find("span")[0].innerText;
                        if (self.parent("label").hasClass("css_attribute_color")) {
                            attr_value = self.parents('label').siblings('label').html();
                            if (attr_value) {
                                attr_value_str = attr_value.toLowerCase();
                                attr_value_str = attr_value_str.replace(/(^\s+|[^a-zA-Z0-9 ]+|\s+$)/g, "");
                                attr_value_str = attr_value_str.replace(/\s+/g, "-");
                            }
                        }
                        var first_li = self.closest("ul").find("li").first();
                        var selected_li = self.closest(".nav-item").find(".nav-link .active");
                        $(first_li).before(selected_li);
                    } else if ($(type).is("select")) {
                        type_value = self.find("option:selected").val();
                        attr_value = self.find("option:selected").html();
                        if (attr_value) {
                            attr_value_str = attr_value.toLowerCase();
                            attr_value_str = attr_value_str.replace(/(^\s+|[^a-zA-Z0-9 ]+|\s+$)/g, "");
                            attr_value_str = attr_value_str.replace(/\s+/g, "-");
                        }
                        attr_name = self.find("option:selected").parents(".nav-item").find('a.te_clear_all_variant').attr('attribute-name');
                        target_select = self.parents(".nav-item").find("a.te_clear_all_variant");
                        attr_title = self.find("option:selected").parents(".nav-item").find("span")[0].innerText;
                    }
                    if (type_value) {
                        $(".te_product_filters, .te_clear_all_form_selection").css("display", "inline-block");
                        $(".te_view_all_filter_div").css("display", "inline-block");
                        if (target_select) {
                            var temp_attr_value = attr_value.toString().split('(');
                            var cust_attr_value = '';
                            switch (parseInt(temp_attr_value.length)) {
                                case 4:
                                    cust_attr_value += temp_attr_value[0] + ' (' + temp_attr_value[1] + ' (' + temp_attr_value[2];
                                    break;
                                case 3:
                                    cust_attr_value += temp_attr_value[0] + '(' + temp_attr_value[1];
                                    break;
                                default:
                                    cust_attr_value += temp_attr_value[0];
                            }
                            var last_attr_filter = $('.attr_filters').find('.attribute:not(.attr_val)').children().last().find('.attr_title').text();
                            if (last_attr_filter.indexOf(attr_title) != -1) {
                                $(".te_view_all_filter_inner .attr_filters").append("<div class='attribute position-relative attr_val'>" + "<a data-id='" + type_value + "' class='te_clear_attr_a attr-remove " + attr_name + " " + attr_value_str + " '>" + "<span class='position-relative'><span class='attr_value'>" + cust_attr_value + "</span></span></a></div>");
                            } else {
                                $(".te_view_all_filter_inner .attr_filters").append("<div class='attribute position-relative'>" + "<a data-id='" + type_value + "' class='te_clear_attr_a attr-remove " + attr_name + " " + attr_value_str + " '>" + "<span class='attr_title'>" + attr_title + "</span> : <span class='position-relative'><span class='attr_value'>" + cust_attr_value + "</span></span></a></div>");
                            }
                        }
                    }
            });
                $("#products_grid_before form.js_attributes input:checked").each(function() {
                    var self = $(this);
                    var type = ($(self).prop("tagName"));
                    var target_select = self.parents(".nav-item").find("a.te_clear_all_variant");
                    var type_value;
                    if ($(type).is("input")) {
                        type_value = this.value;
                        var first_li = self.closest("ul").find("li").first();
                        var selected_li = self.closest("li.nav-item").find(".nav-link .active");
                        $(first_li).before(selected_li);
                    } else if ($(type).is("select")) {
                        type_value = self.find("option:selected").val();
                    }
                    if (type_value) {
                        target_select.css("display", "inline-block");
                    }
                });
                $("#products_grid_before form.js_attributes .accordion-item select.css_attribute_select").each(function() {
                     var self = $(this);
                     var type = ($(self).prop("tagName"));
                     var target_select = self.parents(".nav-item").find("a.te_clear_all_variant");
                     var type_value;
                     if ($(type).is("input")) {
                         type_value = this.value;
                         var first_li = self.closest("ul").find("li").first();
                         var selected_li = self.closest("li.nav-item").find(".nav-link .active");
                         $(first_li).before(selected_li);
                     } else if ($(type).is("select")) {
                         type_value = self.find("option:selected").val();
                     }
                     if (type_value) {
                         target_select.css("display", "inline-block");
                     }
                 });
            }
        },
        _onClearAttribInd: function(ev) {
            var self = ev.currentTarget;
            var id = $(self).attr("data-id");
            if (id) {
                $("#products_grid_before form.js_attributes option:selected[value=" + id + "]").remove();
                $("#products_grid_before form.js_attributes").find("input[value=" + id + "]").removeAttr("checked")
            }
            this.filterData(ev)
        },
        _onClearAttribAll: function(ev) {
            $("form.js_attributes select").val('');
            $("form.js_attributes").find("input:checked").removeAttr("checked");
            this.filterData(ev);
        },
        _onClearAttribDiv: function(event) {
            /* This method is inherit to clear attribute div */
            var attr_name = $(event.currentTarget).attr('attribute-name');
            var self = event.currentTarget;
            var curent_div = $(self).parents(".nav-item");
            var curr_divinput = $(curent_div).find("input:checked");
            var curr_divselect = $(curent_div).find("option:selected");
            _.each(curr_divselect, function(event) {
                $(curr_divselect).remove();
            });
            _.each(curr_divinput, function(event) {
                $(curr_divinput).removeAttr("checked");
            });
            this.filterData(event);
        },
        filterData: function(event) {
            var target = ($(window).width() > 991) ? $("#products_grid_before form.js_attributes") : $("#o_wsale_offcanvas form.js_attributes")
            target.submit()
        },
    });

    /*======= color attribute click=========== */
    $('div.te_s_attr_color, div.te_s_attr_color label.css_attribute_color').on('click',function() {
        $(this).find('input[type="checkbox"]').trigger('click')
    });

    // Theme layout
    $(document).ready(function($) {
        /* mobile view category collapse class*/
        if ($(window).width() <= 767) {
            $('#o_wsale_offcanvas_categories #o_wsale_cate_accordion2').addClass('show');
        }
        /* Sticky Back To Top */
        $(window).scroll(function(){
            if ($(this).scrollTop() > 100) {
                $('#scroll').fadeIn();
            } else {
                $('#scroll').fadeOut();
            }
        });
        $('.product_details_sticky .prod_add_cart #scroll').click(function(){
            $("html, body").animate({ scrollTop: 0 }, 600);
            return false;
        });

        /* compare page short name */
        var maxLength = 26;
        var number_compare_item = $("#o_comparelist_table").find('tr:first').find('td').length;
        if (number_compare_item == 4) {
            maxLength = 35;
        } else if (number_compare_item == 3) {
            maxLength = 46;
        }
        var ellipsestext = "...";
        $(".more").each(function() {
            var myStr = $(this).text();
            if ($.trim(myStr).length > maxLength) {
                var newStr = myStr.substring(0, maxLength);
                var html = newStr + '<span class="moreellipses">' + ellipsestext + '</span>';
                $(this).html(html);
            }
        });

        /* Full Screen Slider animation on mouse hover */
        var lFollowX = 0,
            lFollowY = 0,
            x = 0,
            y = 0,
            friction = 1 / 30;

        function moveBackground(e) {
            x += (lFollowX - x) * friction;
            y += (lFollowY - y) * friction;
            var translate = 'translate(' + x + 'px, ' + y + 'px) scale(1.1)';
            $('.te_s14_img').css({ '-webit-transform': translate, '-moz-transform': translate, 'transform': translate });
            window.requestAnimationFrame(moveBackground);
        }

        $(window).on('mousemove click', function(e) {
            var lMouseX = Math.max(-100, Math.min(100, $(window).width() / 2 - e.clientX));
            var lMouseY = Math.max(-100, Math.min(100, $(window).height() / 2 - e.clientY));
            lFollowX = (20 * lMouseX) / 100;
            lFollowY = (10 * lMouseY) / 100;
        });
        moveBackground();
        $("#myCarousel_banner_prod_slider").find(".a-submit").click(function(event) {
            sale._onClickSubmit(event)
        });
        /* Full Banner With owl Slider */
        $('.te_banner_slider_content').each(function(index){
            var responsive = { 0: {items: 1}, 576: {items: 1} };
            OwlMixin.initOwlCarousel('.te_banner_slider_content', 10, responsive, true, 1, false, true, false, false, false, false, true, false);
        });

        /** On click selected input, filter will be clear*/
        $('.nav-item input[type="checkbox"]').click(function() {
            if ($(this).prop("checked")) {
                var self = $(this);
                var data_id = self.attr('id') || self.attr('value')
                var attr_value;
                if (self.parent("label").hasClass("css_attribute_color")) {
                    attr_value = self.parent("label").siblings(".te_color-name").html();
                    if (attr_value) {
                        attr_value = attr_value.toLowerCase();
                        attr_value = attr_value.replace(/(^\s+|[^a-zA-Z0-9 ]+|\s+$)/g, "");
                        attr_value = attr_value.replace(/\s+/g, "-");
                    }
                } else {
                    attr_value = self.parents('label').siblings('label').html();
                    if (attr_value) {
                        attr_value = attr_value.toLowerCase();
                        attr_value = attr_value.replace(/(^\s+|[^a-zA-Z0-9 ]+|\s+$)/g, "");
                        attr_value = attr_value.replace(/\s+/g, "-");
                    }
                }
                if (!attr_value) {
                    attr_value = self.parent("label").hasClass("css_attribute_color") ? self.parent("label").siblings(".te_color-name").html() : self.siblings("span").html();
                }
                self.addClass('active');
                $('.te_view_all_filter_div .te_view_all_filter_inner .attr_filters').find('.te_clear_attr_a' +'a[data-id='+ data_id +']').trigger('click');
            }
        });
        $("select").change(function() {
            $(this).find("option:selected").each(function() {
                var attr_value = $(this).parents('.nav-item').find('.te_clear_all_variant').attr('attribute-name');
                var self = $(this);
                var data_id = self.attr('value');
                if(attr_value){
                }
                if (!$(this).text()) {
                    /* ToDo : trigger based on data id */
                    $('.te_view_all_filter_div .te_view_all_filter_inner .attr_filters').find('.te_clear_attr_a.' + +'a[data-id='+ data_id +']').trigger('click');
                }
            });
        });

    });

    /* For counting number */
    sAnimations.registry.NumberCount = sAnimations.Animation.extend({
        selector: '#wrapwrap',
        effects: [{
            startEvents: 'scroll',
            update: '_numberCount',
        }],
        init: function() {
            this._super(...arguments);
            this.viewed = false;
            this.windowWidth = $(window).width();
        },
        _numberCount: function(scroll) {
            if (scroll > 200 && this.isScrolledIntoView($(".te_numbers")) && !this.viewed) {
                this.viewed = true;
                $('.te_count_value').each(function() {
                    $(this).prop('Counter', 0).animate({
                        Counter: $(this).text()
                    }, {
                        duration: 4000,
                        easing: 'swing',
                        step: function(now) {
                            $(this).text(Math.ceil(now));
                        }
                    });
                });
            }
        },
        isScrolledIntoView: function(elem) {
            if (elem.length) {
                var docViewTop = $(window).scrollTop();
                var docViewBottom = docViewTop + $(window).height();
                var elemTop = $(elem).offset().top;
                var elemBottom = elemTop + $(elem).height();
                return ((elemBottom <= docViewBottom) && (elemTop >= docViewTop));
            }
        }
    });

    $(document).on('click', ".quick_close", function(ev) {
            $('#quick_view_model_shop').modal('hide');
            $('#quick_view_model').modal('hide');
            $('#quick_view_model_popup').modal('hide');
            $("#quick_view_model_shop .modal-body, #quick_view_model .modal-body").html('');
    });

    $('#quick_view_model_shop, #quick_view_model').on('hide.bs.modal', function (e) {
        $("#quick_view_model_shop .modal-body, #quick_view_model .modal-body").html('');
    })

    $(document).on('keyup', "#quick_view_model_shop", function(ev) {
        if (ev.keyCode == 27) {
            $("#quick_view_model_shop").model('hide');
        }
    });

    $(document).on('keyup', "#quick_view_model_popup", function(ev) {
        if (ev.keyCode == 27) {
            $("#quick_view_model_popup").model('hide');
        }
    });

    publicWidget.registry.ScrollReview = publicWidget.Widget.extend(OwlMixin, {
        selector: '#wrapwrap',
        events: {
            'click .ept-total-review': 'scroll_review_tab',
        },
        scroll_review_tab: function() {
            if ($(window).width() >= 993) {
                if ($("#nav_tabs_link_ratings").length > 0) {
                    var header_height = 10;
                    if ($('header#top').length && !$('header').hasClass('o_header_sidebar')) {
                        if ($('header nav').hasClass('te_header_navbar')) {
                            this.header_height = $('header nav').height() + 30;
                        } else {
                            this.header_height = $('header').height() + 30;
                        }
                    }
                    var totalHeight = parseInt($("#nav-tab").offset().top) - parseInt(header_height) - parseInt($("#nav-tab").outerHeight());
                    if ($(window).width() < 768)
                        totalHeight += 120;
                    $([document.documentElement, document.body]).animate({
                        scrollTop: totalHeight
                    }, 2000);
                    $('#nav_tabs_link_ratings').trigger('click');
                }
            }
            if ($(window).width() <= 992) {
                if ($("#collapse_ratings").length > 0) {
                    var header_height = 10;
                    if ($('header#top').length && !$('header').hasClass('o_header_sidebar')) {
                        if ($('header nav').hasClass('te_header_navbar')) {
                            this.header_height = $('header nav').height() + 20;
                        } else {
                            this.header_height = $('header').height() + 20;
                        }
                    }
                    var totalHeight = parseInt($("#prd-tab-content").offset().top) - parseInt(header_height) - parseInt($("#prd-tab-content").outerHeight());
                    if ($(window).width() < 768)
                        totalHeight += 120;
                    $([document.documentElement, document.body]).animate({
                        scrollTop: totalHeight
                    }, 2000);
                    $('#collapse_ratings').trigger('click');
                    $("#collapse_ratings").addClass("show");
                }
            }
        }
    });

    /** Responsive menu for mobile view **/
    sAnimations.registry.responsiveMobileHeader = sAnimations.Animation.extend({
        selector: '#wrapwrap',
        read_events: {
            'click .header_sidebar': '_headerSidebar',
            'click .close_top_menu': '_closeLeftHeader',
        },
        init: function() {
            this._super(...arguments);
            this.header_height = 0;
            if ($('.o_main_navbar').length) {
                this.header_height = $('.o_main_navbar').height();
            }
        },
        _headerSidebar: function() {
            $("#top_menu_collapse").addClass("header_menu_slide").css('top', this.header_height).show('slow');
            $("#top_menu_collapse").animate({
                width: '100%'
            });
            $("#wrapwrap").addClass("wrapwrap_trans_header");
        },
        _closeLeftHeader: function() {
            $("#top_menu_collapse").animate({
                width: '0'
            });
            $("#wrapwrap").removeClass("wrapwrap_trans_header");
        }
    });

    // Brand Style 3 Slider For Mobile Screen
    publicWidget.registry.dynamic_snippet.include( {
        _renderContent: function () {
            const $templateArea = this.$el.find('.dynamic_snippet_template');
            this._super.apply(this, arguments);

            $('.s_product_brand_style_3 .dynamic-owl-carousel').each(function(index){
                var $items = $(this);
                var item = $items.attr('data-slide-size') || 1;
                var responsive = { 0: {items: 2}, 576: {items: 3}, 991: {items: 1}, 1200: {items: 1} };
                OwlMixin.initOwlCarousel('.s_product_brand_style_3 .dynamic-owl-carousel', 15, responsive, true, 1, false, true, false, false, false, false, true, false);
            });

            $('.o_wsale_alternative_products .dynamic_snippet_template .dynamic-owl-carousel').each(function(index){
                var $items = $(this);
                var item = $items.attr('data-slide-size') || 1;
                var responsive = { 0: {items: 2}, 576: {items: 3}, 991: {items: 4}, 1200: {items: 4} };
                OwlMixin.initOwlCarousel('.o_wsale_alternative_products .dynamic_snippet_template .dynamic-owl-carousel', 15, responsive, true, 1, false, true, false, false, false, false, true, false);
            });
            var interval = parseInt(this.$target[0].dataset.carouselInterval);
            var mobile_element_count = this.$target[0].dataset.numberOfElementsSmallDevices;
            $('.dynamic-owl-carousel').each(function(index) {
                var owl_rtl = false;
                if ($('#wrapwrap').hasClass('o_rtl')) {
                    owl_rtl = true;
                }
                var $items = $(this);
                var item = $items.attr('data-slide-size') || 1;
                var slider_len = $items.find(".item").length == 0 ? $items.find(".card").length : $items.find(".item").length;
                var getItemLength = slider_len > 4 ? true : false;
                if(slider_len > item){
                    getItemLength = true;
                }
                $items.owlCarousel({
                    loop: getItemLength,
                    margin: 15,
                    nav: true,
                    navText : ['<i class="fa fa-angle-left"></i>','<i class="fa fa-angle-right"></i>'],
                    autoplay: true,
                    autoplayTimeout: interval,
                    autoplayHoverPause:true,
                    items: item,
                    dots: false,
                    rtl: owl_rtl,
                    responsive: {
                        0: {
                            items: mobile_element_count == undefined ? 1 : parseInt(mobile_element_count),
                        },
                        576: {
                            items: item > 1 ? 2 : item,
                        },
                        991: {
                            items: item > 1 ? item - 1 : item,
                        },
                        1200: {
                            items: item,
                        },
                    },
                });
                if ( $items.find('.owl-nav').hasClass('disabled')){
                    $items.find('.owl-nav').show();
                }
            });
            if ($templateArea.find('img.lazyload')){
                $("img.lazyload").lazyload();
            }
            $("img.lazyload").lazyload();

        },
    })

    /* Attribute value tooltip */
    $(function() {
        $('[data-bs-toggle="tooltip"]').tooltip({
            animation: true,
            delay: {
                show: 300,
                hide: 100
            }
        })
    });

    publicWidget.registry.brandPage = publicWidget.Widget.extend(OwlMixin, {
        selector: ".featured-all-brands",
        read_events: {
            'click .has-brands': '_onClickAlpha',
            'click #all-brands': '_showAllBrands',
            'keyup #search_box': '_onKeyupInput'
        },
        _onClickAlpha: function(ev) {
            this.showAllBrands();
            var $this = $(ev.currentTarget);
            var value = $('#search_box').val();
            $this.children().toggleClass('selected');
            var selected_letter_arr = []
            $('.selected').each(function(i) {
                selected_letter_arr.push($.trim($(this).text()))
            });
            if ($.inArray("0-9", selected_letter_arr) != -1){
                selected_letter_arr.push('1', '2', '3', '4', '5', '6', '7', '8', '9');
            }
            $('.brand-alpha-main').each(function(e) {
                var first_letter = $(this).find('.brand-name').text().substring(0, 1).toLowerCase();
                if ($.inArray(first_letter, selected_letter_arr) == -1 & selected_letter_arr.length != 0) {
                    $(this).addClass('d-none');
                }
            });
            if (value) {
                this.removeBlocks(value);
            }
        },
        _showAllBrands: function(ev) {
            $('.selected').removeClass('selected');
            this.showAllBrands();
            var value = $('#search_box').val();
            this.removeBlocks(value);
        },

        _onKeyupInput: function(ev) {
            $('.selected').removeClass('selected');
            var value = $(ev.currentTarget).val();
            this.showAllBrands();
            this.enableBrandBox();
            if (value.length >= 1) {
                this.removeBlocks(value);
                this.disableBox(value);
            }
        },
        showAllBrands: function() {
            $('.brand-alpha-main').each(function(e) {
                $(this).find('.brand-item.d-none').each(function(e) {
                    $(this).removeClass('d-none');
                });
                $(this).removeClass('d-none');
            });
        },
        removeBlocks: function(value) {
            $('.brand-alpha-main').each(function(i) {
                var flag = 0
                $(this).find('.brand-item').each(function(i) {
                    var brand = $(this).find('.brand-name').text()
                    if (brand.toLowerCase().indexOf(value.toLowerCase()) == -1) {
                        $(this).addClass('d-none');
                    }
                    if (!$(this).hasClass('d-none')) {
                        flag = 1;
                    }
                });
                if (flag == 0) {
                    $(this).addClass('d-none');
                }
            });
        },
        enableBrandBox: function() {
            $('.has-brands.active').each(function(i) {
                if ($(this).hasClass('disabled')) {
                    $(this).removeClass('disabled');
                }
            });
        },
        disableBox: function(value) {
            var enabled_array = new Array();
            $('.brand-alpha-main').each(function(i) {
                var flag = 0;
                $(this).find('.brand-item').each(function(i) {
                    if (flag == 0) {
                        var brand = $(this).find('.brand-name').text();
                        if (brand.toLowerCase().indexOf(value.toLowerCase()) != -1) {
                            enabled_array.push($(this).find('.brand-name').text().substring(0, 1).toLowerCase());
                            flag = 1;
                        }
                    } else {
                        return false;
                    }
                });
            });
            if (enabled_array.length == 0) {
                $('.has-brands.active').each(function(i) {
                    $(this).addClass('disabled');
                });
            } else {
                enabled_array.forEach(function(item) {
                    $('.has-brands.active').each(function(i) {
                        if ($.inArray($.trim($(this).children('.brand-alpha').text()), enabled_array) == -1) {
                            $(this).addClass('disabled');
                        }
                    });
                });
            }
        }
    });

    //  Sticky filter in shop page
    sAnimations.registry.StickyFilter = sAnimations.Animation.extend({
        selector: '#wrapwrap',
        effects: [{
            startEvents: 'scroll',
            update: '_stickyFilter',
        }],
        init: function() {
            this._super(...arguments);
            var getClass = $('body').find('.te_shop_filter_resp');
            if (getClass.length > 0){
                this.stickyTop = getClass.offset().top;
            }
        },
         _stickyFilter: function(scroll) {
               if ($(window).width() < 768) {
                    var $stickyFilter = $('.te_shop_filter_resp');
                    if (!!$stickyFilter.offset()) {
                        var sidebar_height = $stickyFilter.innerHeight();
                        var stickyTop = $stickyFilter.offset().top;
                        var windowHeight = $(window).height() - 125;
                        const stickyFilterStyle = { width: window.innerWidth, padding: '0px 15px', margin: '0px -15px', 'background-color': '#FFF', 'z-index': '8' }
                        if ((this.stickyTop < scroll)) {
                            if ($('.o_top_fixed_element').length) {
                                $('.te_shop_pager_top').css({ position: 'sticky', top: $('header').height() }).css(stickyFilterStyle);
                            } else {
                                $('.te_shop_pager_top').css({ position: 'relative', top: 'initial' });
                            }
                        } else {
                            $('.te_shop_pager_top').css({ position: 'relative', top: 'initial' }).css(stickyFilterStyle);
                        }
                    }
               }
        },
    });

    //  Sticky product details
    //function for manage sticky add to cart with live chat button
    function stickyMobileDevice(btnHeight, cookie_height) {
    var pwa_bar = $('.ios-prompt').height();
        setTimeout(function() {
            if ($('.ios-prompt').is(':visible')) {
                var btnHeight = (pwa_bar + btnHeight + 30);
                var cookie_height = (pwa_bar + cookie_height + 30);
            }
        }, 8000);
        $('div#wrapwrap .product_details_sticky').css({ 'display': 'block', 'position': 'fixed', 'bottom': cookie_height + 'px', 'top': 'initial' });
        $('.openerp.o_livechat_button').css({ 'bottom': btnHeight + 'px' });
    }
    //function for manage live chat button
    function chatBtn(btnHeight, cookie_height) {
        if (cookie_height) {
            $('.openerp.o_livechat_button').css({ 'bottom': cookie_height + 'px' });
        } else {
            $('.openerp.o_livechat_button').css({ 'bottom': '0px' });
        }
    }

    sAnimations.registry.StickyGallery = sAnimations.Animation.extend({
        selector: '#wrapwrap',
        effects: [{
            startEvents: 'scroll',
            update: '_stickyDetails',
        }],
        init: function() {
            this._super(...arguments);
            this.$sticky = $('#product_detail .row.te_row_main > .col-lg-6:first-child');
            if ($(this.$sticky).length) {
                this.stickyTop = this.$sticky.offset().top;
            }
            this.header_height = 20;
            if ($('header#top').length && !$('header').hasClass('o_header_sidebar')) {
                if ($('header nav').hasClass('te_header_navbar')) {
                    this.header_height = $('header nav').height() + 20;
                } else {
                    this.header_height = $('header').height() + 20;
                }
            }
        },
        _stickyDetails: function(scroll) {
            if ($(window).width() > 991) {
                if (!!this.$sticky.offset() && this.$sticky) {
                    if (this.stickyTop < scroll + this.header_height + this.header_height) {
                        this.$sticky.css({ position: 'sticky', top: this.header_height });
                        this.$sticky.addClass('sticky-media');
                    } else {
                        this.$sticky.css({ position: 'relative', top: 'initial' });
                        this.$sticky.removeClass('sticky-media');
                    }
                }
                if($('.featured-all-brands').is(':visible')){
                    const headerTopHeight = $('header#top').height();
                    const brandMainSection = $('.featured-all-brands .brand-main').offset().top + headerTopHeight + 220;
                    const eptBrandHeader = $('.featured-all-brands').find('.ept_brands_header');
                    const eptBrandStickyHeader = $('.featured-all-brands').find('.ept_brands_sticky_header');
                    scroll > brandMainSection ? ($(eptBrandHeader).addClass('d-none'), $(eptBrandStickyHeader).removeClass('d-none'), $(eptBrandStickyHeader).css({'position': 'sticky','top': headerTopHeight}))
                                              : ($(eptBrandHeader).removeClass('d-none'), $(eptBrandStickyHeader).addClass('d-none'), $(eptBrandStickyHeader).css({'position': '','top': ''}))
                }
            }
            // Sticky add to cart bar
            if ($('.product_details_sticky').length) {
                if ($('div#product_details a#add_to_cart').length) {
                    var getPriceHtml = $('div#product_details .product_price').html();
                    var stickHeight = $('.product_details_sticky .prod_details_sticky_div').height();
                    var btnHeight = $('div#wrapwrap .product_details_sticky').height();
                    var cookie_height = 0;
                    if ($('.o_cookies_discrete .s_popup_size_full').length) {
                        cookie_height = $('.s_popup_size_full .modal-content').height()
                        stickHeight = cookie_height + stickHeight
                    }

                    var footerPosition = $("main").height() - $("#footer").height();
                    var productDetails = $('#product_details').height() - $('#o_product_terms_and_share').height(); /*- $('.te_p_sku').height() - $('.availability_messages').height();*/
                    if (scroll > productDetails && scroll < footerPosition - 500) {
                        if ($(window).width() >= 768) {
                            $('div#wrapwrap .product_details_sticky').css('bottom', cookie_height + 'px').fadeIn();
                            $('.o_product_feature_panel').css({'bottom':$('.product_details_sticky').height()}).fadeIn();
                        }
                        /* Display prices on add to cart sticky*/
                        if ($(".js_product.js_main_product").hasClass("css_not_available")) {
                            $('div#wrapwrap .prod_price').html('');
                        } else {
                            $('div#wrapwrap .prod_price').html(getPriceHtml);
                        }
                        /* Ipad view only */
                        if ($(window).width() >= 768 && $(window).width() <= 991) {
                            stickyMobileDevice(btnHeight, cookie_height);
                        }
                    } else {
                        if ($(window).width() >= 768) {
                            $('.o_product_feature_panel').css({'bottom':0});
                            $('div#wrapwrap .product_details_sticky').css('bottom', cookie_height + 'px').fadeOut();
                        }
                        if ($(window).width() >= 768 && $(window).width() <= 991) {
                            chatBtn(btnHeight, cookie_height);
                        }
                    }
                    /* Mobile view sticky add to cart */
                    if ($(window).width() <= 767) {
                        var relativeBtn = $('main').height() + $('header').height();
                        if(scroll < relativeBtn){
                            $('#add_to_cart_wrap .js_check_product, .o_we_buy_now').css('display','none');
                            stickyMobileDevice(btnHeight, cookie_height);
                            if($('.o_cookies_discrete').length != 0){
                                 $('.o_cookies_discrete .s_popup_size_full .oe_structure').css({'bottom':$('.product_details_sticky').height()});
                            }
                        }
                        else{
                            $('div#wrapwrap .product_details_sticky').fadeOut();
                            $('.o_cookies_discrete .s_popup_size_full .oe_structure').css({'bottom':0});
                            chatBtn(btnHeight, cookie_height);
                        }
                    }
                }
            }
        },
    });

    // Product tabs in mobile
    sAnimations.registry.productTabs = sAnimations.Class.extend({
        selector: '.product_tabs_ept',
        start: function() {

            var self = this;
            var divLength = $('#nav-tab button').length;
            for(var i=0;i<=divLength-1;i++){
                var selectDesktopTab = $('#nav-tab button')[i].id;
                var selectMobileTab = $('#prd-tab-content .tab-pane')[i].id;
                var selectDesktopDynamicIcon;
                var selectDesktopDynamicName;
                if ($('#'+selectDesktopTab +' ' +'a > span').length) {
                    if ($('#'+selectDesktopTab +' ' +'a > span')[0].classList.contains('fa')) {
                        selectDesktopDynamicIcon = $('#nav-tab #'+selectDesktopTab +' ' +'a > span')[0].className;
                        selectDesktopDynamicName = $('#nav-tab #'+selectDesktopTab +' ' +'a > span')[1].innerText;
                        $('#prd-tab-content #'+ selectMobileTab +' ' + 'a > span')[1].innerText = selectDesktopDynamicName;
                        $('#prd-tab-content #'+ selectMobileTab +' ' + 'a > span')[0].className = selectDesktopDynamicIcon;
                    } else{
                        selectDesktopDynamicIcon = $('#'+selectDesktopTab +' ' +'a > span span')[0].className;
                        $('#prd-tab-content #'+ selectMobileTab +' ' + 'a > span')[0].className = selectDesktopDynamicIcon;
                    }
                }
            }
        }
    });

// tooltip in optional product popup
    OptionalProductsModal.include({
        start: function () {
            this._super.apply(this, arguments);
                $(function () {
                  $('[data-bs-toggle="tooltip"]').tooltip({ animation:true, delay: {show: 300, hide: 100} })
                });
        },
    });

    publicWidget.registry.ProductWishlist.include({
        selector: '#wrapwrap',

    });

    publicWidget.registry.multirangePriceSelector.include({
        _onPriceRangeSelected(ev) {
            $('.cus_theme_loader_layout').removeClass('d-none');
            this._super.apply(this, arguments);
        },
    });

    ProductCategoriesLinks.include({
        _openLink: function (ev) {
            $('.cus_theme_loader_layout').removeClass('d-none');
            this._super.apply(this, arguments);
        },
    });

    /*hotspot setting for basic product card and advance product card*/

    var timeout;
    publicWidget.registry.displayHotspot = publicWidget.Widget.extend({
        selector: ".hotspot_element.display_card",
        events: {
            'mouseenter': '_onMouseEnter',
            'mouseleave': '_onMouseLeave',
        },

        start: function () {
            this.$el.popover({
                trigger: 'manual',
                animation: true,
                html: true,
                container: 'body',
                placement: 'auto',
                sanitize: false,
                template: '<div class="popover hotspot-popover" role="tooltip"><div class="tooltip-arrow"></div><h3 class="popover-header"></h3><div class="popover-body"></div></div>'
            });
            return this._super.apply(this, arguments);
        },

        _onMouseEnter: function (ev) {
            let self = this;
            self.hovered = true;
            clearTimeout(timeout);
            $(this.selector).not(ev.currentTarget).popover('hide');
            timeout = setTimeout(function () {
                self._popoverRPC = $.get("/get-pop-up-product-details", {
                    'product': parseInt($(ev.currentTarget).attr("data-product-template-ids")),
                }).then(function (data) {
                    var WebsiteSale = new publicWidget.registry.WebsiteSale();
                    const popover = Popover.getInstance(self.$el[0]);
                    popover._config.content = data;
                    popover.setContent(popover.getTipElement());
                    self.$el.popover("show");
                    $('.popover').on('mouseleave', function () {
                        self.$el.trigger('mouseleave');
                    });
                    $(".hotspot-popover .a-submit").off('click').on('click',function(ev) {
                        ev.preventDefault();
                        var $form = $(ev.currentTarget).closest('form')
                        WebsiteSale._handleAdd($form);
                    });
                });
            }, 300);
        },

        _onMouseLeave: function (ev) {
            let self = this;
            self.hovered = false;
            setTimeout(function () {
                if ($('.popover:hover').length) {
                    return;
                }
                if (!self.$el.is(':hover')) {
                   self.$el.popover('hide');
                }
            }, 1000);
        },
    });
});
