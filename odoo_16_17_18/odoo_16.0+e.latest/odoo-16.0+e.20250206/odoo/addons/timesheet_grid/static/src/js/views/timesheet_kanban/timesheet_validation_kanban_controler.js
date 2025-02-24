/** @odoo-module **/

import { KanbanController } from "@web/views/kanban/kanban_controller";

export class TimesheetValidationKanbanController extends KanbanController {

    async validateTimesheet() {
        const resIds = this.model.root.records.map((datapoint) => datapoint.resId);
        const result = await this.model.orm.call(this.props.resModel, "action_validate_timesheet", [resIds]);
        await this.model.notificationService.add(result.params.title, { type: result.params.type });
        this.render(true);
    }

}
