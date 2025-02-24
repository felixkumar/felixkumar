odoo.define('slider.builder.helper', function (require) {
'use strict';
var Wysiwyg = require('web_editor.wysiwyg');
var rpc = require('web.rpc');

     Wysiwyg.include({
            start: function () {
                if($('#id_lazyload').length) {
                    $('img.lazyload').each(function(){
                        var getDataSrcVal = $(this).attr('data-src');
                        if(getDataSrcVal == undefined || getDataSrcVal != ''){
                            $(this).attr('src', getDataSrcVal);
                            $(this).attr('data-src', '');
                        }
                    });
                }
                return this._super.apply(this, arguments);
            },
        /**
         * @override
         */
            _saveElement: async function ($el, context, withLang) {
                var promises = [];
                var oldHtml = $el;
                /* Apply Lazyload for all snippet images*/
                if($el.parents().find("#id_lazyload").length) {
                    if(oldHtml){
                        $.each(oldHtml.find('img.lazyload'), function(index, value){
                            var getDataSrcVal = $(value).attr('data-src');
                            var getSrcVal = $(value).attr('src');
                            var getClass = $(value).attr('class');
                            var getWeb = $($el.parents().find(".current_website_id")).val();
                            if(getDataSrcVal == undefined || getDataSrcVal != ''){
                                $(value).attr('src', '/web/image/website/'+ getWeb +'/lazy_load_image');
                                $(value).attr('data-src', getSrcVal);
                            }
                        });
                    }
                }
                var updateHtml = oldHtml[0].outerHTML;
                // Saving a view content
                await this._super.apply(this, arguments);
            }
        });
});
