odoo.define('theme_clarico_vega.website_sale.editor', function (require) {
'use strict';

var options = require('web_editor.snippets.options');
const Wysiwyg = require('website.wysiwyg');
const { ComponentWrapper } = require('web.OwlCompatibility');
const { MediaDialog, MediaDialogWrapper } = require('@web_editor/components/media_dialog/media_dialog');
const { useWowlService } = require('@web/legacy/utils');
const {qweb, _t} = require('web.core');
const {Markup} = require('web.utils');
const Dialog = require('web.Dialog');

options.registry.WebsiteSaleProductsItem = options.Class.extend({
    events: _.extend({}, options.Class.prototype.events || {}, {
        'mouseenter .o_wsale_soptions_menu_sizes table': '_onTableMouseEnter',
        'mouseleave .o_wsale_soptions_menu_sizes table': '_onTableMouseLeave',
        'mouseover .o_wsale_soptions_menu_sizes td': '_onTableItemMouseEnter',
        'click .o_wsale_soptions_menu_sizes td': '_onTableItemClick',
    }),
    willStart: async function () {
        const _super = this._super.bind(this);
        this.ppr = this.$target.closest('[data-ppr]').data('ppr');
        this.productTemplateID = parseInt(this.$target.find('[data-oe-model="product.template"]').data('oe-id'));
        this.ribbons = await new Promise(resolve => this.trigger_up('get_ribbons', {callback: resolve}));
        this.$ribbon = this.$target.find('.o_ribbon');
        return _super(...arguments);
    },

     async _colorStyle(){
        var btpClasses = { "bg-black": '#000000', "bg-white": '#FFFFFF', "bg-o-color-1": '#212529', "bg-o-color-2": '#685563', "bg-o-color-3": '#F6F6F6', "bg-o-color-4": '#FFFFFF', "bg-o-color-5": '#383E45', "bg-900": '#212529', "bg-800": '#343A40', "bg-600": '#6C757D', "bg-400": '#CED4DA', "bg-200": '#E9ECEF', "bg-100": '#F8F9FA', "bg-success": '#198754', "bg-info": '#0dcaf0', "bg-warning": '#ffc107', "bg-danger": '#dc3545'};
        for (var key in btpClasses) {
          if($(this.$ribbon).hasClass(key)){
             $(this.$ribbon).removeClass(key).css('background-color', btpClasses[key]);
          }
        }
     },

    async selectStyle(previewMode, widgetValue, params) {
        const proms = [this._super(...arguments)];
        if($(this.$ribbon).hasClass('o_product_label_style_4_left') || $(this.$ribbon).hasClass('o_product_label_style_4_right')){
            await this._colorStyle();
        }
        if (params.cssProperty === 'background-color' && params.colorNames.includes(widgetValue)) {
            proms.push(this.selectStyle(previewMode, '', {cssProperty: 'color'}));
        }
        await Promise.all(proms);
        if (!previewMode) {
            await this._saveRibbon();
        }
    },
    async setRibbon(previewMode, widgetValue, params) {
        if (previewMode === 'reset') {
            widgetValue = this.prevRibbonId;
        } else {
            this.prevRibbonId = this.$target[0].dataset.ribbonId;
        }
        if (!previewMode) {
            this.ribbonEditMode = false;
        }
        await this._setRibbon(widgetValue);
    },
    editRibbon(previewMode, widgetValue, params) {
        this.ribbonEditMode = !this.ribbonEditMode;
    },
    async createRibbon(previewMode, widgetValue, params) {
        await this._setRibbon(false);
        this.$ribbon.text(_t('Badge Text'));
        this.$ribbon.addClass('bg-primary o_ribbon_left');
        this.ribbonEditMode = true;
        await this._saveRibbon(true);
    },
    async deleteRibbon(previewMode, widgetValue, params) {
        const save = await new Promise(resolve => {
            Dialog.confirm(this, _t('Are you sure you want to delete this badge ?'), {
                confirm_callback: () => resolve(true),
                cancel_callback: () => resolve(false),
            });
        });
        if (!save) {
            return;
        }
        const {ribbonId} = this.$target[0].dataset;
        this.trigger_up('delete_ribbon', {id: ribbonId});
        this.ribbons = await new Promise(resolve => this.trigger_up('get_ribbons', {callback: resolve}));
        this.rerender = true;
        await this._setRibbon(ribbonId);
        this.ribbonEditMode = false;
    },
    async setRibbonHtml(previewMode, widgetValue, params) {
        this.$ribbon.html(widgetValue);
        if (!previewMode) {
            await this._saveRibbon();
        }
    },
    async setRibbonMode(previewMode, widgetValue, params) {
        const classList = this.$ribbon[0].classList;
        const cardProduct = $(this.$target).parents('#products_grid').find('.oe_product_image')
        this.$ribbon[0].className = this.$ribbon[0].className.replace(/o_(ribbon|tag|product_label_style_1|product_label_style_2|product_label_style_3|product_label_style_4|product_label_style_5)_(left|right)/, `o_${widgetValue}_$2`);
        const productStyle = $(this.$target).parents('#products_grid').find('.o_product_label_style_4_left, .o_product_label_style_4_right').parents('.oe_product_image')
        if (this.$ribbon[0].classList.contains('o_ribbon_left') || this.$ribbon[0].classList.contains('o_ribbon_right')){
            $(cardProduct).addClass('overflow-hidden');
            $(productStyle).removeClass('overflow-hidden');
        } else if (this.$ribbon[0].classList.contains('o_product_label_style_4_left') || this.$ribbon[0].classList.contains('o_product_label_style_4_right')){
            $(productStyle).removeClass('overflow-hidden');
            await this._colorStyle();
        }
        await this._saveRibbon();
    },
    async setRibbonPosition(previewMode, widgetValue, params) {
        this.$ribbon[0].className = this.$ribbon[0].className.replace(/o_(ribbon|tag|product_label_style_1|product_label_style_2|product_label_style_3|product_label_style_4|product_label_style_5)_(left|right)/, `o_$1_${widgetValue}`);
        await this._saveRibbon();
    },
    updateUIVisibility: async function () {
        await this._super(...arguments);
        this.$el.find('[data-name="ribbon_customize_opt"]').toggleClass('d-none', !this.ribbonEditMode);
    },
    async _renderCustomXML(uiFragment) {
        const $select = $(uiFragment.querySelector('.o_wsale_ribbon_select'));
        this.ribbons = await new Promise(resolve => this.trigger_up('get_ribbons', {callback: resolve}));
        const classes = this.$ribbon[0].className;
        this.$ribbon[0].className = '';
        const defaultTextColor = window.getComputedStyle(this.$ribbon[0]).color;
        this.$ribbon[0].className = classes;
        Object.values(this.ribbons).forEach(ribbon => {
            const colorClasses = ribbon.html_class.split(' ').filter(className => !/^o_(ribbon|tag|product_label_style_1|product_label_style_2|product_label_style_3|product_label_style_4|product_label_style_5)_(left|right)$/.test(className)).join(' ');
            $select.append(qweb.render('website_sale.ribbonSelectItem', {
                ribbon,
                colorClasses,
                isTag: /o_tag_(left|right)/.test(ribbon.html_class),
                isLeft: /o_(tag|ribbon|product_label_style_1|product_label_style_2|product_label_style_3|product_label_style_4|product_label_style_5)_left/.test(ribbon.html_class),
                textColor: ribbon.text_color || (colorClasses ? 'currentColor' : defaultTextColor),
            }));
        });
    },
    async _computeWidgetState(methodName, params) {
        const classList = this.$ribbon[0].classList;
        switch (methodName) {
            case 'setRibbon':
                return this.$target.attr('data-ribbon-id') || '';
            case 'setRibbonHtml':
                return this.$ribbon.html();
            case 'setRibbonMode': {
                if (classList.contains('o_ribbon_left') || classList.contains('o_ribbon_right')) {
                    return 'ribbon';
                } else if (classList.contains('o_tag_left') || classList.contains('o_tag_right')){
                    return 'tag';
                } else if (classList.contains('o_product_label_style_1_left') || classList.contains('o_product_label_style_1_right')){
                    return 'product_label_style_1';
                } else if (classList.contains('o_product_label_style_2_left') || classList.contains('o_product_label_style_2_right')){
                    return 'product_label_style_2';
                } else if (classList.contains('o_product_label_style_3_left') || classList.contains('o_product_label_style_3_right')){
                    return 'product_label_style_3';
                } else if (classList.contains('o_product_label_style_4_left') || classList.contains('o_product_label_style_4_right')){
                    return 'product_label_style_4';
                } else if (classList.contains('o_product_label_style_5_left') || classList.contains('o_product_label_style_5_right')){
                    return 'product_label_style_5';
                }
            }
            case 'setRibbonPosition': {
                if (classList.contains('o_tag_left') || classList.contains('o_ribbon_left') || classList.contains('o_product_label_style_1_left') || classList.contains('o_product_label_style_2_left') || classList.contains('o_product_label_style_3_left') || classList.contains('o_product_label_style_4_left') || classList.contains('o_product_label_style_5_left')) {
                    return 'left';
                }
                return 'right';
            }
        }
        return this._super(methodName, params);
    },

    async _saveRibbon(isNewRibbon = false) {
        const text = this.$ribbon.html().trim();
        const ribbon = {
            'html': text,
            'bg_color': this.$ribbon[0].style.backgroundColor,
            'text_color': this.$ribbon[0].style.color,
            'html_class': this.$ribbon.attr('class').split(' ').filter(c => !['o_ribbon'].includes(c)).join(' '),
        };
        ribbon.id = isNewRibbon ? Date.now() : parseInt(this.$target.closest('.oe_product')[0].dataset.ribbonId);
        this.trigger_up('set_ribbon', {ribbon: ribbon});
        this.ribbons = await new Promise(resolve => this.trigger_up('get_ribbons', {callback: resolve}));
        this.rerender = true;
        await this._setRibbon(ribbon.id);
    },
    async _setRibbon(ribbonId) {
        this.$target[0].dataset.ribbonId = ribbonId;
        this.trigger_up('set_product_ribbon', {
            templateId: this.productTemplateID,
            ribbonId: ribbonId || false,
        });
        const ribbon = this.ribbons[ribbonId] || {html: '', bg_color: '', text_color: '', html_class: ''};
        const $editableDocument = $(this.$target[0].ownerDocument.body);
        const $ribbons = $editableDocument.find(`[data-ribbon-id="${ribbonId}"] .o_ribbon`);
        $ribbons.empty().append(ribbon.html);
        let htmlClasses;
        this.trigger_up('get_ribbon_classes', {callback: classes => htmlClasses = classes});
        $ribbons.removeClass(htmlClasses);
        $ribbons.addClass(ribbon.html_class || '');
        $ribbons.css({'color': ribbon.text_color || '', 'background-color': ribbon.bg_color || '', 'border-bottom-color': ribbon.bg_color || '', 'border-left-color': ribbon.bg_color || '', 'border-top-color': ribbon.bg_color || ''});
        if (!this.ribbons[ribbonId]) {
            $editableDocument.find(`[data-ribbon-id="${ribbonId}"]`).each((index, product) => delete product.dataset.ribbonId);
        }
    },
    _onTableMouseEnter: function (ev) {
        $(ev.currentTarget).addClass('oe_hover');
    },
    _onTableMouseLeave: function (ev) {
        $(ev.currentTarget).removeClass('oe_hover');
    },
    _onTableItemMouseEnter: function (ev) {
        var $td = $(ev.currentTarget);
        var $table = $td.closest("table");
        var x = $td.index() + 1;
        var y = $td.parent().index() + 1;
        var tr = [];
        for (var yi = 0; yi < y; yi++) {
            tr.push("tr:eq(" + yi + ")");
        }
        var $selectTr = $table.find(tr.join(","));
        var td = [];
        for (var xi = 0; xi < x; xi++) {
            td.push("td:eq(" + xi + ")");
        }
        var $selectTd = $selectTr.find(td.join(","));
        $table.find("td").removeClass("select");
        $selectTd.addClass("select");
    },
    _onTableItemClick: function (ev) {
        var $td = $(ev.currentTarget);
        var x = $td.index() + 1;
        var y = $td.parent().index() + 1
        this._rpc({
            route: '/shop/config/product',
            params: {
                product_id: this.productTemplateID,
                x: x,
                y: y,
            },
        }).then(() => this._reloadEditable());
    },
    _reloadEditable() { return this.trigger_up('request_save', {reload: true, optionSelector: `.oe_product:has(span[data-oe-id=${this.productTemplateID}])`}); }
});
});