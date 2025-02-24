/** @odoo-module */

import { HtmlField } from "@web_editor/js/backend/html_field";
import { KnowledgePlugin } from "@knowledge/js/knowledge_plugin";
import { patch } from "@web/core/utils/patch";
import { decodeDataBehaviorProps } from "@knowledge/js/knowledge_utils";
import { Deferred, Mutex } from "@web/core/utils/concurrency";
import { useService } from "@web/core/utils/hooks";

// Behaviors:

import { ArticleBehavior } from "@knowledge/components/behaviors/article_behavior/article_behavior";
import { ArticlesStructureBehavior } from "@knowledge/components/behaviors/articles_structure_behavior/articles_structure_behavior";
import { FileBehavior } from "@knowledge/components/behaviors/file_behavior/file_behavior";
import { EmbeddedViewBehavior } from "@knowledge/components/behaviors/embedded_view_behavior/embedded_view_behavior";
import { TemplateBehavior } from "@knowledge/components/behaviors/template_behavior/template_behavior";
import { TableOfContentBehavior } from "@knowledge/components/behaviors/table_of_content_behavior/table_of_content_behavior";
import { ViewLinkBehavior } from "@knowledge/components/behaviors/view_link_behavior/view_link_behavior";

import {
    markup,
    onWillDestroy,
    onWillUnmount,
    useEffect,
    useRef,
} from "@odoo/owl";

const behaviorTypes = {
    o_knowledge_behavior_type_article: {
        Behavior: ArticleBehavior,
    },
    o_knowledge_behavior_type_file: {
        Behavior: FileBehavior,
    },
    o_knowledge_behavior_type_template: {
        Behavior: TemplateBehavior,
    },
    o_knowledge_behavior_type_toc: {
        Behavior: TableOfContentBehavior,
    },
    o_knowledge_behavior_type_articles_structure: {
        Behavior: ArticlesStructureBehavior
    },
    o_knowledge_behavior_type_embedded_view: {
        Behavior: EmbeddedViewBehavior
    },
    o_knowledge_behavior_type_view_link: {
        Behavior: ViewLinkBehavior
    },
};

