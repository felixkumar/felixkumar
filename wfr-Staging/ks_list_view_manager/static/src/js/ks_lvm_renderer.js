/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
import { browser } from "@web/core/browser/browser";
import { qweb, _t } from 'web.core';
//import { DateTimePicker } from '@web/core/datepicker/datepicker';
const datepicker = require("web.datepicker");
import { DateWidget, DateTimeWidget } from 'web.datepicker';
import session from 'web.session';
import fieldUtils from 'web.field_utils';
import { useService } from "@web/core/utils/hooks";
import ajax from 'web.ajax';
const framework = require('web.framework');
import { ListArchParser } from "@web/views/list/list_arch_parser";
const { onWillStart, useState, useRef, onMounted, onWillPatch, onPatched, useExternalListener, onWillUpdateProps, onWillUnmount ,onWillRender } = owl;


patch(ListRenderer.prototype, "ks_lvm_renderer", {
    setup() {
        var self = this;
        this.ks_call_flag = 1;
        this.ks_serial_number = session.ks_serial_number;
        this.notification = useService("notification");
        this.rpc = useService("rpc");
        this.ks_datepicker_flag = 0
        this.ksDomain = null;
        this.mydomain = null;
        this.ks_allow_search = true;
        this.ks_field_popup = {};
        this.ks_autocomplete_data = {};
        this.ks_autocomplete_data_result = {};
        this.ks_lvm_mode = true;
        this.ks_remove_popup_flag = false;
        this.ks_key_fields = [];
        this.ks_field_domain_list = [];
        this.ks_field_domain_dict = {};
        this.ksBaseDomain = null;
        this.ks_advance_search_refresh = false;
        this.ks_start_date = undefined;
        this.ks_end_date = undefined;
        this.ks_start_date_id = undefined;
        this.ks_end_date_id = undefined;
        this.datepicker;
        this.ks_editable = false;
        if (this.props.list.domain){
        this.default_domain = [...this.props.list.model.root.domain]
        this.ks_search_domain = [...this.props.list.domain]
        };
        if(this.env.searchModel && this.env.searchModel.globalDomain){
        this.search_default=[...this.env.searchModel.globalDomain]
        };
        this.ks_list_data = this.props.list_data ? this.props.list_data : session.list_data

        this.tableRef = useRef("table");
        this.ks_is_lines = true;

        if (this.props.activeActions.type == 'view') {
            this.ks_is_lines = false;
            onMounted(this._mounted);
            onWillUpdateProps((next_prop) => {
                this.keepColumnWidths = false;
                this.allColumns = next_prop.archInfo.columns;
                this.getOptionalActiveFields();
                this.state.columns = this.getActiveColumns(next_prop.list);
                this._mounted();

            });
            onWillStart(async () => {
                 this.willStart()
            });
    }

        // Todo: Remove this as useExternalListener and follow the proper approach.
        useExternalListener(document, 'keyup', this.ks_advance_searchbar.bind(this))
        useExternalListener(document, 'click', this.ks_remove_popup_domain_event.bind(this))
        useExternalListener(document, 'change', this.ks_change_event.bind(this))
        useExternalListener(document, 'click', this._onKsFieldActiveClickrender.bind(this))
        browser.addEventListener("beforeunload", this.clearLocalStorage);

        return this._super(...arguments);
    },
     async willStart() {
        var self= this;
        this.ks_searchdomain = [];
        if ((browser.localStorage.getItem("ks_model"))){
            if ((browser.localStorage.getItem("ks_model")) === this.props.list.model.root.resModel && (browser.localStorage.getItem("search_domain")) && this.env.config.actionId == browser.localStorage.getItem("ks_actionid")){
                this.ks_searchdomain = JSON.parse(browser.localStorage.getItem("search_domain"))
            }else{
                browser.localStorage.getItem("ks_actionid");
                browser.localStorage.removeItem("search_domain");
                browser.localStorage.removeItem("ks_model");
                browser.localStorage.removeItem("field_dict");
                browser.localStorage.removeItem("key_field")
            }
            if (this.ks_searchdomain.length){
            this.ksBaseDomain = [...this.props.list.domain];
            for (let ks_values of this.ks_searchdomain){
                this.props.list.model.root.domain.push(ks_values);
                this.env.searchModel.globalDomain.push(ks_values);
            }

            this.ks_search_domain = this.props.list.model.root.domain;
            this.ksDomain = this.ks_searchdomain;
            this.ks_field_domain_list = this.ks_searchdomain;
            this.ks_field_domain_dict = JSON.parse(browser.localStorage.getItem("field_dict"));
            this.ks_key_fields = JSON.parse(browser.localStorage.getItem("key_field"))
            this.ks_advance_search_refresh = true;
            this.ks_key_insert_flag =false;

        }
     }
    },




    async _mounted() {
        var self = this;
        var table = this.tableRef
        this.ks_allow_search = true;
        self.ks_call_flag = 1;
        self.ks_field_popup = {};
        if($(table.el).parents().find(".modal-header").length == 0){
        if (session.ks_serial_number &&  table.el.querySelector(".o_list_record_selector").cellIndex ==0){
        $(table.el.querySelector("tr")).prepend($("<th>S.No</th>"));
        $(table.el.tFoot.querySelector("tr")).prepend($("<td></td>"))
        }
        }
        if (self.ksDomain != null) {
            for (var i = 0; i < self.ksDomain.length; i++) {
                if (!(self.ksDomain[i] === '|')) {
                    if (self.ks_field_popup[self.ksDomain[i][0]] === undefined) {
                        self.ks_field_popup[self.ksDomain[i][0]] = [self.ksDomain[i][2]]
                    } else {
                        self.ks_field_popup[self.ksDomain[i][0]].push(self.ksDomain[i][2])
                    }
                }
            }
        }
        var $tr = $('<tr>').append(_.map(self.state.columns, self.ks_textBox.bind(self)));
        if (self.hasSelectors) {
            $tr.prepend($('<th>'));
        }
        if (session.ks_serial_number){
            $tr.prepend($('<th>'));
        }


        if (session.ks_can_advanced_search){
            $tr.addClass('hide-on-modal')
            if ($(table.el).find("tr.hide-on-modal").length!=0){
                $(table.el.querySelectorAll("tr.hide-on-modal")).remove()
                $(table.el.querySelectorAll("thead")).append($tr);

            }else{
                $(table.el.querySelectorAll("thead")).append($tr);
            }
        }
        $($(table.el.querySelectorAll("thead tr"))[0]).addClass("bg-primary");
        if(document.querySelector(".o_list_controller.o_list_actions_header")){
            $(document.querySelector(".o_list_controller.o_list_actions_header")).addClass("d-none")
        }




    },
    clearLocalStorage(){
        browser.localStorage.removeItem("search_domain");
        browser.localStorage.removeItem("ks_model");
        browser.localStorage.removeItem("field_dict");
        browser.localStorage.removeItem("key_field");
        browser.localStorage.getItem("ks_actionid")
    },


    //    Too manage the hide and show of duplicate record button
    getRowClass(record) {
        var classNames = this._super(...arguments);
        if (this.props.list.selection && this.props.list.selection.length > 0) {
            $('.copy_button').css('display', 'block')

        } else {
            $('.copy_button').css('display', 'none');
        }
        if (record.selected) {
            $('.o_data_row[data-id="' + record.id + '"]').addClass('ks_highlight_row');
            classNames = "o_data_row_selected"
        }
        return classNames;
    },

    toggleSelection() {
        this._super(...arguments);
        if (this.props.list.selection && this.props.list.selection.length === 0) {
            $('.o_data_row').removeClass('ks_highlight_row');
            $('.o_data_row').addClass('text-info');
        }
    },

    toggleRecordSelection(record) {
        this._super(...arguments);
        if (!record.selected) {
            $('.o_data_row[data-id="' + record.id + '"]').removeClass('ks_highlight_row');
            $('.o_data_row[data-id="' + record.id + '"]').addClass('text-info');
        }
    },
     onClickCapture(record, ev) {
     this._super(...arguments);
     if ($(ev.target).hasClass("o_priority_star") && $(ev.currentTarget).hasClass("ks_highlight_row")){
     $(document.querySelectorAll(".ks_highlight_row")).removeClass("ks_highlight_row")
     }
     },



        freezeColumnWidths() {
            if (!this.ks_is_lines){
                var tableRef = this.tableRef;
        //        const headers = [...tableRef.el.querySelectorAll("thead .bg-primary th:not(.o_list_actions_header)")];
                $(tableRef.el).hasClass('o_field_many2many')
                if (session.ks_header_text_color !="white"){
                    var ks_header_text_color = session.ks_header_text_color;
                    $(tableRef.el.querySelectorAll("thead .bg-primary")).find("th").addClass('ks_header_text_color').css('color', ks_header_text_color + ' !important')
                }
                if (session.ks_header_color){
                    var ks_header_color = session.ks_header_color;
                    (tableRef.el.querySelectorAll("thead .bg-primary th")).forEach((item) =>{item.style.setProperty("background-color", session.ks_header_color, "important")})
                }
                if (tableRef.el && ($(tableRef.el).hasClass('o_field_one2many') !== false || $(tableRef.el).hasClass('o_field_many2many') !== false)) {
                    this._super();
                }
                if (!this.keepColumnWidths) {
                    this.columnWidths = null;
                }

                if ($('.o_optional_columns_dropdown').length === 1 && !session.ks_dynamic_list_show) {
                    $('.o_optional_columns_dropdown').parent().removeClass('d-none');
                }

                const headers = [...tableRef.el.querySelectorAll("thead .bg-primary th:not(.o_list_actions_header)")];

                if (!this.columnWidths || !this.columnWidths.length) {
                    tableRef.el.style.tableLayout = "auto";
                    headers.forEach((th) => {
                        th.style.width = null;
                        th.style.maxWidth = null;
                    });

                    this.setDefaultColumnWidths();

                    this.columnWidths = this.computeColumnWidthsFromContent();
                    tableRef.el.style.tableLayout = "fixed";
                }

                headers.forEach((th, index) => {
                    if (!th.style.width) {
                        th.style.width = `${Math.floor(this.columnWidths[index])}px`;
                    }
                    if(!parseInt(th.style.width)|| th.style.width == "100%"){
                     th.style.width = '';
                     th.style['max-width'] = '';
                     }
                });

                if (this.props.activeActions && this.props.activeActions.type === 'view') {
                    this.allColumns.forEach((item) =>{
                       if(item.rawAttrs && item.rawAttrs.width !== undefined &&  parseInt(item.rawAttrs.width) && $("thead .bg-primary th[data-name="+item.name+"]").length > 0){
                            $("thead .bg-primary th[data-name="+item.name+"]")[0].style.width = `${Math.floor(parseInt(item.rawAttrs.width))}px`;
                            $("thead .bg-primary th[data-name="+item.name+"]")[0].style['max-width'] = `${Math.floor(parseInt(item.rawAttrs.width))}px`;
                        }

                    });
                }

                for (let item of (tableRef.el.querySelectorAll("thead .bg-primary th"))){
                    if(!parseInt(item.style.width)){
                        tableRef.el.querySelector("thead").parentElement.style.tableLayout="auto";
                    break;
                }
                }
            }else{
                this._super();
            }
        },
        computeColumnWidthsFromContent() {

            if (!this.ks_is_lines){

                const table = this.tableRef.el;

                // Toggle a className used to remove style that could interfere with the ideal width
                // computation algorithm (e.g. prevent text fields from being wrapped during the
                // computation, to prevent them from being completely crushed)
                table.classList.add("o_list_computing_widths");

                const headers = [...table.querySelectorAll("thead .bg-primary th")];
                const columnWidths = headers.map((th) => th.getBoundingClientRect().width);
                const getWidth = (th) => columnWidths[headers.indexOf(th)] || 0;
                const getTotalWidth = () => columnWidths.reduce((tot, width) => tot + width, 0);
                const shrinkColumns = (thsToShrink, shrinkAmount) => {
                    let canKeepShrinking = true;
                    for (const th of thsToShrink) {
                        const index = headers.indexOf(th);
                        let maxWidth = columnWidths[index] - shrinkAmount;
                        // prevent the columns from shrinking under 92px (~ date field)
                        if (maxWidth < 92) {
                            maxWidth = 92;
                            canKeepShrinking = false;
                        }
                        th.style.maxWidth = `${Math.floor(maxWidth)}px`;
                        columnWidths[index] = maxWidth;
                    }
                    return canKeepShrinking;
                };
                // Sort columns, largest first
                const sortedThs = [...table.querySelectorAll("thead .bg-primary th:not(.o_list_button)")].sort(
                    (a, b) => getWidth(b) - getWidth(a)
                );
                const allowedWidth = table.parentNode.getBoundingClientRect().width;

                let totalWidth = getTotalWidth();
                for (let index = 1; totalWidth > allowedWidth; index++) {
                    // Find the largest columns
                    const largestCols = sortedThs.slice(0, index);
                    const currentWidth = getWidth(largestCols[0]);
                    for (; currentWidth === getWidth(sortedThs[index]); index++) {
                        largestCols.push(sortedThs[index]);
                    }

                    // Compute the number of px to remove from the largest columns
                    const nextLargest = sortedThs[index];
                    const toRemove = Math.ceil((totalWidth - allowedWidth) / largestCols.length);
                    const shrinkAmount = Math.min(toRemove, currentWidth - getWidth(nextLargest));

                    // Shrink the largest columns
                    const canKeepShrinking = shrinkColumns(largestCols, shrinkAmount);
                    if (!canKeepShrinking) {
                        break;
                    }

                    totalWidth = getTotalWidth();
                }

                // We are no longer computing widths, so restore the normal style
                table.classList.remove("o_list_computing_widths");
                return columnWidths;
            }else{
                return this._super();
            }
    },


    onStartResize(ev) {
        this._super(...arguments);
        if (!this.ks_is_lines){
            const table = this.tableRef.el;
            const th = ev.target.closest("th");
            const handler = th.querySelector(".o_resize");
            table.style.width = `${Math.floor(table.getBoundingClientRect().width)}px`;
            const thPosition = [...th.parentNode.children].indexOf(th);
            const resizingColumnElements = [...table.getElementsByTagName("tr")]
                .filter((tr) => tr.children.length === th.parentNode.children.length)
                .map((tr) => tr.children[thPosition]);
            const initialX = ev.clientX;
            const initialWidth = th.getBoundingClientRect().width;
            const initialTableWidth = table.getBoundingClientRect().width;
            const resizeStoppingEvents = ["keydown", "mousedown", "mouseup"];

            const stopResize = (ev) => {
                for (const eventType of resizeStoppingEvents) {
                    window.removeEventListener(eventType, stopResize);
                }

                // we remove the focus to make sure that the there is no focus inside
                // the tr.  If that is the case, there is some css to darken the whole
                // thead, and it looks quite weird with the small css hover effect.
                document.activeElement.blur();
                this.ks_data_width = $(resizingColumnElements[0]).innerWidth();
                var ks_field_data_width = this.ks_list_data.fields_data[resizingColumnElements[0].dataset.name];
                ks_field_data_width.ks_width = this.ks_data_width;
                if (!this.ks_list_data.table_data){
                         this.props.ks_initialize_lvm_data(this.ks_list_data.fields_data);
                }else{
                    this.props.ks_update_field_data([], [ks_field_data_width], true);
                    }

            };
            for (const eventType of resizeStoppingEvents) {
                window.addEventListener(eventType, stopResize);
            }
        }
    },


    ks_textBox: function (node) {
        var self = this;
        if (node.type === "field") {
            if (self.props.list.fields[node.name].store === true &&  node.name != 'sequence' && !(self.props.list.fields[node.name].type === "one2many" || self.props.list.fields[node.name].type === "many2many")) {
                var ks_name = node.name;
                var ks_fields = self.props.list.fields[ks_name];
                var ks_selection_values = []
                var ks_description;
                var ks_field_type;
                var $ks_from;
                var ks_field_identity;
                var ks_identity_flag = false;
                var ks_field_id = ks_name;
                var ks_is_hide = true;
                var ks_widget_flag = true;
                if (ks_fields) {
                    ks_field_type = self.props.list.fields[ks_name].type;

                    if (ks_field_type === "selection") {
                        ks_selection_values = self.props.list.fields[ks_name].selection;
                    }
                    if (ks_description === undefined) {
                        ks_description = node.rawAttrs.string || ks_fields.string;
                    }
                }

                var $th = $('<th>').addClass("ks_advance_search_row ");
                if (ks_field_type === "date" || ks_field_type === "datetime") {
                    if (self.ks_call_flag > 1) {
                        $th.addClass("ks_fix_width");
                    }
                }

                if (ks_field_type === "date" || ks_field_type === "datetime") {
                    if (!(self.ks_call_flag > 1)) {
                        self.ks_call_flag += 1;
                        $ks_from = self.ks_textBox(node);
                        ks_identity_flag = true
                    }
                    if (self.ks_call_flag == 2 && ks_identity_flag == false) {
                        ks_field_id = ks_name + "_lvm_end_date"
                        ks_field_identity = ks_field_id + " lvm_end_date"
                    } else {
                        ks_field_id = ks_name + "_lvm_start_date"
                        ks_field_identity = ks_field_id + " lvm_start_date"
                    }
                }

                var $input = $(qweb.render("ks_list_view_advance_search", {
                    ks_id: ks_field_id,
                    ks_description: ks_description,
                    ks_type: ks_field_type,
                    ks_field_identifier: ks_field_identity,
                    ks_selection: ks_selection_values
                }));

                if ((ks_field_type === "date" || ks_field_type === "datetime") && (self.ks_call_flag == 2 && ks_identity_flag == false)) {
                    if (self.ks_search_domain && self.ks_search_domain.length === 0) {
                        $input.addClass("d-none");
                        $th.addClass("ks_date_inner");
                    }

                    if (!(self.ks_search_domain && self.ks_search_domain.length === 0)) {
                        if (Object.values(self.ks_field_popup) !== undefined) {
                            for (var ks_hide = 0; ks_hide < Object.keys(self.ks_field_popup).length; ks_hide++) {
                                if ((Object.keys(self.ks_field_popup)[ks_hide] === ks_name)) {
                                    ks_is_hide = false
                                    break
                                }
                            }
                            if (self.ksDomain) {
                                if (ks_is_hide === true) {
                                    $input.addClass("d-none");
                                    $th.addClass("d-none");
                                } else {
                                    $th.addClass("ks_date_inner");
                                }
                            } else {
                                $input.addClass("d-none");
                                $th.addClass("d-none");
                            }
                        }
                    }
                }

                if (self.ksDomain != null && self.ksDomain.length) {
                    if (self.ksDomain[self.ksDomain.length - 1] === self.ks_search_domain[self.ks_search_domain.length - 1]) {
                        if (ks_field_type === "date" || ks_field_type === "datetime") {
                            for (var ks_add_span = 0; ks_add_span < Object.keys(self.ks_field_popup).length; ks_add_span++) {
                                if (Object.keys(self.ks_field_popup)[ks_add_span] === ks_name) {
                                    for (var ks_add_span_inner = 0; ks_add_span_inner < Object.values(self.ks_field_popup)[ks_add_span].length - 1; ks_add_span_inner++) {

                                        var $div = $('<div>').addClass("ks_inner_search")
                                        $div.attr('id', ks_name + '_value' + ks_add_span_inner)
                                        var $span = $('<span>');
                                        if (ks_field_type === "datetime") {
                                            $span = $span.addClass("ks_date_chip_ellipsis");
                                        }
                                        $span.attr('id', ks_name + '_ks_span' + ks_add_span_inner)

                                        var $i = $('<i>').addClass("fa fa-times")
                                        $i.addClass('ks_remove_popup');

                                        if (self.ks_call_flag == 2 && ks_identity_flag == false) {
                                            $span.text(Object.values(self.ks_field_popup)[ks_add_span][1])
                                            $span.attr("title", Object.values(self.ks_field_popup)[ks_add_span][1]);
                                            $input.prepend($div);
                                            $input.find("#" + Object.keys(self.ks_field_popup)[ks_add_span] + "_value" + ks_add_span_inner).prepend($i);
                                            $input.find("#" + Object.keys(self.ks_field_popup)[ks_add_span] + "_value" + ks_add_span_inner).prepend($span)
                                        } else {
                                            $input.addClass("ks_date_main");
                                            $span.text(Object.values(self.ks_field_popup)[ks_add_span][0]);
                                            $span.attr("title", Object.values(self.ks_field_popup)[ks_add_span][0]);
                                            $input.prepend($div);
                                            $input.find("#" + Object.keys(self.ks_field_popup)[ks_add_span] + "_value" + ks_add_span_inner).prepend($i);
                                            $input.find("#" + Object.keys(self.ks_field_popup)[ks_add_span] + "_value" + ks_add_span_inner).prepend($span);
                                        }
                                    }
                                }
                            }
                        } else if (ks_field_type === "selection") {
                            for (var ks_add_span = 0; ks_add_span < Object.keys(self.ks_field_popup).length; ks_add_span++) {
                                if (Object.keys(self.ks_field_popup)[ks_add_span] === ks_name) {
                                    for (var ks_add_span_inner = 0; ks_add_span_inner < Object.values(self.ks_field_popup)[ks_add_span].length; ks_add_span_inner++) {
                                        var value;
                                        var $div = $('<div>').addClass("ks_inner_search")
                                        $div.attr('id', ks_name + '_value' + ks_add_span_inner)

                                        var $span = $('<span>').addClass("ks_advance_chip");
                                        $span.attr('id', ks_name + '_ks_span' + ks_add_span_inner)
                                        $span.addClass("ks_advance_chip_ellipsis");

                                        var $i = $('<i>').addClass("fa fa-times")
                                        $i.addClass('ks_remove_popup');

                                        for (var sel = 0; sel < ks_selection_values.length; sel++) {
                                            if (ks_selection_values[sel][0] === Object.values(self.ks_field_popup)[ks_add_span][ks_add_span_inner]) {
                                                value = ks_selection_values[sel][1];
                                            }
                                        }

                                        $span.text(value)
                                        $span.attr("title", value);
                                        $input.prepend($div);
                                        $input.find("#" + Object.keys(self.ks_field_popup)[ks_add_span] + "_value" + ks_add_span_inner).prepend($i);
                                        $input.find("#" + Object.keys(self.ks_field_popup)[ks_add_span] + "_value" + ks_add_span_inner).prepend($span)
                                    }
                                }
                            }
                        } else {
                            for (var ks_add_span = 0; ks_add_span < Object.keys(self.ks_field_popup).length; ks_add_span++) {
                                if (Object.keys(self.ks_field_popup)[ks_add_span] === ks_name) {
                                    for (var ks_add_span_inner = 0; ks_add_span_inner < Object.values(self.ks_field_popup)[ks_add_span].length; ks_add_span_inner++) {

                                        var $div = $('<div>').addClass("ks_inner_search")
                                        $div.attr('id', ks_name + '_value' + ks_add_span_inner)

                                        var $span = $('<span>').addClass("ks_advance_chip");

                                        if (!(ks_field_type === "date" || ks_field_type === "datetime")) {
                                            $span.addClass("ks_advance_chip_ellipsis");
                                        }


                                        $span.attr('id', ks_name + '_ks_span' + ks_add_span_inner)
                                        var $i = $('<i>').addClass("fa fa-times")

                                        $i.addClass('ks_remove_popup');
                                        if (ks_field_type === 'monetary' || ks_field_type === 'integer' || ks_field_type === 'float') {
                                            var currency = session.get_currency(self.props.list_data.currency);
                                            var formatted_value = fieldUtils.format.float(Object.values(self.ks_field_popup)[ks_add_span][ks_add_span_inner] || 0, {
                                                digits: currency && currency.digits
                                            });
                                            $span.text(formatted_value);
                                            $span.attr('title', formatted_value);

                                        } else {
                                            $span.text(Object.values(self.ks_field_popup)[ks_add_span][ks_add_span_inner])
                                            $span.attr('title', Object.values(self.ks_field_popup)[ks_add_span][ks_add_span_inner]);
                                        }
                                        if (!(ks_field_type === 'many2one' || ks_field_type === 'many2many' || ks_field_type === 'one2many'))
                                            $input.find('input').removeAttr('placeholder');
                                        $input.prepend($div);
                                        $input.find("#" + Object.keys(self.ks_field_popup)[ks_add_span] + "_value" + ks_add_span_inner).prepend($i);
                                        $input.find("#" + Object.keys(self.ks_field_popup)[ks_add_span] + "_value" + ks_add_span_inner).prepend($span)
                                    }
                                }
                            }
                        }
                    }
                }

                if (self.ksDomain != null && self.ksDomain.length) {
                    if (!(self.ksDomain[self.ksDomain.length - 1] === self.ks_search_domain[self.ks_search_domain.length - 1])) {
                        delete self.ks_field_domain_dict
                        delete self.ksDomain
                        self.ksBaseDomain = []
                        self.ks_field_domain_dict = {}
                        self.ks_key_fields.splice(0, self.ks_key_fields.length)
                        self.ks_field_domain_list.splice(0, self.ks_field_domain_list.length)
                    }
                }


                if ((ks_field_type === "date" || ks_field_type === "datetime") && (self.ks_search_domain)) {
                    for (var i = 0; i < self.ks_search_domain.length; i++) {
                        if (ks_field_identity.split("_lvm_end_date")[0] === self.ks_search_domain[i][0] || ks_field_identity.split("_lvm_start_date")[0] === self.ks_search_domain[i][0]) {
                            ks_widget_flag = false
                            break;
                        }
                    }
                }

                if (ks_widget_flag && ks_field_type === "date") {
                    var widget_key = "ksStartdatePickerWidget" + ks_field_identity;
                    self[widget_key] = new (datepicker.DateWidget)(this);
                    self[widget_key].appendTo($input.find('.custom-control-searchbar-change')).then((function () {
                        self["ksStartdatePickerWidget" + ks_field_identity].$el.addClass("ks_btn_middle_child o_input");
                        self["ksStartdatePickerWidget" + ks_field_identity].$el.find("input").attr("placeholder", "Search");
                    }).bind(this));

                    self[widget_key].on("datetime_changed", widget_key, function () {
                        self.ks_on_date_filter_change(widget_key);
                    });
                }


                if (ks_widget_flag && ks_field_type === "datetime") {
                    var widget_key = "ksStartdatetimePickerWidget" + ks_field_identity;
                    self[widget_key] = new (datepicker.DateTimeWidget)(this);
                    self[widget_key].appendTo($input.find(".custom-control-searchbar-change")).then((function () {

                        //
                        self["ksStartdatetimePickerWidget" + ks_field_identity].$el.addClass("ks_btn_middle_child o_input");
                        self["ksStartdatetimePickerWidget" + ks_field_identity].$el.find("input").attr("placeholder", "Search");
                    }).bind(this));

                    self[widget_key].on("datetime_changed", widget_key, function () {
                        self.ks_on_date_filter_change(widget_key);
                    });
                }



                if (self.ksDomain != null && this.ksDomain.length) {
                    if (self.ksDomain.length === self.ks_search_domain.length) {
                        for (var i = 0; i < self.ks_search_domain.length; i++) {
                            if (!(self.ks_search_domain[i] === self.ksDomain[i])) {
                                self.ksbaseFlag = true
                            }
                        }
                    }

                    if (self.ksbaseFlag === true) {
                        self.ksBaseDomain = self.ks_search_domain
                        self.ksbaseFlag = false
                    }
                }

                if ((self.ksDomain === null || self.ksDomain === undefined || self.ksDomain.length === 0) && self.ks_search_domain && self.ks_search_domain.length) {
                    self.ksBaseDomain = self.ks_search_domain
                }
                if ((self.ksDomain === null || self.ksDomain === undefined || self.ksDomain.length === 0) && self.ks_search_domain && self.ks_search_domain.length === 0) {
                    self.ksBaseDomain = self.ks_search_domain
                }

                $th.append($input);
                if (self.ks_call_flag == 2) {
                    $th.append($ks_from);
                    self.ks_datepicker_flag += 1;
                }
                if (self.ks_datepicker_flag == 2) {
                    self.ks_call_flag = 1;
                    self.ks_datepicker_flag = 0;
                }
            } else {
                var $th = $('<th>').addClass("ks_advance_search_row ");
            }
            return $th;
        } else {
            return $('<th>').addClass("ks_advance_search_row ");;
        }
    },
    ks_on_date_filter_change(ks_widget_key) {
        var self = this;
        var ks_date_widget = this[ks_widget_key];
        var target = ks_date_widget.el;
        if (ks_date_widget.getValue()) {
            let rec_ids = [];
            for (let i = 0; i < this.props.list.records.length; i++) {
                rec_ids.push(this.props.list.records[i].resId);
            }
            var ks_options = {
                ksFieldName: target.parentElement.dataset.ksField,
                KsSearchId: target.parentElement.dataset.name,
                ksfieldtype: target.parentElement.dataset.fieldType,
                ksFieldIdentity: target.parentElement.dataset.fieldIdentity,
                res_ids: rec_ids,
                ks_val: ks_date_widget.getValue().toISOString()
            }
            this.Ks_update_advance_search_controller(ks_options);

            if (!(target.parentElement.dataset.name.indexOf("_lvm_end_date") > 0)) {
                $(".custom-control-searchbar-change[data-name=" + target.parentElement.dataset.name + "]").parent().addClass("ks_date_main");
                $($(".custom-control-searchbar-change[data-name=" + target.parentElement.dataset.name + "]").parent().parent().children()[1]).addClass("ks_date_inner");
                $($($(".custom-control-searchbar-change[data-name=" + target.parentElement.dataset.name + "]").parent().parent().children()[1])[0]).prop("style", "");
                $($(".custom-control-searchbar-change[data-name=" + target.parentElement.dataset.name + "]").parent().parent().children()[1]).removeClass("d-none");
                $($($(".custom-control-searchbar-change[data-name=" + target.parentElement.dataset.name + "]").parent().parent().children()[1]).children()[0]).removeClass("d-none");
            }
        };
    },
    async ks_fetch_autocomplete_data(field, type, value, ks_one2many_relation) {
        var self = this;

        const data1 = await this.rpc("/web/dataset/call", {
            model: 'user.mode',
            method: 'ks_get_autocomplete_values',
            args: [self.props.list.resModel, field, type, value, ks_one2many_relation],
        })
        return data1
    },

    async ks_advance_searchbar(e) {
        if ($(e.target).hasClass("custom-control-searchbar-advance")) {
            // block of code for Autocomplete
            var self = this;
            var ks_field_type = e.target.dataset.fieldType;
            var ks_field_name = e.target.dataset.ks_field_id;
            var ks_one2many_relation;
            var ks_input_val = $(e.target).val();

            if ((!(e.keyCode == 13)) && $(e.target).val().length) {

                if (ks_field_type === "one2many") {
                    ks_one2many_relation = self.props.list.fields[e.target.dataset.name].relation
                }


                self.ks_fetch_autocomplete_data(e.target.dataset.name, ks_field_type, $(e.target).val(), ks_one2many_relation)
                    .then(function (ks_auto_Data) {

                        self.ks_autocomplete_data_result = ks_auto_Data

                        if (!(ks_field_type === "date" || ks_field_type === "datetime" || ks_field_type === "selection")) {
                            var ks_unique_data = {}
                            self.ks_autocomplete_data[e.target.dataset.name] = [];

                            if (ks_field_type === 'one2many') {
                                for (var i = 0; i < self.ks_autocomplete_data_result.length; i++) {

                                    if (!(ks_unique_data[self.ks_autocomplete_data_result[i]])) {
                                        self.ks_autocomplete_data[e.target.dataset.name].push(String(self.ks_autocomplete_data_result[i]));
                                        ks_unique_data[self.ks_autocomplete_data_result[i]] = true;
                                    }
                                }
                            } else if (ks_field_type === 'many2many' || ks_field_type === 'many2one') {
                                for (var i = 0; i < self.ks_autocomplete_data_result.length; i++) {

                                    if (!(ks_unique_data[self.ks_autocomplete_data_result[i][e.target.dataset.name][1]])) {
                                        self.ks_autocomplete_data[e.target.dataset.name].push(String(self.ks_autocomplete_data_result[i][e.target.dataset.name][1]));
                                        ks_unique_data[self.ks_autocomplete_data_result[i][e.target.dataset.name][1]] = true;
                                    }
                                }
                            } else {
                                for (var i = 0; i < self.ks_autocomplete_data_result.length; i++) {

                                    if (!(ks_unique_data[self.ks_autocomplete_data_result[i][e.target.dataset.name]])) {
                                        self.ks_autocomplete_data[e.target.dataset.name].push(String(self.ks_autocomplete_data_result[i][e.target.dataset.name]));
                                        ks_unique_data[self.ks_autocomplete_data_result[i][e.target.dataset.name]] = true;
                                    }
                                }
                            }


                            $(".custom-control-searchbar-advance[data-name=" + e.target.dataset.name + "]").autocomplete({
                                source: self.ks_autocomplete_data[e.target.dataset.name],
                                response: function (event, ui) {
                                    if (!ui.content.length) {
                                        var noResult = { value: "", label: "No results found" };
                                        ui.content.push(noResult);
                                        //$("#message").text("No results found");
                                    }
                                }

                            });
                        }
                    });
            }
            if (e.keyCode == 8 && this.ks_allow_search) {
                if (event.target.parentNode.children.length !== 1) {
                    this.ks_remove_popup_domain_event(e);

                    this.ks_allow_search = false;
                }
            }
            if (e.keyCode == 13 && this.ks_allow_search) {
                let rec_ids = [];
                for (let i = 0; i < this.props.list.records.length; i++) {
                    rec_ids.push(this.props.list.records[i].resId);
                }
                var ks_options = {
                    ksFieldName: e.target.dataset.ksField,
                    KsSearchId: e.target.dataset.name,
                    ksfieldtype: e.target.dataset.fieldType,
                    res_ids: rec_ids
                };
                this.Ks_update_advance_search_controller(ks_options)
                this.ks_allow_search = false;
            }
        }
    },

    Ks_update_advance_search_controller(ks_options) {
        if (this.ks_lvm_mode) {
            var self = this;
            if (self.ks_remove_popup_flag === true) {
                var ks_advance_search_params = {};
                ks_advance_search_params["modelName"] = self.props.resModel;
                ks_advance_search_params["context"] = self.props.context;
                ks_advance_search_params["ids"] = ks_options.res_ids;
                ks_advance_search_params["offset"] = self.props.list.model.root.offset;
                //                    ks_advance_search_params["currentId"] = self.renderer.state.res_id;
                ks_advance_search_params["selectRecords"] = self.props.list.model.root.selection;
                ks_advance_search_params["groupBy"] = self.props.list.model.root.groupBy;
                self.ks_field_domain_list = [];

                for (var j = 0; j < self.ks_key_fields.length; j++) {
                    self.ks_field_domain_list = self.ks_field_domain_list.concat(self.ks_field_domain_dict[self.ks_key_fields[j]]);
                }
                self.ks_remove_popup_flag = false;
                ks_advance_search_params["ksDomain"] = self.ks_field_domain_list;
                if (self.ks_search_domain.length === 0) {
                    self.ksBaseDomain = []
                }
                if (self.ksBaseDomain === null && (self.ksDomain === null || self.ksDomain.length === 0) && self.ks_search_domain.length) {
                    self.ksBaseDomain = self.ks_search_domain
                }
                if (self.ksBaseDomain.length !== 0 || self.ks_field_domain_list.length !== 0) {
                    ks_advance_search_params["domain"] = self.ksBaseDomain.concat(self.ks_field_domain_list)
                } else {
                    ks_advance_search_params["domain"] = []
                }
                self.ksDomain = ks_advance_search_params["ksDomain"]
                self.mydomain = ks_advance_search_params["ksDomain"]
                self.ks_update(self.mydomain);

            } else {
                var ks_val_flag = false;
                if (ks_options.ks_val) {
                    ks_val_flag = ks_options.ks_val.trim() !== 0
                } else {
                    if (ks_options.ksfieldtype == "selection") {
                        ks_val_flag = $(".custom-control-searchbar-change[data-name=" + ks_options.KsSearchId + "]").val().trim() !== 0
                    } else {
                        ks_val_flag = $(".custom-control-searchbar-advance[data-name=" + ks_options.KsSearchId + "]").val() !== 0
                    }
                }

                if (Number(ks_val_flag)) {
                    self.ks_advance_search_refresh = true;
                    if (ks_options.ksfieldtype == "selection") {
                        var ks_search_value = ks_options.ks_val || $(".custom-control-searchbar-change[data-name=" + ks_options.KsSearchId + "]").val();
                    } else {
                        var ks_search_value = ks_options.ks_val || $(".custom-control-searchbar-advance[data-name=" + ks_options.KsSearchId + "]").val();
                    }
                    //                        var ks_search_value = ks_options.data.ks_val || $(".custom-control-searchbar-advance[data-name=" + ks_options.data.KsSearchId + "]").val();
                    var ks_advance_search_type = ks_options.ksfieldtype;
                    var ks_selection_values = [];
                    var ks_advance_search_params = {};
                    self.ks_field_domain_list = [];
                    self.ks_key_insert_flag = false;
                    var ks_data_insert_flag = false;
                    var ks_value = ks_options.KsSearchId.split("_lvm_start_date")
                    ks_advance_search_params["groupBy"] = self.props.list.model.root.groupBy
                    ks_advance_search_params["modelName"] = self.props.resModel;
                    ks_advance_search_params["context"] = self.props.context;
                    ks_advance_search_params["ids"] = ks_options.res_ids;
                    ks_advance_search_params["offset"] = self.props.list.model.root.offset;
                    //                        ks_advance_search_params["currentId"] = self.renderer.state.res_id;
                    ks_advance_search_params["selectRecords"] = self.props.list.model.root.selection

                    if (ks_value.length === 1) {
                        ks_value = ks_options.KsSearchId.split("_lvm_end_date")
                        if (ks_value.length === 2)
                            ks_options.KsSearchId = ks_value[0];
                    } else {
                        ks_options.KsSearchId = ks_value[0];
                    }

                    for (var ks_sel_check = 0; ks_sel_check < self.ks_key_fields.length; ks_sel_check++) {
                        if (ks_options.KsSearchId === self.ks_key_fields[ks_sel_check]) {
                            ks_data_insert_flag = true;
                        }
                    }

                    if ((ks_data_insert_flag === false) || (ks_data_insert_flag === true && (ks_advance_search_type === "many2one" || ks_advance_search_type === "many2many" || ks_advance_search_type === "char"))) {
                        if (!(ks_advance_search_type === "datetime" || ks_advance_search_type === "date")) {
                            if (this.ks_key_fields.length === 0) {
                                if (ks_advance_search_type === 'monetary' || ks_advance_search_type === 'integer' || ks_advance_search_type === 'float') {
                                    try {
                                        //Fixme currency
                                        var currency = session.get_currency(self.props.list_data.currency);
                                        var formatted_value = fieldUtils.parse.float(ks_search_value || 0, {
                                            digits: currency && currency.digits
                                        });
                                        ks_search_value = formatted_value
                                        self.ks_key_fields.push(ks_options.KsSearchId);
                                    } catch {
                                        this.notification.add(this.env._t("Please enter a valid number"), {
                                            title: this.env._t("Notification"),
                                            sticky: false,
                                            type: "info",
                                        });
                                    }
                                } else {
                                    self.ks_key_fields.push(ks_options.KsSearchId);
                                }
                            } else {
                                for (var key_length = 0; key_length < self.ks_key_fields.length; key_length++) {
                                    if ((self.ks_key_fields[key_length] === ks_options.KsSearchId)) {
                                        self.ks_key_insert_flag = true;
                                        break;
                                    }
                                }
                                if (!(self.ks_key_insert_flag)) {
                                    if (ks_advance_search_type === 'monetary' || ks_advance_search_type === 'integer' || ks_advance_search_type === 'float') {
                                        try {
                                            // Fixme currency
                                             var currency = session.get_currency(self.props.list_data.currency);
                                            var formatted_value = fieldUtils.parse.float(ks_search_value || 0, {
                                                digits: currency && currency.digits
                                            });
                                            ks_search_value = formatted_value
                                            self.ks_key_fields.push(ks_options.KsSearchId);
                                        } catch {
                                            this.notification.add(this.env._t("Please enter a valid number"), {
                                                title: this.env._t("Notification"),
                                                sticky: false,
                                                type: "info",
                                            });
                                        }
                                    } else {
                                        self.ks_key_fields.push(ks_options.KsSearchId);
                                    }
                                }
                            }
                        }

                        if (ks_advance_search_type === "datetime" || ks_advance_search_type === "date") {
                            if (ks_options.ksFieldIdentity === ks_options.KsSearchId + '_lvm_start_date lvm_start_date') {
                                self.ks_start_date = ks_search_value;
                                self.ks_start_date_id = ks_options.KsSearchId;
                            } else {
                                self.ks_end_date = ks_search_value;
                                self.ks_end_date_id = ks_options.KsSearchId
                            }

                            if (ks_advance_search_type === "datetime" || ks_advance_search_type === "date") {
                                if (ks_options.ksFieldIdentity === ks_options.KsSearchId + '_lvm_end_date lvm_end_date') {
                                    if (self.ks_start_date_id === self.ks_end_date_id) {
                                        self.ks_field_domain_dict[self.ks_start_date_id] = [
                                            [self.ks_start_date_id, '>=', self.ks_start_date],
                                            [self.ks_end_date_id, '<=', self.ks_end_date]
                                        ]
                                        if (self.ks_key_fields.length === 0) {
                                            self.ks_key_fields.push(self.ks_start_date_id);
                                        } else {
                                            for (var key_length = 0; key_length < self.ks_key_fields.length; key_length++) {
                                                if (!(self.ks_key_fields[key_length] === ks_options.KsSearchId)) {
                                                    self.ks_key_fields.push(self.ks_start_date_id);
                                                    break;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        } else if (ks_advance_search_type === 'selection') {
                            if (ks_search_value === "Select a Selection") {
                                for (var j = 0; j < self.ks_key_fields.length; j++) {
                                    self.ks_field_domain_list = self.ks_field_domain_list.concat(self.ks_field_domain_dict[self.ks_key_fields[j]]);
                                }
                                ks_advance_search_params["ksDomain"] = self.ks_field_domain_list;
                                if (self.ks_search_domain.length === 0) {
                                    self.ksBaseDomain = []
                                }
                                ks_advance_search_params["domain"] = self.ksBaseDomain.concat(self.ks_field_domain_list)
                                self.ksDomain = ks_advance_search_params["ksDomain"]
                                self.mydomain = ks_advance_search_params["ksDomain"]
                                self.ks_update(self.mydomain);
                                //                                    self.update(ks_advance_search_params, undefined);
                            } else {

                                // obtaining values of selection
                                ks_selection_values = self.props.list.fields[ks_options.KsSearchId].selection;

                                //setting values for selection
                                for (var i = 0; i < ks_selection_values.length; i++) {
                                    if (ks_selection_values[i][1] === ks_search_value) {
                                        ks_search_value = ks_selection_values[i][0];
                                    }
                                }
                                self.ks_field_domain_dict[ks_options.KsSearchId] = [
                                    [ks_options.KsSearchId, '=', ks_search_value]
                                ]
                            }
                        } else if (ks_advance_search_type === "many2one" || ks_advance_search_type === "many2many") {
                            if (self.ks_field_domain_dict[ks_options.KsSearchId] === undefined)
                                self.ks_field_domain_dict[ks_options.KsSearchId] = [
                                    [ks_options.KsSearchId, "ilike", ks_search_value]
                                ]
                            else
                                self.ks_field_domain_dict[ks_options.KsSearchId].push([ks_options.KsSearchId, "ilike", ks_search_value])

                            if (self.ks_field_domain_dict[ks_options.KsSearchId].length > 1) {
                                self.ks_field_domain_dict[ks_options.KsSearchId].unshift("|")
                            }
                            //                                ks_advance_search_params["ids"] = self.initialState.res_id;
                        } else if (ks_advance_search_type === 'monetary' || ks_advance_search_type === 'integer' || ks_advance_search_type === 'float') {
                            self.ks_field_domain_dict[ks_options.KsSearchId] = [
                                [ks_options.KsSearchId, '=', ks_search_value]
                            ]

                        }
                        else if (ks_advance_search_type === 'char') {
                            if (self.ks_field_domain_dict[ks_options.KsSearchId] === undefined) {
                                self.ks_field_domain_dict[ks_options.KsSearchId] = [
                                    [ks_options.KsSearchId, 'ilike', ks_search_value]
                                ]
                            }
                            else { self.ks_field_domain_dict[ks_options.KsSearchId].push([ks_options.KsSearchId, 'ilike', ks_search_value]) }
                            if (self.ks_field_domain_dict[ks_options.KsSearchId].length > 1) {
                                self.ks_field_domain_dict[ks_options.KsSearchId].unshift("|")
                            }
                        }

                        else {
                            self.ks_field_domain_dict[ks_options.KsSearchId] = [
                                [ks_options.KsSearchId, "ilike", ks_search_value]
                            ]
                        }

                        if (ks_advance_search_type === "datetime" || ks_advance_search_type === "date") {
                            if (ks_options.ksFieldIdentity === ks_options.KsSearchId + '_lvm_end_date lvm_end_date') {
                                for (var j = 0; j < self.ks_key_fields.length; j++) {
                                    this.ks_field_domain_list = self.ks_field_domain_list.concat(self.ks_field_domain_dict[self.ks_key_fields[j]]);
                                }
                                ks_advance_search_params["ksDomain"] = self.ks_field_domain_list;
                                if (self.ks_search_domain.length === 0) {
                                    self.ksBaseDomain = []
                                }
                                ks_advance_search_params["domain"] = self.ksBaseDomain.concat(self.ks_field_domain_list)
                                self.ksDomain = ks_advance_search_params["ksDomain"]
                                self.mydomain = ks_advance_search_params["ksDomain"]
                                self.ks_update(self.mydomain);
                                // Fixme update
                                //                                    self.update(ks_advance_search_params, undefined);
                                self.ks_start_date = undefined;
                                self.ks_end_date = undefined;
                                self.ks_start_date_id = undefined;
                                self.ks_end_date_id = undefined;
                            }
                        } else {
                            if (ks_advance_search_type === 'monetary' || ks_advance_search_type === 'integer' || ks_advance_search_type === 'float') {
                                if (!(isNaN(ks_search_value))) {
                                    for (var j = 0; j < self.ks_key_fields.length; j++) {
                                        self.ks_field_domain_list = self.ks_field_domain_list.concat(self.ks_field_domain_dict[self.ks_key_fields[j]]);
                                    }
                                    ks_advance_search_params["ksDomain"] = self.ks_field_domain_list;
                                    if (self.ks_search_domain.length === 0) {
                                        self.ksBaseDomain = []
                                    }
                                    ks_advance_search_params["domain"] = self.ksBaseDomain.concat(self.ks_field_domain_list)
                                    self.ksDomain = ks_advance_search_params["ksDomain"]
                                    self.mydomain = ks_advance_search_params["ksDomain"]
                                    self.ks_update(self.mydomain);
                                    // FIXME update
                                    //                                        self.update(ks_advance_search_params, undefined);
                                } else {
                                    if (self.ks_search_domain.length === 0) {
                                        self.ksBaseDomain = []
                                    }
                                    ks_advance_search_params["domain"] = self.ksDomain || []
                                    self.mydomain = ks_advance_search_params["domain"]
                                    self.ks_update(self.mydomain);
                                    // Fixme update
                                    //                                        self.update(ks_advance_search_params, undefined);
                                }
                            } else {
                                for (var j = 0; j < self.ks_key_fields.length; j++) {
                                    self.ks_field_domain_list = self.ks_field_domain_list.concat(self.ks_field_domain_dict[self.ks_key_fields[j]]);
                                }
                                ks_advance_search_params["ksDomain"] = self.ks_field_domain_list;
                                if (self.ks_search_domain.length === 0) {
                                    self.ksBaseDomain = []
                                }
                                ks_advance_search_params["domain"] = self.ksBaseDomain.concat(self.ks_field_domain_list)
                                self.ksDomain = ks_advance_search_params["ksDomain"];
                                self.mydomain = ks_advance_search_params["ksDomain"]
                                self.ks_update(self.mydomain);
                                // Fixme update
                                //                                    self.update(ks_advance_search_params, undefined);
                            }
                        }
                    } else {
                        for (var j = 0; j < self.ks_key_fields.length; j++) {
                            self.ks_field_domain_list = self.ks_field_domain_list.concat(self.ks_field_domain_dict[self.ks_key_fields[j]]);
                        }
                        ks_advance_search_params["ksDomain"] = self.ks_field_domain_list;
                        if (self.ks_search_domain.length === 0) {
                            self.ksBaseDomain = []
                        }
                        ks_advance_search_params["domain"] = self.ksBaseDomain.concat(self.ks_field_domain_list)
                        self.ksDomain = ks_advance_search_params["ksDomain"]
                        self.mydomain = ks_advance_search_params["ksDomain"]
                        self.ks_update(self.mydomain);
                        // Fixme update
                        //                            self.update(ks_advance_search_params, undefined);
                    }
                } else {
                    self.ks_advance_search_refresh = true;
                    //                        var ks_search_value = $('#' + ks_options.data.KsSearchId).val().trim();
                    if (ks_options.ksfieldtype == "selection") {
                        var ks_search_value = $(".custom-control-searchbar-change[data-name=" + ks_options.KsSearchId + "]").val().trim();
                    } else {
                        var ks_search_value = $(".custom-control-searchbar-advance[data-name=" + ks_options.KsSearchId + "]").val();
                    }
                    //                        var ks_search_value = $(".custom-control-searchbar-advance[data-name=" + ks_options.data.KsSearchId + "]").val().trim();
                    var ks_advance_search_type = ks_options.ksfieldtype;
                    var ks_selection_values = [];
                    var ks_advance_search_params = {};
                    self.ks_field_domain_list = [];
                    self.ks_key_insert_flag = false;
                    var ks_data_insert_flag = false;
                    var ks_value = ks_options.KsSearchId.split("_lvm_start_date")

                    ks_advance_search_params["modelName"] = self.props.list.resModel;
                    ks_advance_search_params["context"] = self.props.context;
                    ks_advance_search_params["ids"] = ks_options.res_ids;
                    ks_advance_search_params["offset"] = self.props.list.model.root.offset;
//                    ks_advance_search_params["currentId"] = self.renderer.state.res_id;
                    ks_advance_search_params["selectRecords"] = self.props.list.model.root.selection;
                    ks_advance_search_params["groupBy"] = [];

                    for (var j = 0; j < self.ks_key_fields.length; j++) {
                        self.ks_field_domain_list = self.ks_field_domain_list.concat(self.ks_field_domain_dict[self.ks_key_fields[j]]);
                    }
                    ks_advance_search_params["ksDomain"] = self.ks_field_domain_list;
                    if (self.ks_search_domain.length === 0) {
                        self.ksBaseDomain = []
                    }
                    ks_advance_search_params["domain"] = self.ksBaseDomain.concat(self.ks_field_domain_list)
                    self.ksDomain = ks_advance_search_params["ksDomain"]
                    self.mydomain = ks_advance_search_params["ksDomain"]
                    self.ks_update(self.mydomain);

                }
            }
        }
    },

    async ks_update(data) {
//    this.props.ks_renderer_update(data);
        const list = this.props.list.model.root;
        list.domain = [];
        this.ks_search_domain  = [];
        var browser_search_domain =[];
        this.env.searchModel.globalDomain = [];
        for (let item of this.default_domain){
            if (item != undefined){
                list.domain.push(item);
                this.ks_search_domain.push(item);
            }
        }
        for (let items of this.search_default){
            if (items != undefined){
                this.env.searchModel.globalDomain.push(items);
            }
        }
        for(let ks_domain of data){
            if (ks_domain != undefined){
                list.domain.push(ks_domain);
                this.env.searchModel.globalDomain.push(ks_domain);
                this.ks_search_domain.push(ks_domain)
                browser_search_domain.push(ks_domain)
            }
        }
        browser.localStorage.setItem("ks_actionid",this.env.config.actionId);
        browser.localStorage.setItem("search_domain",JSON.stringify(browser_search_domain));
        browser.localStorage.setItem("ks_model",list.resModel);
        browser.localStorage.setItem("field_dict",JSON.stringify(this.ks_field_domain_dict));
        browser.localStorage.setItem("key_field",JSON.stringify(this.ks_key_fields));
        await this.env.searchModel._notify();


        },

    ks_remove_popup_domain_event(e) {
        if ($(e.target).hasClass("ks_remove_popup")) {

            var div = e.target.closest('.ks_inner_search')
            var ks_remove_options = {
                ksDiv: div,
                ksfieldtype: e.target.parentElement.parentElement.children[1].dataset.fieldType
            };
            this.ks_remove_popup_domain(ks_remove_options);
        }
    },

    ks_remove_popup_domain(ks_options) {
        if (this.ks_lvm_mode) {
            var self = this;
            var ks_i;
            var key;
            var key_array;

            if (ks_options.ksDiv !== undefined) {
                key_array = ks_options.ksDiv.id.split("_value")
                key = key_array[0];
            } else {
                key = event.target.id;
            }

            if (self.ks_field_domain_dict[key] !== undefined) {
                if (self.ks_field_domain_dict[key].length === 1 || ks_options.ksfieldtype === "date" || ks_options.ksfieldtype === "datetime") {
                    delete self.ks_field_domain_dict[key]
                    for (ks_i = 0; ks_i < self.ks_key_fields.length; ks_i++) {
                        if (key === self.ks_key_fields[ks_i]) {
                            break;
                        }
                    }

                    if (ks_options.ksDiv !== undefined) {
                        $("#" + ks_options.ksDiv.id).remove()
                    } else {
                        // fixme
                        //                            $("#" + $(ks_options.event.target).parent().children()[$(ks_options.data.event.target).parent().children().length - 2].id).remove();
                    }

                    self.ks_key_fields.splice(ks_i, 1);
                    self.ks_remove_popup_flag = true;
                    self.Ks_update_advance_search_controller(false);
                } else {
                    for (var j = 0; j < self.ks_field_domain_dict[key].length; j++) {
                        if (self.ks_field_domain_dict[key][j] !== '|') {
                            if (ks_options.ksDiv !== undefined) {
                                if (self.ks_field_domain_dict[key][j][2] === ks_options.ksDiv.innerText) {
                                    self.ks_field_domain_dict[key].splice(j, 1)
                                    self.ks_field_domain_dict[key].splice(0, 1);
                                    break;
                                }
                            } else {
                                self.ks_field_domain_dict[key].splice(j, 1)
                                self.ks_field_domain_dict[key].splice(0, 1);
                                break;
                            }
                        }
                    }
                    if (ks_options.ksDiv !== undefined) {
                        $("#" + ks_options.ksDiv.id).remove()
                    } else {
                        //fixme
                        //                            $("#" + $(ks_options.data.event.target).parent().children()[$(ks_options.data.event.target).parent().children().length - 2].id).remove();
                    }
                    self.ks_remove_popup_flag = true;
                    self.Ks_update_advance_search_controller(false);
                }
            } else {
                self.ks_remove_popup_flag = true;
                self.Ks_update_advance_search_controller(false);
            }
        }
    },

    ks_change_event(e) {
        if ($(e.target).hasClass("custom-control-searchbar-change")) {
            if (e.target.dataset.fieldType !== "datetime" && e.target.dataset.fieldType !== 'date') {
                let rec_ids = [];
                for (let i = 0; i < this.props.list.records.length; i++) {
                    rec_ids.push(this.props.list.records[i].resId);
                }
                var ks_options = {
                    ksFieldName: e.target.dataset.ksField,
                    KsSearchId: e.target.dataset.name,
                    ksfieldtype: e.target.dataset.fieldType,
                    ksFieldIdentity: e.target.dataset.fieldIdentity,
                    res_ids: rec_ids
                }
                this.Ks_update_advance_search_controller(ks_options)

            }
        }
    },


    async onCellClicked(record, column, ev) {
    if (this.ks_is_lines){
        this._super(...arguments);
    }
    if (this.props.activeActions.type == 'view'){
        if (window.getSelection().toString() && this.props.activeActions.type == 'view') {
            return;
        }
        if (this.ks_list_data){
            if (this.ks_lvm_mode && this.ks_list_data.table_data.ks_editable && this.props.activeActions.type == 'view') {
                if (ev.target.special_click) {
                    return;
                }
                const recordAfterResequence = async () => {
                    const recordIndex = this.props.list.records.indexOf(record);
                    await this.resequencePromise;
                    // row might have changed record after resequence
                    record = this.props.list.records[recordIndex] || record;
                };
                if (record.isInEdition && this.props.list.editedRecord === record) {
                    this.focusCell(column);
                    this.cellToFocus = null;
                } else {
                    await recordAfterResequence();
                    await record.switchMode("edit");
                    this.cellToFocus = { column, record };
                }

            } else {
                this._super(...arguments);
            }
            }else{
                this._super(...arguments);
            }
        }
},

    _onKsFieldActiveClickrender(event) {
        if ($(event.target).hasClass("ks_hide_show_checkbox")) {
            if (this.ks_lvm_mode) {
                event.stopPropagation();
                var self = this;
                self.ks_list_data = self.list_data ? self.list_data : session.list_data
                self.ks_resize = false;
                if (session.ks_toggle_color) {
                    $("input:checked + .ks_slider").css("background-color", session.ks_toggle_color);
                    $("input:not(:checked) + .ks_slider").css("background-color", "");
                }
                var ks_field_data = self.ks_list_data.fields_data[event.target.dataset.field_name];
                ks_field_data.ksShowField = event.target.checked;
//                self.toggleOptionalField(event.target.dataset.field_name);
                if (!self.ks_list_data.table_data){
                    return self.props.ks_initialize_lvm_data(this.ks_list_data.fields_data);
                }
                self.props.ks_update_field_data([], [ks_field_data], true);

            }
        }
    },

});
ListRenderer.props = [
    "activeActions?",
    "list",
    "archInfo",
    "openRecord",
    "onAdd?",
    "cycleOnTab?",
    "allowSelectors?",
    "editable?",
    "noContentHelp?",
    "nestedKeyOptionalFieldsData?",
    "readonly?",
    "onOptionalFieldsChanged?",
    "ks_update_field_data?",
    "ks_initialize_lvm_data?",
    "list_data?",
    "ks_renderer_update?"
];
