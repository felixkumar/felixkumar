/** @odoo-module */

import { useService } from "@web/core/utils/hooks";
import { KanbanController } from '@web/views/kanban/kanban_controller';

export class MrpWorkorderKanbanController extends KanbanController {

    setup() {
        super.setup();
        this.context = {
            'from_manufacturing_order': this.props.context.from_manufacturing_order,
            'from_production_order': this.props.context.from_production_order,
        };
        this.orm = useService('orm');
    }

    actionBack() {
        this.actionService.doAction('mrp.mrp_workcenter_kanban_action', {
            clearBreadcrumbs: true,
        });
    }

    async openRecord(record, mode) {
        const action = await this.orm.call(
            'mrp.workorder',
            'open_tablet_view',
            [record.resId],
        );
        Object.assign(action.context, this.context);
        this.actionService.doAction(action);
    }
}
