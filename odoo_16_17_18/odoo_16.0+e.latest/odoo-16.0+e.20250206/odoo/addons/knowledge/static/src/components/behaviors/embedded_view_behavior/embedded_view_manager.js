/** @odoo-module **/

import { CallbackRecorder } from "@web/webclient/actions/action_hook";
import { getDefaultConfig, View } from "@web/views/view";
import { PromptEmbeddedViewNameDialog } from "@knowledge/components/prompt_embedded_view_name_dialog/prompt_embedded_view_name_dialog";
import { useOwnDebugContext } from "@web/core/debug/debug_context";
import { useService } from "@web/core/utils/hooks";

const {
    Component,
    onWillStart,
    useSubEnv } = owl;

const EMBEDDED_VIEW_LIMITS = {
    kanban: 20,
    list: 40,
};

/**
 * Wrapper for the embedded view, manage the toolbar and the embedded view props
 */
export class EmbeddedViewManager extends Component {
    setup() {
        // allow access to the SearchModel exported state which contain facets
        this.__getGlobalState__ = new CallbackRecorder();

        this.actionService = useService('action');
        this.dialogService = useService('dialog');
        this.embedViewsFilterService = useService('knowledgeEmbedViewsFilters');

        useOwnDebugContext(); // define a debug context when the developer mode is enable
        const config = {
            ...getDefaultConfig(),
            disableSearchBarAutofocus: true,
        };

        /**
         * @param {ViewType} viewType
         * @param {Object} [props={}]
         */
        const switchView = (viewType, props = {}) => {
            if (this.action.type !== "ir.actions.act_window") {
                throw new Error('Can not open the view: The action is not an "ir.actions.act_window"');
            }
            if (props.resId) {
                this.action.res_id = props.resId;
            }
            this.action.globalState = this.getEmbeddedViewGlobalState();
            this.actionService.doAction(this.action, {
                viewType: viewType,
            });
        };

        const services = this.env.services;
        const extendedServices = Object.create(services);
        extendedServices.action = Object.create(services.action);
        extendedServices.action.switchView = switchView;

        useSubEnv({
            config,
            services: extendedServices,
            __getGlobalState__: this.__getGlobalState__,
        });
        onWillStart(this.onWillStart.bind(this));
    }

    /**
     * Extract the SearchModel state of the embedded view
     *
     * @returns {Object} globalState
     */
    getEmbeddedViewGlobalState() {
        const callbacks = this.__getGlobalState__.callbacks;
        let globalState;
        if (callbacks.length) {
            globalState = callbacks.reduce((res, callback) => {
                return { ...res, ...callback() };
            }, {});
        }
        return { searchModel: globalState && globalState.searchModel };
    }

    /**
     * Recover the action from its parsed state (attrs of the Behavior block)
     * and setup the embedded view props
     */
    onWillStart () {
        const { action, context, viewType } = this.props;
        const contextKeyOptionalFields = context.keyOptionalFields;
        if (contextKeyOptionalFields && !contextKeyOptionalFields.includes(context.knowledgeEmbeddedViewId)) {
            // If the key from the context does not contain the embeddedViewId this means that we are inserting
            // a brand new embed. Thus we are adding the optionalFields stored with contextKeyOptionalFields
            // inside the localStorage with a key that contains the embeddedViewId.
            // This way when we are rendering the embedded view and its fullscreen version we are using the correct
            // key and rendering the correct fields.
            const optionalFields = localStorage.getItem(contextKeyOptionalFields);
            if (optionalFields !== null && !localStorage.getItem(contextKeyOptionalFields+`,${context.knowledgeEmbeddedViewId}`)) {
                localStorage.setItem(contextKeyOptionalFields+`,${context.knowledgeEmbeddedViewId}`, optionalFields);
                context.keyOptionalFields = contextKeyOptionalFields+`,${context.knowledgeEmbeddedViewId}`;
            }
        }
        this.env.config.setDisplayName(action.display_name);
        this.env.config.views = action.views;
        const ViewProps = {
            resModel: action.res_model,
            context: context,
            domain: action.domain || [],
            type: viewType,
            loadIrFilters: true,
            loadActionMenus: true,
            globalState: { searchModel: context.knowledge_search_model_state },
            /**
             * @param {integer} recordId
             */
            selectRecord: recordId => {
                const [formViewId] = this.action.views.find((view) => {
                    return view[1] === 'form';
                }) || [false];
                this.saveEmbedViewFilters();
                this.actionService.doAction({
                    type: 'ir.actions.act_window',
                    res_model: action.res_model,
                    views: [[formViewId, 'form']],
                    res_id: recordId,
                });
            },
            createRecord: async () => {
                const [formViewId] = this.action.views.find((view) => {
                    return view[1] === 'form';
                }) || [false];
                this.saveEmbedViewFilters();
                this.actionService.doAction({
                    type: 'ir.actions.act_window',
                    res_model: action.res_model,
                    views: [[formViewId, 'form']],
                });
            },
        };
        if (action.search_view_id) {
            ViewProps.searchViewId = action.search_view_id[0];
        }
        if (context.orderBy) {
            try {
                ViewProps.orderBy = JSON.parse(context.orderBy);
            } catch {};
        }
        if (this.props.viewType in EMBEDDED_VIEW_LIMITS) {
            ViewProps.limit = EMBEDDED_VIEW_LIMITS[this.props.viewType];
        }

        this.embedViewsFilterService.applyFilter(
            this.actionService.currentController,
            this.props.context.knowledgeEmbeddedViewId,
            ViewProps
        );

        this.EmbeddedView = View;
        this.EmbeddedViewProps = ViewProps;
        this.action = action;
    }

    /**
     * Rename an embedded view
     */
    _onRenameBtnClick () {
        this.dialogService.add(PromptEmbeddedViewNameDialog, {
            isNew: false,
            defaultName: this.props.getTitle(),
            viewType: this.props.viewType,
            save: name => {
                this.props.setTitle(name);
            },
            close: () => {}
        });
    }

    /**
     * Open an embedded view (fullscreen)
     */
    _onOpenBtnClick () {
        if (this.action.type !== "ir.actions.act_window") {
            throw new Error('Can not open the view: The action is not an "ir.actions.act_window"');
        }
        const props = {};
        if (this.action.context.orderBy) {
            try {
                props.orderBy = JSON.parse(this.action.context.orderBy);
            } catch {};
        }
        this.saveEmbedViewFilters();
        this.action.globalState = this.getEmbeddedViewGlobalState();
        this.actionService.doAction(this.action, {
            viewType: this.props.viewType,
            props,
            additionalContext: { knowledgeEmbeddedViewId: this.props.context.knowledgeEmbeddedViewId }
        });
    }

    /**
     * This function is called when opening a record from an embedded list or kanban view or when creating
     * a new record in the said view.
     * This function calls the correct function of the filter service in order to save the searchModel of the
     * view.
     * By saving the searchModel we allow filters applied to a view to be reassigned to it when coming back
     * via the breadcrumbs created by opening/creating a record.
     */
    saveEmbedViewFilters() {
        this.embedViewsFilterService.saveFilters(
            this.actionService.currentController,
            this.props.context.knowledgeEmbeddedViewId,
            this.getEmbeddedViewGlobalState().searchModel
        );
    }
}

EmbeddedViewManager.template = 'knowledge.EmbeddedViewManager';
EmbeddedViewManager.props = {
    el: { type: HTMLElement },
    action: { type: Object },
    context: { type: Object },
    viewType: { type: String },
    setTitle: { type: Function },
    getTitle: { type: Function },
    readonly: { type: Boolean },
};
