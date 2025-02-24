/** @odoo-module **/

import { EmbeddedControllersPatch } from "@knowledge/views/embedded_controllers_patch";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { patch } from "@web/core/utils/patch";
import { registry } from "@web/core/registry";

export class KnowledgeArticleItemsKanbanController extends KanbanController {
    /**
     * @override
     * Item creation is not allowed if the user can not edit the parent article
     */
    get canCreate() { 
        if (!this.env.knowledgeArticleUserCanWrite) {
            return false;
        }
        return super.canCreate;
    }
}

patch(KnowledgeArticleItemsKanbanController.prototype, 'knowledge_embedded_kanban_controller', EmbeddedControllersPatch);

registry.category("views").add('knowledge_article_view_kanban_embedded', {
    ...kanbanView,
    Controller: KnowledgeArticleItemsKanbanController
});