const HtmlFieldPatch = {
    setup() {
        this._super(...arguments);
        this.uiService = useService('ui');
        this.behaviorState = {
            // Owl does not support destroying a Root when its container node is
            // not in the DOM. This reference is a `d-none` element used to
            // re-insert anchors of live Behavior Root before calling `destroy`
            // to circumvent the Owl limitation.
            handlerRef: useRef("behaviorHandler"),
            // Set of anchor elements with an active Behavior (Owl Root) used to
            // keep track of them.
            appAnchors: new Set(),
            // Mutex to prevent multiple _updateBehavior methods running at
            // once.
            updateMutex: new Mutex(),
            // Element currently being observed for Behaviors Components.
            observedElement: null,
            // Observer responsible for mounting Behaviors coming to the DOM,
            // and destroying those that are removed.
            appAnchorsObserver: new MutationObserver(() => {
                // Clean Behaviors that are not currently in the DOM.
                const anchors = this.behaviorState.observedElement.querySelectorAll('.o_knowledge_behavior_anchor');
                this.destroyBehaviorApps(new Set(anchors));
                // Schedule a scan for new Behavior anchors to render.
                this.updateBehaviors();
            }),
        };
        // Update Behaviors and reset the observer when the html_field
        // DOM element changes.
        useEffect(() => {
            if (this.behaviorState.observedElement !== this.injectorEl) {
                // The observed Element has to be replaced.
                this.behaviorState.appAnchorsObserver.disconnect();
                this.behaviorState.observedElement = null;
                this.destroyBehaviorApps();
                if (this.props.readonly || (this.wysiwyg && this.wysiwyg.odooEditor)) {
                    // Restart the observer only if the html_field element is
                    // ready to display its value. If it is not ready (async),
                    // it will be started in @see startWysiwyg.
                    this.startAppAnchorsObserver();
                    this.updateBehaviors();
                }
            }
        }, () => {
            return [this.injectorEl];
        });
        onWillUnmount(() => {
            if (this.wysiwyg && this.wysiwyg.$editable) {
                this._removeRefreshBehaviorsListeners();
            }
        });
        onWillDestroy(() => {
            this.behaviorState.appAnchorsObserver.disconnect();
            this.destroyBehaviorApps();
        });
    },
    /**
     * Destroy all currently active Behavior Roots except those which anchor
     * is in `ignoredAnchors`.
     *
     * @param {Set<Element>} ignoredAnchors optional - Set of anchors to ignore
     *        for the destruction of Behavior Roots
     */
    destroyBehaviorApps(ignoredAnchors=new Set()) {
        for (const anchor of Array.from(this.behaviorState.appAnchors)) {
            if (!ignoredAnchors.has(anchor)) {
                this.destroyBehaviorApp(anchor);
            }
        }
    },
    /**
     * Destroy a Behavior Root.
     *
     * Considerations:
     * - To mount the Behavior Root at a later time based on the same anchor
     * where it was destroyed, it is necessary to keep some Component nodes
     * inside. Since Owl:ComponentNode.destroy removes all its DOM nodes, this
     * method has to clone them beforehand to preserve them.
     * - An Owl Root has to be destroyed in the DOM (Owl constraint), but the
     * OdooEditor has no hook to tell if a node will be removed or not.
     * Therefore this method can be called by a MutationObserver, at which point
     * the anchor is not in the DOM anymore and it has to be reinserted before
     * the Root can be destroyed. It is done in a custom `d-none` element aside
     * the editable.
     * - Cloned child nodes can be re-inserted after the Root destruction in the
     * anchor. It is important to do it even if the anchor is not in the DOM
     * anymore since that same anchor can be re-inserted in the DOM with an
     * editor `undo`.
     *
     * @param {HTMLElement} anchor in which the Behavior is mounted
     */
    destroyBehaviorApp(anchor) {
        // Deactivate the Element in UI service to prevent unwanted behaviors
        this.uiService.deactivateElement(anchor);
        // Preserve the anchor children since they will be removed by the
        // Root destruction.
        const clonedAnchor = anchor.cloneNode(true);
        for (const node of clonedAnchor.querySelectorAll('.o_knowledge_clean_for_save')) {
            node.remove();
        }
        let shouldBeRemoved = false;
        let shouldBeRestored = false;
        const parentNode = anchor.parentNode;
        if (!document.body.contains(anchor)) {
            // If anchor has a parent outside the DOM, it has to be given back
            // to its parent after being destroyed, so it is replaced by its
            // clone (to keep track of its position).
            if (parentNode) {
                parentNode.replaceChild(clonedAnchor, anchor);
                shouldBeRestored = true;
            } else {
                shouldBeRemoved = true;
            }
            // A Component should always be destroyed in the DOM.
            this.behaviorState.handlerRef.el.append(anchor);
        }
        anchor.oKnowledgeBehavior.updatePromise.resolve(false);
        anchor.oKnowledgeBehavior.destroy();
        delete anchor.oKnowledgeBehavior;
        if (shouldBeRemoved) {
            anchor.remove();
        } else if (shouldBeRestored) {
            // Give back the anchor to its original parent (before destroying).
            parentNode.replaceChild(anchor, clonedAnchor);
        }
        // Recover the child nodes from the clone because OWL removed all of
        // them, but they are necessary to re-render the Component later.
        // (it's the blueprint of the Behavior).
        anchor.replaceChildren(...clonedAnchor.childNodes);
        this.behaviorState.appAnchors.delete(anchor);
    },
    /**
     * Observe the element containing the html_field value in the DOM.
     * Since that element can change during the lifetime of the html_field, the
     * observed element has to be held in a custom property (typically to
     * disconnect the observer).
     */
    startAppAnchorsObserver() {
        this.behaviorState.observedElement = this.injectorEl;
        this.behaviorState.appAnchorsObserver.observe(this.behaviorState.observedElement, {
            subtree: true,
            childList: true,
        });
    },
    /**
     * @returns {Object}
     */
    get behaviorTypes() {
        return behaviorTypes;
    },
    /**
     * @returns {HTMLElement}
     */
    get injectorEl() {
        if (this.props.readonly && this.readonlyElementRef.el) {
            return this.readonlyElementRef.el;
        } else if (this.wysiwyg && this.wysiwyg.odooEditor) {
            return this.wysiwyg.odooEditor.editable;
        }
        return null;
    },
    /**
     * @override
     * @param {Widget} wysiwyg
     */
    async startWysiwyg(wysiwyg) {
        await this._super(...arguments);
        this._addRefreshBehaviorsListeners();
        this.startAppAnchorsObserver();
        await this.updateBehaviors();
    },
    /**
     * This function is called in the process of commitChanges and will disable
     * Behavior rendering and destroy all currently active Behaviors, because
     * the super function will do heavy changes in the DOM that are not
     * supported by OWL.
     * Behaviors rendering is re-enabled after the processing of the super
     * function is done, but Behaviors are not restarted (they will be in
     * updateValue, function that is called after _toInline if the html_field
     * is not in a destroyed Owl state).
     *
     * @override
     */
    async _toInline() {
        const _super = this._super.bind(this);
        // Prevent any new Behavior rendering during `toInline` processing.
        this.behaviorState.appAnchorsObserver.disconnect();
        this._removeRefreshBehaviorsListeners();
        // Wait for the `udpateBehaviors` mutex to ensure that it is idle during
        // `toInline` processing (we don't want it to mess with DOM nodes).
        await this.behaviorState.updateMutex.getUnlockedDef();
        // Destroy all Behaviors because `toInline` will apply heavy changes
        // in the DOM that are not supported by OWL. The nodes generated by
        // OWL stay in the DOM as the html_field value, but are not managed
        // by OWL during the `toInline` processing.
        this.destroyBehaviorApps();
        await _super(...arguments);
        // Reactivate Behavior rendering.
        this._addRefreshBehaviorsListeners();
        this.startAppAnchorsObserver();
    },
    /**
     * This method should stay quasi-synchronous and is not allowed to await
     * more than the super promise, because it is used in the process of an
     * urgentSave during a `beforeunload` handling, and the browser does not
     * let enough time to add many asynchronous calls, and definitely not enough
     * time for a rpc roundtrip.
     *
     * @override
     */
    async updateValue() {
        const promise = this._super(...arguments);
        // Update Behaviors after the updateValue to ensure that they all are
        // properly mounted (they could have been destroyed by `_toInline`).
        promise.then(() => this.updateBehaviors());
        // Return the `super` promise, not the `then` promise, so that the
        // urgentSave can continue even when Behaviors are being mounted.
        return promise;
    },
    /**
     * Mount Behaviors in visible anchors that should contain one.
     *
     * Since any mutation can trigger an updateBehaviors call, the mutex ensure
     * that the next updateBehaviors call always await the previous one.
     *
     * @param {Array[Object]} behaviorsData - optional - Contains information on
     *                        which Behavior to update. If not set, the
     *                        html_field will handle every visible Behavior
     *                        Composed by:
     *     @param {HTMLElement} [behaviorsData.anchor] Element which content
     *                          will be replaced by the rendered Component
     *                          (Behavior)
     *     @param {string} [behaviorsData.behaviorType] Class name of the
     *                      Behavior @see behaviorTypes
     *     edit mode only options:
     *     @param {boolean} [behaviorsData.setCursor] optional - Whether to use
     *                      the setCursor method of the Behavior if it has one
     *                      when it is mounted.
     * @param {HtmlElement} target - optional - the node to scan for new
     *                      Behavior to instanciate. Defaults to this.injectorEl
     * @returns {Promise} Resolved when the mutex updating Behaviors is idle.
     */
    async updateBehaviors(behaviorsData = [], target = null) {
        this.behaviorState.updateMutex.exec(() => this._updateBehaviors(behaviorsData, target));
        return this.behaviorState.updateMutex.getUnlockedDef();
    },
    async _updateBehaviors(behaviorsData, target) {
        const injectorEl = target || this.injectorEl;
        if (!document.body.contains(injectorEl)) {
            return;
        }
        if (!behaviorsData.length) {
            this._scanFieldForBehaviors(behaviorsData, injectorEl);
        }
        const promises = [];
        for (const behaviorData of behaviorsData) {
            const anchor = behaviorData.anchor;
            if (!document.body.contains(anchor)) {
                // trying to mount components on nodes that were removed from
                // the dom => no need to handle the current anchor.
                // this is due to the fact that this function is asynchronous
                // but onPatched and onMounted are synchronous and do not
                // wait for their content to finish so the life cycle of
                // the component can continue during the execution of this
                // function
                continue;
            }
            const {Behavior} = this.behaviorTypes[behaviorData.behaviorType] || {};
            if (!Behavior) {
                continue;
            }
            if (!anchor.oKnowledgeBehavior) {
                if (!this.props.readonly && this.wysiwyg && this.wysiwyg.odooEditor) {
                    this.wysiwyg.odooEditor.observerUnactive('injectBehavior');
                }
                // parse html to get all data-behavior-props content nodes
                const props = {
                    readonly: this.props.readonly,
                    anchor: anchor,
                    wysiwyg: this.wysiwyg,
                    record: this.props.record,
                    root: this.injectorEl,
                    blueprintNodes: [...anchor.childNodes],
                };
                let behaviorProps = {};
                if (anchor.hasAttribute("data-behavior-props")) {
                    try {
                        behaviorProps = decodeDataBehaviorProps(anchor.dataset.behaviorProps);
                    } catch {}
                }
                for (const prop in behaviorProps) {
                    if (prop in Behavior.props) {
                        props[prop] = behaviorProps[prop];
                    }
                }
                const propNodes = anchor.querySelectorAll("[data-prop-name]");
                for (const node of propNodes) {
                    if (node.dataset.propName in Behavior.props) {
                        // safe because sanitized by the editor and backend
                        props[node.dataset.propName] = markup(node.innerHTML);
                    }
                }
                if (!this.props.readonly && this.wysiwyg && this.wysiwyg.odooEditor) {
                    this.wysiwyg.odooEditor.observerActive('injectBehavior');
                }
                const app = this.__owl__.app;
                const { env } = app;
                anchor.oKnowledgeBehavior = app.createRoot(Behavior, {
                    props,
                    env,
                });
                this.behaviorState.appAnchors.add(anchor);
                // App.mountNode promise is not resolved if the Root is destroyed before it
                // is mounted, so instead, await a Deferred that is resolved
                // when the Root is mounted (true) or destroyed (false).
                const updatePromise = new Deferred();
                anchor.oKnowledgeBehavior.updatePromise = updatePromise;
                anchor.oKnowledgeBehavior.mount(anchor).then(
                    () => updatePromise.resolve(true)
                );
                const promise = anchor.oKnowledgeBehavior.updatePromise.then(async (isMounted) => {
                    // isMounted is true if the Root was mounted and false if it
                    // was destroyed before being mounted. If it was mounted,
                    // update child behaviors inside anchor
                    if (isMounted) {
                        await this._updateBehaviors([], anchor);
                    }
                });
                promises.push(promise);
            }
        }
        await Promise.all(promises);
        if (!this.props.readonly && this.wysiwyg && this.wysiwyg.odooEditor) {
            for (const behaviorData of behaviorsData.reverse()) {
                if (
                    behaviorData.setCursor && behaviorData.anchor.oKnowledgeBehavior &&
                    behaviorData.anchor.oKnowledgeBehavior.node.component.setCursor
                ) {
                    behaviorData.anchor.oKnowledgeBehavior.node.component.setCursor();
                    break;
                }
            }
        }
    },
    _addRefreshBehaviorsListeners() {
        if (this.wysiwyg && this.wysiwyg.$editable && this.wysiwyg.$editable.length) {
            this.wysiwyg.$editable.on('refresh_behaviors', this._onRefreshBehaviors.bind(this));
        }
    },
    _onRefreshBehaviors(e, data = {}) {
        this.updateBehaviors("behaviorsData" in data ? data.behaviorsData : []);
    },
    _removeRefreshBehaviorsListeners() {
        if (this.wysiwyg && this.wysiwyg.$editable && this.wysiwyg.$editable.length) {
            this.wysiwyg.$editable.off('refresh_behaviors');
        }
    },
    /**
     * Scans the target for Behaviors to mount.
     *
     * @param {Array[Object]} behaviorsData Array that will be filled with the
     *        results of the scan. Any Behavior that is not instanciated at the
     *        moment of the scan will have one entry added in this Array, with
     *        the condition that it is not a child of another Behavior that is
     *        not mounted yet (those will have to be scanned again when their
     *        parent is mounted, because their anchor will change).
     *        Existing items of the Array will not be altered.
     * @param {HTMLElement} target Element to scan for Behaviors
     */
    _scanFieldForBehaviors(behaviorsData, target) {
        const types = new Set(Object.getOwnPropertyNames(this.behaviorTypes));
        const anchorNodes = target.querySelectorAll('.o_knowledge_behavior_anchor');
        const anchorNodesSet = new Set(anchorNodes);
        // Iterate over the list of nodes while the set will be modified.
        // Only keep anchors of Behaviors that have to be rendered first.
        for (const anchorNode of anchorNodes) {
            if (!anchorNodesSet.has(anchorNode)) {
                // anchor was already removed (child of another anchor)
                continue;
            }
            if (anchorNode.oKnowledgeBehavior) {
                anchorNodesSet.delete(anchorNode);
            } else {
                // If the Behavior in anchorNode is not already mounted, remove
                // its children Behaviors from the scan, as their anchor will
                // change when this Behavior is mounted (replace all children
                // nodes by their mounted version). They will be mounted after
                // their parent during _updateBehaviors.
                const anchorSubNodes = anchorNode.querySelectorAll('.o_knowledge_behavior_anchor');
                for (const anchorSubNode of anchorSubNodes) {
                    anchorNodesSet.delete(anchorSubNode);
                }
            }
        }
        for (const anchor of anchorNodesSet) {
            const type = Array.from(anchor.classList).find(className => types.has(className));
            if (type) {
                behaviorsData.push({
                    anchor: anchor,
                    behaviorType: type,
                });
            }
        }
    },
};

const extractProps = HtmlField.extractProps;

HtmlField.extractProps = ({ attrs, field }) => {
    const props = extractProps({ attrs, field });
    props.wysiwygOptions.knowledgeCommands = attrs.options.knowledge_commands;
    props.wysiwygOptions.editorPlugins.push(KnowledgePlugin);
    return props;
};

patch(HtmlField.prototype, 'knowledge_html_field', HtmlFieldPatch);
