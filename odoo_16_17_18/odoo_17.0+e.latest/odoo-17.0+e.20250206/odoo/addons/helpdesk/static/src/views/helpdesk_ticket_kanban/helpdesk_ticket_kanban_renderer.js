/** @odoo-module */

import { KanbanRenderer } from '@web/views/kanban/kanban_renderer';
import { HelpdeskTicketKanbanHeader } from './helpdesk_ticket_kanban_header';

export class HelpdeskTicketRenderer extends KanbanRenderer {
    static components = {
        ...KanbanRenderer.components,
        KanbanHeader: HelpdeskTicketKanbanHeader,
    };

    canCreateGroup() {
        return super.canCreateGroup() && !!this.props.list.context.default_team_id;
    }
}
