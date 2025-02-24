odoo.define('izi_web_widget_image_url.TemplateImageURL', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var registry = require('web.field_registry');
    var _t = core._t;

    var UrlImage = AbstractField.extend({
        className: 'o_attachment_image',
        template: 'TemplateImageURL',
        placeholder: "/web/static/src/images/placeholder.png",
        supportedFieldTypes: ['char'],

        url: function () {
            if (this.value) {
                return this.value;    
            } else {
                return this.placeholder;
            }
        },

        _render: function () {
            this._super(arguments);

            var self = this;
            var $img = this.$("img:first");
            $img.on('error', function () {
                $img.attr('src', self.placeholder);
                self.do_warn(
                    _t("Image"), _t("System can not display this image."));
            });
        },
    });

    registry.add('image_url', UrlImage);
});