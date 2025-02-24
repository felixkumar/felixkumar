/** @odoo-module alias=timesheet_grid.task_with_hours_grid **/

import field_registry from 'web.field_registry';
import TaskWithHours from 'hr_timesheet.task_with_hours';

const TaskWithHoursGrid = TaskWithHours.extend({
    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        this.DisplayDiscardDialog = true;
    },

    /**
     * @override
     * The M2ODialog is not available outside of the relational_fields.js file. To trigger it, we call the 'super' method which will do the job.
     */
    _onInputFocusout: function () {
        if (!this.floating || this.$input.val() === "") {
            return;
        }
        const firstValue = this.suggestions.find(s => s.id);
        if (firstValue) {
            this.reinitialize({ id: firstValue.id, display_name: firstValue.name });
        } else if (this.can_create && this.DisplayDiscardDialog) {
            this._super();
        } else {
            this.$input.val("");
        }
    },

});

field_registry.add('task_with_hours_grid', TaskWithHoursGrid);

export default TaskWithHoursGrid;
