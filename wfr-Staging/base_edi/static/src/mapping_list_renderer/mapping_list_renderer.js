/* @odoo-module */

import { ListRenderer } from '@web/views/list/list_renderer';

const { useState } = owl;

export class MappingListRenderer extends ListRenderer {
    setup() {
        super.setup(arguments);
        this.rowState = useState({
            recordsToDisplay: [],
        });
        this.expandedRecords = new Set();
        this.parentToChildrenMap = this.props.list.records.reduce((map, record) => {
            map[record.data.id] = record.data.child_ids.records.map(child => child.data.id)
            return map;
        }, {})
        this.recomputeShownRecords();
    }

    recomputeShownRecords() {
        let recordsToDisplay = []
        for (let record of this.props.list.records) {
            if (!record.data.parent_id || this.expandedRecords.has(record.data.parent_id[0])) {
                recordsToDisplay.push(record);
            }
        }
        this.rowState.recordsToDisplay = recordsToDisplay;
    }

    expandChildren(record) {
        this.expandedRecords.add(record.data.id);
        this.recomputeShownRecords();
    }

    collapseChildren(record) {
        this.expandedRecords.delete(record.data.id);
        this._hideAllDescendants(record.data.id);
        this.recomputeShownRecords();
    }

    _hideAllDescendants(parentId) {
        for (let childId of this.parentToChildrenMap[parentId]) {
            if (this.expandedRecords.has(childId)) {
                this.expandedRecords.delete(childId);
                this._hideAllDescendants(childId);
            }
        }
    }
}

MappingListRenderer.rowsTemplate = 'base_edi.MappingListRenderer.Rows';
MappingListRenderer.recordRowTemplate = 'base_edi.MappingListRenderer.RecordRow';