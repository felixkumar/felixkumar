/** @odoo-module */

import { _t } from "web.core";
import { CalendarRenderer } from "@web/views/calendar/calendar_renderer";
import { GraphRenderer } from "@web/views/graph/graph_renderer";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { ListRenderer } from "@web/views/list/list_renderer";
import { MapRenderer } from "@web_map/map_view/map_renderer";
import { patch } from "@web/core/utils/patch";
import { PivotRenderer } from "@web/views/pivot/pivot_renderer";
import { SelectCreateDialog } from "@web/views/view_dialogs/select_create_dialog";
import {
    useBus,
    useOwnedDialogs,
    useService } from "@web/core/utils/hooks";
import { omit } from "@web/core/utils/objects";

/**
 * The following patch will add two new entries to the 'Favorites' dropdown menu
 * of the control panel namely: 'Insert view in article' and 'Insert link in article'.
 */
const EmbeddedViewRendererPatch = {
    setup() {
        this._super(...arguments);
        if (this.env.searchModel) {
            useBus(this.env.searchModel, 'insert-embedded-view', this._insertEmbeddedView.bind(this));
            useBus(this.env.searchModel, 'insert-view-link', this._insertViewLink.bind(this));
            this.orm = useService('orm');
            this.actionService = useService('action');
            this.addDialog = useOwnedDialogs();
            this.userService = useService('user');
        }
    },
    /**
     * Returns the full context that will be passed to the embedded view.
     * @returns {Object}
     */
    _getViewContext: function () {
        const context = {};
        if (this.env.searchModel) {
            // Store the context of the search model:
            Object.assign(context, omit(this.env.searchModel.context, ...Object.keys(this.userService.context)));
            // Store the state of the search model:
            Object.assign(context, {
                knowledge_search_model_state: JSON.stringify(this.env.searchModel.exportState())
            });
        }
        // Store the "local context" of the view:
        const fns = this.env.__getContext__.callbacks;
        const localContext = Object.assign({}, ...fns.map(fn => fn()));
        Object.assign(context, localContext);
        Object.assign(context, {
            knowledge_embedded_view_framework: 'owl'
        });
        return context;
    },
    _insertEmbeddedView: function () {
        const config = this.env.config;
        if (config.actionType !== 'ir.actions.act_window') {
            return;
        }
        this._openArticleSelector(async id => {
            const context = this._getViewContext();
            context['keyOptionalFields'] = this.keyOptionalFields;
            await this.orm.call('knowledge.article', 'append_embedded_view',
                [[id],
                config.actionId,
                config.viewType,
                config.getDisplayName(),
                context]
            );
            this.actionService.doAction('knowledge.ir_actions_server_knowledge_home_page', {
                additionalContext: {
                    res_id: id
                }
            });
        });
    },
    /**
     * Inserts a new link in the article redirecting the user to the current view.
     */
    _insertViewLink: function () {
        const config = this.env.config;
        if (config.actionType !== 'ir.actions.act_window') {
            return;
        }
        this._openArticleSelector(async id => {
            const context = this._getViewContext();
            await this.orm.call('knowledge.article', 'append_view_link',
                [[id],
                config.actionId,
                config.viewType,
                config.getDisplayName(),
                context]
            );
            this.actionService.doAction('knowledge.ir_actions_server_knowledge_home_page', {
                additionalContext: {
                    res_id: id
                }
            });
        });
    },
    /**
     * @param {Function} onSelectCallback
     */
    _openArticleSelector: function (onSelectCallback) {
        this.addDialog(SelectCreateDialog, {
            title: _t('Select an article'),
            noCreate: false,
            multiSelect: false,
            resModel: 'knowledge.article',
            context: {},
            domain: [
                ['user_has_write_access', '=', true]
            ],
            onSelected: resIds => {
                onSelectCallback(resIds[0]);
            },
            onCreateEdit: async () => {
                const articleId = await this.orm.call('knowledge.article', 'article_create', [], {
                    is_private: true
                });
                onSelectCallback(articleId);
            },
        });
    },
};

const EmbeddedViewListRendererPatch = {
    ...EmbeddedViewRendererPatch,
    /**
     * @override
     * @returns {Object}
     */
    _getViewContext: function () {
        const context = EmbeddedViewRendererPatch._getViewContext.call(this);
        Object.assign(context, {
            orderBy: JSON.stringify(this.props.list.orderBy)
        });
        return context;
    },
    /**
     * When the user hides/shows some columns from the list view, the system will
     * add a new cache entry in the local storage of the user and will list all
     * visible columns for the current view. To make the configuration specific to
     * a view, the system generates a unique key for the cache entry by using all
     * available information about the view.
     *
     * When loading the view, the system regenerates a key from the current view
     * and check if there is any entry in the cache for that key. If there is a
     * match, the system will load the configuration specified in the cache entry.
     *
     * For the embedded views of Knowledge, we want the configuration of the view
     * to be unique for each embedded view. To achieve that, we will overwrite the
     * function generating the key for the cache entry and include the unique id
     * of the embedded view.
     *
     * @override
     * @returns {string}
     */
    createKeyOptionalFields () {
        const embeddedViewId = this.env.searchModel ? this.env.searchModel.context.knowledgeEmbeddedViewId : null;
        if (this.env.searchModel && this.env.searchModel.context.keyOptionalFields) {
            const searchModelKeyOptionalFields = this.env.searchModel.context.keyOptionalFields;
            return searchModelKeyOptionalFields.includes(embeddedViewId)
                ? searchModelKeyOptionalFields
                : searchModelKeyOptionalFields + (embeddedViewId ? `,${embeddedViewId}` : "");
        }
        return this._super(...arguments) + (embeddedViewId ? "," + embeddedViewId : "");
    },
};

patch(CalendarRenderer.prototype, 'knowledge_calendar_embeddable', EmbeddedViewRendererPatch);
patch(GraphRenderer.prototype, 'knowledge_graph_embeddable', EmbeddedViewRendererPatch);
patch(KanbanRenderer.prototype, 'knowledge_kanban_embeddable', EmbeddedViewRendererPatch);
patch(ListRenderer.prototype, 'knowledge_list_embeddable', EmbeddedViewListRendererPatch);
patch(MapRenderer.prototype, 'knowledge_map_embeddable', EmbeddedViewRendererPatch);
patch(PivotRenderer.prototype, 'knowledge_pivot_embeddable', EmbeddedViewRendererPatch);

const supportedEmbeddedViews = new Set([
    'calendar',
    'graph',
    'kanban',
    'list',
    'map',
    'pivot',
]);

odoo.ready("web.assets_backend").then(async () => {
    try {
        const { CohortRenderer } = await odoo.runtimeImport("@web_cohort/cohort_renderer");
        patch(CohortRenderer.prototype, "knowledge_cohort_embeddable", EmbeddedViewRendererPatch);
        supportedEmbeddedViews.add("cohort");
    } catch {}
});

export {
    supportedEmbeddedViews,
};
