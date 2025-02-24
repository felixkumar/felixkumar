/** @odoo-module **/

import { DateTimeField } from "@web/views/fields/datetime/datetime_field";
import { formatDateTime } from "@web/core/l10n/dates";
import { localization } from "@web/core/l10n/localization";
import { registry } from "@web/core/registry";

class FsmDateWidget extends DateTimeField {
    /**
     * @override
     */
    get formattedValue() {
        const format = localization.timeFormat.search("HH") === 0 ? "HH:mm" : "hh:mm a";
        return formatDateTime(this.props.value, { format: format });
    }
    get className() {
        const date = new Date();
        const widgetcolor = this.props.record.data.planned_date_end < date && this.props.record.data.stage_id[1] !== 'Done' ? 'oe_kanban_text_red' : '';
        return widgetcolor;
    }
}

FsmDateWidget.template = 'industry_fsm.FsmDateWidget';

registry.category('fields').add('fsm_date', FsmDateWidget);
