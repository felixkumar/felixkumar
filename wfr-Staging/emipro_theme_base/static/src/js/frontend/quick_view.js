odoo.define('emipro_theme_base.quick_view', function(require) {
    'use strict';

    var sAnimations = require('website.content.snippets.animation');
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var WebsiteSale = publicWidget.registry.WebsiteSale;
    var core = require('web.core');
    var QWeb = core.qweb;
    var Dialog = require('web.Dialog');
    var _t = core._t;


    publicWidget.registry.quickView = publicWidget.Widget.extend({
        selector: "#wrapwrap",
        events: {
            'click .quick-view-a': 'initQuickView',
            'click .ajax_cart_popup': 'initQuickView',
        },
        initQuickView: function(ev) {
            /* This method is called while click on the quick view icon
             and show the model and quick view data */
            ev.preventDefault()
            self = this;
            var element = ev.currentTarget;
            var product_id = $(element).attr('data-id');
            if (product_id){
                ajax.jsonRpc('/quick_view_item_data', 'call',{'product_id':product_id}).then(function(data) {
                    if($("#wrap").hasClass('js_sale'))
                    {
                        $("#quick_view_model_shop .modal-body").html(data);
                        $('#quick_view_model_shop').modal('show');
                    }else {
                        $("#quick_view_model .modal-body").html(data);
                        $('#quick_view_model').modal('show');
                    }
                    var WebsiteSale = new publicWidget.registry.WebsiteSale();

                    WebsiteSale.init();
                    WebsiteSale._startZoom();
                    var combination = [];

                    setTimeout(function(){
                        var quantity = $('.quick_view_content').find('.quantity').val();
                        $('.quick_view_content').find('.quantity').val(quantity).trigger('change');

                    }, 200);
                    $('.variant_attribute  .list-inline-item').find('.active').parent().addClass('active_li');
                    $( ".list-inline-item .css_attribute_color" ).change(function(ev) {
                        var $parent = $(ev.target).closest('.js_product');
                        $parent.find('.css_attribute_color').parent('.list-inline-item').removeClass("active_li");
                        $parent.find('.css_attribute_color').filter(':has(input:checked)').parent('.list-inline-item').addClass("active_li");
                    });

                    /* Attribute value tooltip */
                    $(function () {
                      $('[data-bs-toggle="tooltip"]').tooltip({ animation:true, delay: {show: 300, hide: 100} })
                    });

                });
            }
        },
    });


});
