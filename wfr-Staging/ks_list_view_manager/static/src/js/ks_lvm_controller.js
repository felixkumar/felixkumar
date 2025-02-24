/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { useListener } from "@web/core/utils/hooks";
import { useService } from "@web/core/utils/hooks";
import { browser } from "@web/core/browser/browser";
import { patch } from "@web/core/utils/patch";
import Dialog from 'web.Dialog';
import ajax from 'web.ajax';
import core from 'web.core';
const framework = require('web.framework');
import { qweb, _t } from 'web.core';
import { listView } from '@web/views/list/list_view';
import { registry } from "@web/core/registry";
import { ListArchParser } from "@web/views/list/list_arch_parser";
import session from 'web.session';
const { onWillStart, useState, useRef, onMounted, useExternalListener ,onWillUnmount } = owl;

patch(ListController.prototype, "ks_lvm_controller", {
    setup(params) {
        var self = this;
        this.tableRef = useRef("table");
        if (session.server_version === '16.0+e' && this.env.services.cookie.current.color_scheme === 'dark'){
                document.body.style.setProperty("--ks_lvm_background_color", '#3b3b3b');
        }
        this.ks_fields_data_dirty = {};
        onMounted(this._mounted);
        this.ks_editable = false;
        this.rpc = useService("rpc");
        this.ks_remove_popup_flag = false;
        onWillStart(async () => {
            await this.willStart()
        });
        return this._super(...arguments);
    },
    async willStart() {
        var self = this;
        this.ks_searchdomain = [];
        if ((browser.localStorage.getItem("ks_model"))){
            if ((browser.localStorage.getItem("ks_model")) === this.props.resModel && (browser.localStorage.getItem("search_domain")) && this.env.config.actionId == browser.localStorage.getItem("ks_actionid")){
                this.ks_searchdomain = JSON.parse(browser.localStorage.getItem("search_domain"))
            }else{
                browser.localStorage.removeItem("search_domain");
                browser.localStorage.removeItem("ks_model");
                browser.localStorage.removeItem("field_dict");
                browser.localStorage.removeItem("key_field")
            }
            if (this.ks_searchdomain.length){
            this.ksBaseDomain = [...this.props.domain];
            for (let ks_values of this.ks_searchdomain){
                this.props.domain.push(ks_values);
            }
             this.model.load();
        }
     }
        const data = await ajax.jsonRpc("/ks_lvm_control/ks_generate_arch_view", 'call', {
        'ks_context':this.props.context,
        'ks_model': this.props.resModel,
        'ks_view_id': this.env.config.viewId || false,
        'ks_search_id': this.props.info.searchViewId || false
        });
        if (data) {
            this.data = data;
            this.data.views.list.ks_lvm_user_data['fields'] = data['models'][this.props.resModel];
            this.ks_lvm_data = Object.assign({}, this.data.views.list.ks_lvm_user_data);
            this.currency_id = this.data.views.list.ks_lvm_user_data.ks_lvm_user_mode_data.currency_id;
        }
        this.ks_lvm_data = this.ks_lvm_data ? this.ks_lvm_data : false;
        this.ks_table_data = this.ks_lvm_data && this.ks_lvm_data.ks_lvm_user_table_result ? this.ks_lvm_data.ks_lvm_user_table_result.ks_table_data : false;
        this.ks_lvm_user_mode_data = this.ks_lvm_data ? this.ks_lvm_data.ks_lvm_user_mode_data : false;
        this.ks_user_table_result = this.ks_lvm_data && this.ks_lvm_data.ks_lvm_user_table_result ? this.ks_lvm_data.ks_lvm_user_table_result : false;
        this.userMode = this.ks_lvm_data ? this.ks_lvm_data.ks_lvm_user_mode_data.list_view_data : false;
        this.ks_fields_data = this.ks_user_table_result.ks_fields_data ? self.ks_user_table_result.ks_fields_data : self.ksComputeFieldData(this.props.archInfo, this.props.fields);
        this.ks_field_list = Object.values(this.ks_fields_data).sort((a, b) => a.ks_field_order - b.ks_field_order).sort((a, b) => a.ksShowField === b.ksShowField ? 0: a.ksShowField ? -1: 1);
        this.list_data ={"fields_data":this.ks_fields_data,"currency":this.currency_id,"table_data":this.ks_table_data}
        session.list_data  = this.list_data;

        },
        ksComputeFieldData: function (arch, fields) {
            var ks_field_list = {};
            var self = this;
            //            Making Field List
            var sort_counter = arch.columns.length;
            _.map(fields, function (x, y) {
                if (y !== "activity_exception_decoration") {
                    ks_field_list[y] = {
                        ks_columns_name: x.string,
                        ksShowField: false,
                        field_name: y,
                        ks_width: 0,
                        ks_field_order: sort_counter,
                        ks_tag: 'field'
                    }
                }
            })
            //            Assigning visible/invisible from arch
            sort_counter = 0;
            _.map(arch.columns, function (x) {

                if (x.modifiers !== undefined){
                    var invis = x.modifiers.column_invisible || x.optional === "hide";
                }else{
                    var invis = x.optional === "hide";
                }

                if(x["type"] === "field" || x["type"] === "button_group") {
                    if (ks_field_list.hasOwnProperty(x.name)) {
                        _.extend(ks_field_list[x.name], {
                            ksShowField: !invis,
                            ks_field_order: sort_counter,
                            ks_columns_name: x.string || ks_field_list[x.name].ks_columns_name,
                            ks_tag: 'field'
                        });
                        sort_counter += 1;
                    } else if (x.name) {
                        if (x.tag === "button_group"){
                                ks_field_list[x.name] = {
                                ks_columns_name: x.string || x.name,
                                ksShowField: !invis,
                                field_name: x.name,
                                ks_width: 0,
                                ks_field_order: sort_counter,
                                ks_tag: 'button'
                            }


                    } else {
                        ks_field_list[x.name] = {
                            ks_columns_name: x.string || "Undefined",
                            ksShowField: !invis,
                            field_name: x.name,
                            ks_width: 0,
                            ks_field_order: sort_counter,
                            ks_tag: 'field'
                        }
                    }
                }
            }
        })
        return ks_field_list;
    },


    _mounted() {
        var table = this.tableRef;
      if ($(this.rootRef.el).hasClass("o_action")){
        this.ks_renderButtons();

        this.ks_lvm_mode = true;
        this.ks_resize = false;
        this.ks_lvm_data = {};
        this._ks_init_sortable();
        if(this.ks_table_data.ks_editable == true){
            $("#mode").prop('checked',true);
        }


        document.querySelector('.refresh_button').addEventListener('click', this.ks_reload_list_view.bind(this));
        document.querySelector('.copy_button').addEventListener('click', this._onKsDuplicateRecord.bind(this));
        document.querySelector('#mode').addEventListener('click', this.ks_modeToggle.bind(this));
        document.querySelector('.restore_button').addEventListener('click', this.ks_confirm_restoreData.bind(this));
        document.querySelector(".cancel_button").addEventListener('click', this._onKsCancelButtonClick.bind(this));
        document.querySelector("#ks_dropdown").addEventListener('hide.bs.dropdown', this._onKsHideLvmDropDown.bind(this));
        document.querySelector("#myInput").addEventListener("keyup", this.ks_searchBar.bind(this));
        Object.values(document.querySelectorAll("span.ks_editable")).map((item) => { item.addEventListener('click', this._onKsSpanFieldEditableClick.bind(this)) });
        Object.values(document.querySelectorAll("input.ks_editable")).map((item) => { item.addEventListener('focusout', this._onKsInputFieldEditableFocusout.bind(this)) });

        if (!this.ks_lvm_user_mode_data.ks_can_edit){
            $('.mode_button').addClass('d-none')
        }
        if (!this.ks_lvm_user_mode_data.ks_dynamic_list_show){
            $('.toggle_button').parent().addClass('d-none');
        }
    }
    },

    ks_renderButtons: function () {

        // Todo: Make this as a sub-component.
        var $lvmButtons = $(qweb.render('ks_ListView.buttons', { widget: this }));
        if ($('#ks_dropdown').length == 0) {
            $lvmButtons.appendTo($('.o_list_buttons'));
            this._ks_init_sortable();
        }

        //            this.renderer.on_attach_callback();
    },

    _ks_init_sortable() {
        if (this.ks_lvm_mode) {
            var self = this;
            $(".ks_columns_list").sortable({
                axis: 'y',
                update: function (event, ui) {
                    self._ks_update_fields_order(event, ui);
                }
            });
        if (session.ks_toggle_color) {
             $("input:checked + .ks_slider").css("background-color", session.ks_toggle_color);
        }
        }
    },

    ks_searchBar(e) {
        if ($(e.target).hasClass("myinput")) {
            if (this.ks_lvm_mode) {
                var ks_input = e.target.value.toUpperCase();
                _.map($(".ks_columns_list").children(), function ($field) {
                    $field.style.display = $field.dataset.ks_columns_name.toUpperCase().indexOf(ks_input) > -1 ? "" : "none";
                })
            }
        }
    },

    ks_reload_list_view: function () {

        this.props.context['default_fields'] = this.model.rootParams.fields
        var order_records_ids = [];
        var order_records = this.model.root.records
        for (var i = 0; i < order_records.length; i++) {
            order_records_ids.push(order_records[i].resId);
        }
        if (this.ks_lvm_mode) {
            var ks_update_params = {};
            ks_update_params["modelName"] = this.model.rootParams.resModel;
            ks_update_params["context"] = this.props.context;
            ks_update_params["ids"] = order_records_ids;
            ks_update_params["offset"] = this.model.root.offset;
            ks_update_params["selectRecords"] = this.model.root.selection;
            ks_update_params["groupBy"] = this.model.root.groupBy;
            ks_update_params["domain"] = this.model.root.domain;
            this.ks_update(ks_update_params);
        }
    },

    async ks_update(params) {
        const list = this.model.root
        await list.load();
        this.render(true);
    },

    _onKsDuplicateRecord: function () {
        if (this.ks_lvm_mode) {
            var self = this;
            const resIds = this.model.root.selection.map((record) => record.resId);
            ajax.jsonRpc('/ks_lvm_control/ks_duplicate_list_records', 'call', {
                'ks_model': this.props.resModel,
                'ks_record_ids': resIds || [],
            }).then(function (res) {
                $(".refresh_button").removeClass("d-none");
                $(".toggle_button").removeClass("d-none");
                $(".mode_button").removeClass("d-none");
                $('.copy_button').hide();
                self.ks_update();
            });
        }
        console.log("Duplicate record");
    },

    // Update Field Status in LVM DB. TODO: Add condition to either update data or not
    ks_update_field_data(ks_table_data, ks_field_data, ks_reset_renderer) {
        if (this.ks_lvm_mode) {
            var self = this;
            if (!self.ks_table_data) {
                return self.ks_initialize_lvm_data(this.ks_fields_data);
            }

            var ks_reset_renderer = ks_reset_renderer;
            //            Condition to fetch data or not

            var ks_fetch_options = {
                'ks_context':this.props.context,
                'ks_model': this.props.resModel,
                'ks_view_id': this.env.config.viewId || false,
                'ks_search_id': self.props.info.searchViewId
            }

            if (ks_reset_renderer) framework.blockUI();
           return ajax.jsonRpc('/ks_lvm_control/update_list_view_data', 'call', {
                'ks_table_data': ks_table_data,
                'ks_fields_data': ks_field_data,
                'ks_fetch_options': ks_fetch_options,


            }).then(function (ks_list_view_data) {
                if (ks_reset_renderer) {
                    var archInfo = new ListArchParser().parse(ks_list_view_data.views.list.arch, self.props.relatedModels, self.props.resModel);
                    Object.assign(self.archInfo, archInfo);
                    Object.assign(self.model.root.activeFields, self.archInfo.activeFields);
                    self.ks_resize = false;
                    framework.unblockUI();
                    self.ks_update(ks_list_view_data);
                    self.env.bus.trigger("CLEAR-CACHES");
                };
            });

        }
    },


    // Initialize LVM data in Database
    ks_initialize_lvm_data: function (ks_fields_data) {
        if (this.ks_lvm_mode) {
            var self = this;
            var ks_table_width_px = $('.o_list_table').width();
            //patchy code to convert float number up to two decimal precisions
            var ks_table_width_per = +(((ks_table_width_px / $(window).width()) * 100).toFixed(14));

              return  ajax.jsonRpc("/ks_lvm_control/create_list_view_data", "call", {
                    ks_context :this.props.context,
                    ks_model: this.model.root.resModel,
                    ks_editable: this.ks_editable,
                    ks_view_id: this.env.config.viewId || false,
                    ks_table_width_per: ks_table_width_per || 99.45,
                    ks_fields_data: ks_fields_data,
                    ks_resize: self.ks_resize,
                    ks_search_id: self.props.info.searchViewId,
                })
                .then(function (ks_list_view_data) {
                    self.ks_table_data = ks_list_view_data.views.list.ks_lvm_user_data.ks_lvm_user_table_result.ks_table_data;
                    self.ks_fields_data = ks_list_view_data.views.list.ks_lvm_user_data.ks_lvm_user_table_result.ks_fields_data;
                    self.list_data.fields_data = self.ks_fields_data;
                    self.list_data.table_data = self.ks_table_data;
                    self.ks_resize = false;
                    self.ks_field_list = Object.values(self.ks_fields_data).sort((a, b) => a.ks_field_order - b.ks_field_order);
                    var archInfo = new ListArchParser().parse(ks_list_view_data.views.list.arch, self.props.relatedModels, self.props.resModel);
                    Object.assign(self.archInfo, archInfo),
                    Object.assign(self.model.root.activeFields, self.archInfo.activeFields);
                    self.ks_update(ks_list_view_data);
                    self.env.bus.trigger("CLEAR-CACHES");

                });
        }

    },


    ks_modeToggle: function (ev) {
        if (this.ks_lvm_mode) {
            var self = this;
            var ks_table_data_list = [];
            this.ks_editable = ev.target.checked;
            if (this.ks_table_data) {
                this.ks_table_data.ks_editable = ev.target.checked;
                ks_table_data_list = [this.ks_table_data]
            };

            if (!self.ks_table_data) {
                return self.ks_initialize_lvm_data(self.ks_fields_data);
            }

            this.ks_update_field_data(ks_table_data_list, [], true)
                self.editable = self.ks_editable ? "top" : false;

        }
        console.log("Inline Editing");
    },



    ks_confirm_restoreData: function (event) {
        if (this.ks_lvm_mode) {
        var self = this;
        self.ks_resize = false;
        Dialog.confirm(this, _t("Are you sure you want to restore to Odoo default View?"), {
            confirm_callback: function () {
            self.ks_is_restore_flag = true;
            self.ksResetLvmData();
                console.log("Confirm");
            }
        });
        }
    },
    ksResetLvmData: function () {
            if (this.ks_lvm_mode) {
                var self = this;
                if (this.ks_table_data) {
                    return ajax.jsonRpc("/ks_lvm_control/ks_reset_list_view_data","call",{
                            'ks_context':this.props.context,
                            'ks_model': this.model.root.resModel,
                            'ks_view_id': this.env.config.viewId || false,
                            'ks_lvm_table_id': this.ks_table_data.id,
                            'ks_search_view_id': self.props.info.searchViewId
                        }).then(function (ks_list_view_data) {
                            self.KsResetControllerData(ks_list_view_data);

                    });
                }
                return $.when();
            }
        },
         KsResetControllerData(data) {
            if (this.ks_lvm_mode) {
                var self = this;
                if (data){
                    this.data = data;
                    this.data.views.list.ks_lvm_user_data['fields'] = data['models'][this.props.resModel];
                    this.ks_lvm_data = Object.assign({}, this.data.views.list.ks_lvm_user_data);
                    this.currency_id = this.data.views.list.ks_lvm_user_data.ks_lvm_user_mode_data.currency_id;
                }
            var archInfo = new ListArchParser().parse(data.views.list.arch, self.props.relatedModels, self.props.resModel);
            Object.assign(self.archInfo, archInfo),
            Object.assign(self.model.root.activeFields, self.archInfo.activeFields);
            self.ks_update(data);
            self.env.bus.trigger("CLEAR-CACHES");
            this.ks_lvm_data = this.ks_lvm_data ? this.ks_lvm_data : false;
            this.ks_table_data = this.ks_lvm_data && this.ks_lvm_data.ks_lvm_user_table_result ? this.ks_lvm_data.ks_lvm_user_table_result.ks_table_data : false;
            this.ks_lvm_user_mode_data = this.ks_lvm_data ? this.ks_lvm_data.ks_lvm_user_mode_data : false;
            this.ks_user_table_result = this.ks_lvm_data && this.ks_lvm_data.ks_lvm_user_table_result ? this.ks_lvm_data.ks_lvm_user_table_result : false;
            this.userMode = this.ks_lvm_data ? this.ks_lvm_data.ks_lvm_user_mode_data.list_view_data : false;
            this.ks_fields_data = this.ks_user_table_result.ks_fields_data ? self.ks_user_table_result.ks_fields_data : self.ksComputeFieldData(this.props.archInfo, this.props.fields);
            this.ks_field_list = Object.values(this.ks_fields_data).sort((a, b) => a.ks_field_order - b.ks_field_order);
            this.list_data ={"fields_data":this.ks_fields_data,"currency":this.currency_id,"table_data":this.ks_table_data}
            this.ks_lvm_user_mode_data = false;
            if ($(".ks_columns").length) {
                $(".ks_columns_list").remove();

                $(".ks-text-center").remove();
                var $ks_column_list = $(qweb.render("ks_list_view_fields_selection_list", {
                        widget: this
                }));
                $(".ks_columns").append($ks_column_list);
                self._ks_init_sortable();

                }
                 $("#mode").prop('checked',false);
                 this.editable = null;
             Object.values(document.querySelectorAll("span.ks_editable")).map((item) => { item.addEventListener('click', this._onKsSpanFieldEditableClick.bind(this)) });
             Object.values(document.querySelectorAll("input.ks_editable")).map((item) => { item.addEventListener('focusout', this._onKsInputFieldEditableFocusout.bind(this)) });


            }
        },



    _onKsSpanFieldEditableClick(event) {
        if ($(event.target).hasClass("ks_editable_span")) {
            if (this.ks_lvm_mode) {
                event.stopPropagation();
                var self = this;
                var ks_field_id = event.target.dataset.fieldId;
                var $field_span_el = $(event.target);
                var $field_input_el = $(this.rootRef.el).find('input.ks_editable[data-field-id=' + ks_field_id + ']');
                var name = this.ks_fields_data[ks_field_id].ks_columns_name;
                $field_input_el.val(name);
                $field_span_el.hide();
                $field_input_el.removeClass("d-none");
                $field_input_el.focus();
                $(".cancel_button").removeClass("d-none");
            }
        }
    },

    _onKsInputFieldEditableFocusout(event) {
        if ($(event.target).hasClass("ks_editable_input")) {
            if (this.ks_lvm_mode) {
                event.stopPropagation();
                var self = this;
                var ks_field_id = event.target.dataset.fieldId;
                var $field_span_el = $(self.rootRef.el).find('span.ks_editable[data-field-id=' + ks_field_id + ']');
                var $field_input_el = $(event.target)
                var name = self.ks_fields_data[ks_field_id].ks_columns_name;
                var input_val = $field_input_el.val();

                if (input_val.length !== 0) {
                    $field_span_el.text(input_val);
                    self.ks_fields_data_dirty[ks_field_id] = _.extend({}, self.ks_fields_data_dirty[ks_field_id], {
                        ks_columns_name: input_val,
                        id: self.ks_fields_data[ks_field_id].id,
                    })
                }
                $field_span_el.show();
                $field_input_el.addClass("d-none");
            }
        }
    },
    _onKsCancelButtonClick(event) {
        if ($(event.target).hasClass("cancel_button")) {
            if (this.ks_lvm_mode) {
                event.stopPropagation();
                var self = this;
                _.map(Object.keys(self.ks_fields_data_dirty), function (ks_field_id) {
                    var $field_span_el = $(self.rootRef.el).find('span.ks_editable[data-field-id=' + ks_field_id + ']');
                    var name = self.ks_fields_data[ks_field_id].ks_columns_name;
                    $field_span_el.text(name);
                });
                self.ks_fields_data_dirty = {};
                $(".cancel_button").addClass("d-none");
            }
        }
    },
    _onKsHideLvmDropDown(event) {
        if ($(event.target).hasClass("dropdown-toggle")) {
            if (this.ks_lvm_mode) {
                event.stopPropagation();
                var self = this;

                // Box Hide Reset View
                $(".cancel_button").addClass("d-none");
                $("#myInput").val("");
                _.map($(".ks_columns_list").children(), function ($field) {
                    $field.style.display = "";
                })

                // Hack code to control drop down button click again when drop down is active
                if (!event.hasOwnProperty("clickEvent")) return false;

                // Handle BS hide : Write Dirty Data
                if (!$(".ks_lvm_dd").has(event.clickEvent.target).length > 0) {
                    if (Object.keys(self.ks_fields_data_dirty).length > 0 && !self.ks_is_restore_flag) {
                        var ks_update_field_list = [];
                        _.map(self.ks_fields_data_dirty, function (value, key) {
                            ks_update_field_list.push(value);
                            self.ks_fields_data[key]['ks_columns_name'] = value['ks_columns_name'];
                        })
                        self.ks_update_field_data([], ks_update_field_list, true)
                    }
                    self.ks_is_restore_flag = false;
                    self.ks_fields_data_dirty = {};
                }
                return !$(".ks_lvm_dd").has(event.clickEvent.target).length > 0;
            }
        }
    },
    _ks_update_fields_order(event, ui) {
        if (this.ks_lvm_mode) {
            var self = this;
            var sort_counter = 0;
            _.map($(".ks_columns_list").children(), function ($field) {
                if(self.ks_fields_data[$field.dataset.field_name]){
                self.ks_fields_data[$field.dataset.field_name].ks_field_order = sort_counter;
                sort_counter += 1;
                }
            })

            if (!self.ks_table_data) {
                return self.ks_initialize_lvm_data(self.ks_fields_data);
            }

            self.ks_update_field_data([], Object.values(self.ks_fields_data), true);
        }
    },




});