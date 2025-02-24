/** @odoo-module */

import { useService } from "@web/core/utils/hooks";
import {
    Component,
    onMounted,
    onPatched,
    onWillDestroy,
    onWillPatch,
    onWillStart,
    useExternalListener,
} from "@odoo/owl";

let observerId = 0;

export class AbstractBehavior extends Component {
    setup() {
        super.setup();
        this.setupAnchor();
        this.uiService = useService('ui');
        this.knowledgeCommandsService = useService('knowledgeCommandsService');
        this.observerId = observerId++;
        if (!this.props.readonly) {
            onWillStart(() => {
                this.editor.observerUnactive(`knowledge_behavior_id_${this.observerId}`);
            });
            onWillPatch(() => {
                this.editor.observerUnactive(`knowledge_behavior_id_${this.observerId}`);
            });
            onMounted(() => {
                // Remove non-owl nodes after the mount process because we
                // never want the HtmlField to be in a "corrupted" state
                // during an asynchronous timespan so we cannot remove them
                // earlier.
                this.props.blueprintNodes.forEach(child => child.remove());
                this.editor.idSet(this.props.anchor);
                this.editor.observerActive(`knowledge_behavior_id_${this.observerId}`);
            });
            onPatched(() => {
                this.editor.idSet(this.props.anchor);
                this.editor.observerActive(`knowledge_behavior_id_${this.observerId}`);
            });
            onWillDestroy(() => {
                this.editor.observerActive(`knowledge_behavior_id_${this.observerId}`);
            });
        } else {
            onMounted(() => {
                this.props.blueprintNodes.forEach(child => child.remove());
            });
        }
    }

    /**
     * Normally, the editable is the only element in the editor which has the focus.
     * With behaviors however (and most notably embedded views), it can be useful to delegate the focus at a lower level
     * (i.e. to use hotkeys with the uiService).
     * Also, since "focus" and "blur" events don't bubble, and the "blur" event is used to handle a dirty field for saving purpose,
     * it has to sometimes be triggered programmatically for a proper save.
     *
     * We are adding tabindex="-1" to the anchor because this attribute is needed to capture the
     * 'focusin' and 'focusout' events.
     * In these events we are using activateElement/deactivateElement:
     *
     * `activateElement` is used to set the anchor as an active element in the ui service, this enables
     * us to contain the events inside the embedded view when it has the focus.
     *
     * `deactivateElement` removes the anchor as an active element, leaving only the document as active
     * and we come back to the default behavior of the document handling all the events.
     *
     */
    handleFocusEvents() {
        this.props.anchor.setAttribute('tabindex', '-1');
        useExternalListener(this.props.anchor, 'focusin', () => {
            if (!this.props.anchor.contains(this.uiService.activeElement)) {
                this.uiService.activateElement(this.props.anchor);
            }
        });
        useExternalListener(this.props.anchor, 'focusout', (event) => {
            if (!this.props.anchor.contains(event.relatedTarget)) {
                this.uiService.deactivateElement(this.props.anchor);
                if (!this.props.readonly && !this.editor.editable.contains(event.relatedTarget)) {
                    this.editor.editable.dispatchEvent(new FocusEvent('blur', {relatedTarget: event.relatedTarget}));
                }
            }
        });
    }

    /**
     * This method is used to ensure that the correct attributes are set
     * on the anchor of the Behavior. Attributes could be incorrect for the
     * following reasons: cleaned by the sanitization (frontend or backend),
     * attributes from a previous Odoo version, attributes from a drop/paste
     * of a Behavior which was in another state (i.e. from readonly to editable)
     */
    setupAnchor() {
        this.handleFocusEvents();
        if (!this.props.readonly) {
            this.props.anchor.setAttribute('contenteditable', 'false');
        }
    }

    get editor () {
        return this.props.wysiwyg ? this.props.wysiwyg.odooEditor : undefined;
    }
}

AbstractBehavior.props = {
    readonly: { type: Boolean },
    anchor: { type: Element },
    wysiwyg: { type: Object, optional: true},
    record: { type: Object },
    root: { type: Element },
    // TODO: make it mandatory in master, as a bugfix we don't add required
    // props.
    blueprintNodes: { type: Array, optional: true },
};

AbstractBehavior.defaultProps = {
    blueprintNodes: [],
}
