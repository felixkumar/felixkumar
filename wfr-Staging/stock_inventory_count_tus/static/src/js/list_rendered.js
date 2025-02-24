/** @odoo-module */

import { makeContext } from "@web/core/context";
import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";
import { getTabableElements } from "@web/core/utils/ui";



const { useEffect } = owl;
patch(ListRenderer.prototype, 'web.ListRenderer', {
    focusCell(column, forward = true) {
        const index = this.state.columns.indexOf(column);
        let columns;
        if (index === -1 && !forward) {
            columns = this.state.columns.slice(0).reverse();
        } else {
            columns = [
                ...this.state.columns.slice(index, this.state.columns.length),
                ...this.state.columns.slice(0, index),
            ];
        }
        const editedRecord = this.props.list.editedRecord;
        for (const column of columns) {
            if (column.type !== "field") {
                continue;
            }
            const fieldName = column.name;
            // in findNextFocusableOnRow test is done by using classList
            // refactor
            if (!editedRecord.isReadonly(fieldName)) {
                const cell = this.tableRef.el.querySelector(
                    `.o_selected_row td[name=${fieldName}]`
                );
                if (cell) {
                    const toFocus = getTabableElements(cell)[0] || cell;
                    if (cell !== toFocus) {
                        debugger
                        if (column.widget === 'count_widget'){
                            toFocus.focus();
                            toFocus.value = '';
                        }
                        else{
                            this.focus(toFocus);
                        }
                        debugger
                        this.lastEditedCell = { column, record: editedRecord };
                        break;
                    }
                }
            }
        }
    },
    onClickCapture(record, ev) {
        this._super(...arguments);
        debugger
        if($(ev.target.parentElement)){
            $(ev.target.parentElement).addClass('selected_count_row');
        }
    }

});