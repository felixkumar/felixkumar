odoo.define('theme_clarico_vega.snippets.options', function (require) {
'use strict';

    var core = require('web.core');
    const Dialog = require('web.Dialog');
    var Widget = require('web.Widget');
    var weWidgets = require('wysiwyg.widgets');
    const registry = {};
    const options = require('web_editor.snippets.options');

    options.registry.hotspotSetting = options.Class.extend({
        start: function() {
            this.$target.parent().find('.hotspot_element').draggable({
                containment: 'parent', scroll: false, revertDuration: 200, refreshPositions: true,
                stop: function () {
                    var l = ( 100 * parseFloat($(this).position().left / parseFloat($(this).parent().width())) ) + "%" ;
                    var t = ( 100 * parseFloat($(this).position().top / parseFloat($(this).parent().height())) ) + "%" ;
                    $(this).css("left", l);
                    $(this).css("top", t);
                    $(this).find('img').click()
                }
            })
        },
        async setImgHotspot(previewMode, widgetValue, params) {
            if (widgetValue == 'enabled') {
                this.$target.parent().find('.hotspot_element').remove();
                this.$target.parent().append('<section contenteditable="false" name="Hotspot-Block" data-exclude=".s_col_no_resize, .s_col_no_bgcolor" class="hotspot_draggable hotspot_element o_not_editable s_col_no_resize s_col_no_bgcolor fade_hotspot circle"><span class="hotspot_dot"> </span></section>')
                this.trigger_up('activate_snippet', {
                    $snippet: this.$target.parent().find('.hotspot_element'),
                });
            } else {
                this.$target.parent().find('.hotspot_element').remove();
            }
        },
    });

    options.registry.hotspotActions = options.Class.extend({
        start: function () {
            this._super.apply(this, arguments);
            this.$target.draggable({
                containment: 'parent', scroll: false, revertDuration: 200, refreshPositions: true,
                stop: function () {
                    var l = ( 100 * parseFloat($(this).position().left / parseFloat($(this).parent().width())) ) + "%" ;
                    var t = ( 100 * parseFloat($(this).position().top / parseFloat($(this).parent().height())) ) + "%" ;
                    $(this).css("left", l);
                    $(this).css("top", t);
                    $(this).find('img').click()
                }
            })
        },
        onFocus() {
            core.bus.on('activate_image_link_tool', this, this._activateLinkTool);
            core.bus.on('deactivate_image_link_tool', this, this._deactivateLinkTool);
            this.rerender = true;
        },

        onBlur() {
            core.bus.off('activate_image_link_tool', this, this._activateLinkTool);
            core.bus.off('deactivate_image_link_tool', this, this._deactivateLinkTool);
        },

        setLink(previewMode, widgetValue, params) {
            const parentEl = this.$target.find('.hotspot_dot')[0].parentNode;
            if (parentEl.tagName !== 'A') {
                const wrapperEl = document.createElement('a');
                this.$target.find('.hotspot_dot')[0].after(wrapperEl);
                wrapperEl.appendChild(this.$target.find('.hotspot_dot')[0]);
                // TODO Remove when bug fixed in Chrome.
                if (this.$target.find('.hotspot_dot')[0].getBoundingClientRect().width === 0) {
                    // Chrome lost lazy-loaded image => Force Chrome to display image.
                    const src = this.$target.find('.hotspot_dot')[0].src;
                    this.$target.find('.hotspot_dot')[0].src = '';
                    this.$target.find('.hotspot_dot')[0].src = src;
                }
            } else {
                parentEl.replaceWith(this.$target.find('.hotspot_dot')[0]);
            }
        },
        setAction(previewMode, widgetValue, params) {
            const parentEl = this.$target.find('.hotspot_dot')[0].parentNode;
            this.$target.html(this.$target.find('.hotspot_dot')[0]);
            if (widgetValue == 'redirect_product' || widgetValue == 'redirect_url') {
                if (parentEl.tagName !== 'A') {
                    const wrapperEl = document.createElement('a');
                    this.$target.find('.hotspot_dot')[0].after(wrapperEl);
                    wrapperEl.appendChild(this.$target.find('.hotspot_dot')[0]);
                }
                else{
                    const wrapperEl = document.createElement('a');
                    this.$target.find('.hotspot_dot')[0].after(wrapperEl);
                    wrapperEl.appendChild(this.$target.find('.hotspot_dot')[0]);
                }
            }
        },
        setProductLink(previewMode, widgetValue, params) {
            const parentEl = this.$target.find('.hotspot_dot')[0].parentNode;
            if(this.$target[0].classList.contains('redirect_product')) {
                if (parentEl.tagName === 'A'){
                    const wrapperEl = this.$target.find('a')[0];
                    var product_id = this.$target[0].getAttribute('data-product-template-ids')
                    product_id ? wrapperEl.setAttribute('href', '/shop/product/' + product_id) : ''
                }
            } else if(this.$target[0].classList.contains('display_adv_card')) {
            this.$target.attr('data-id', this.$target[0].getAttribute('data-product-template-ids'));
            }
        },

        setNewWindow(previewMode, widgetValue, params) {
            const linkEl = this.$target.find('.hotspot_dot')[0].parentElement;
            if (widgetValue) {
                linkEl.setAttribute('target', '_blank');
            } else {
                linkEl.removeAttribute('target');
            }
        },

        setUrl(previewMode, widgetValue, params) {
            const linkEl = this.$target.find('.hotspot_dot')[0].parentElement;
            let url = widgetValue;
            if (!url) {
                // As long as there is no URL, the image is not considered a link.
                linkEl.removeAttribute('href');
                this.$target.trigger('href_changed');
                return;
            }
            if (!url.startsWith('/') && !url.startsWith('#')
                    && !/^([a-zA-Z]*.):.+$/gm.test(url)) {
                // We permit every protocol (http:, https:, ftp:, mailto:,...).
                // If none is explicitly specified, we assume it is a http.
                url = 'http://' + url;
            }
            linkEl.setAttribute('href', url);
            this.rerender = true;
            this.$target.trigger('href_changed');
        },

        async updateUI() {
            if (this.rerender) {
                this.rerender = false;
                await this._rerenderXML();
                return;
            }
            return this._super.apply(this, arguments);
        },

        _activateLinkTool() {
            if (this.$target.find('.hotspot_dot')[0].parentElement.tagName === 'A') {
                this._requestUserValueWidgets('media_url_opt')[0].focus();
            } else {
                this._requestUserValueWidgets('media_link_opt')[0].enable();
            }
        },

        _deactivateLinkTool() {
            const parentEl = this.$target.children('.hotspot_dot')[0].parentNode;
            if (parentEl.tagName === 'A') {
                this._requestUserValueWidgets('media_link_opt')[0].enable();
            }
        },

        _computeWidgetState(methodName, params) {
            const parentEl = this.$target.find('a');
            var linkEl = parentEl.tagName === 'A' ? parentEl : null;
            if(parentEl.length != 0) {
                linkEl = parentEl[0].tagName === 'A' ? parentEl : null;
            }
            switch (methodName) {
                case 'setLink': {
                    return linkEl ? 'true' : '';
                }
                case 'setUrl': {
                    let href = linkEl ? linkEl[0].getAttribute('href') : '';
                    return href || '';
                }
                case 'setNewWindow': {
                    const target = linkEl ? linkEl[0].getAttribute('target') : '';
                    return target && target === '_blank' ? 'true' : '';
                }
            }
            return this._super(...arguments);
        },

        async _computeWidgetVisibility(widgetName, params) {
            if (widgetName === 'media_link_opt') {
                if (this.$target[0].matches('img')) {
                    return isImageSupportedForStyle(this.$target[0]);
                }
                return !this.$target.find('.hotspot_dot')[0].classList.contains('media_iframe_video');
            }
            return this._super(...arguments);
        },
    });
});
