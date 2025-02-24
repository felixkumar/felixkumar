/** @odoo-module */

import { AbstractMacro } from "@knowledge/macros/abstract_macro";
import { dragAndDrop } from "@knowledge/macros/utils";

export class UseAsAttachmentMacro extends AbstractMacro {
    /**
     * @override
     * @returns {Array[Object]}
     */
    macroAction() {
        const action = super.macroAction();
        let attachFilesLastClickedEl = null;
        action.steps.push({
            trigger: function() {
                this.validatePage();
                const el = this.getFirstVisibleElement('.o_ChatterTopbar_buttonToggleAttachments:not([disabled])');
                if (el) {
                    const attachmentBoxEl = this.getFirstVisibleElement('.o_AttachmentBox_content');
                    if (attachmentBoxEl) {
                        return attachmentBoxEl;
                    } else if (el !== attachFilesLastClickedEl) {
                        el.click();
                        attachFilesLastClickedEl = el;
                    }
                } else {
                    this.searchInXmlDocNotebookTab('.oe_chatter');
                }
                return null;
            }.bind(this),
            action: (el) => el.scrollIntoView(),
        }, this.unblockUI);
        return action;
    }
}

export class AttachToMessageMacro extends AbstractMacro {
    /**
     * @override
     * @returns {Array[Object]}
     */
    macroAction() {
        const action = super.macroAction();
        let sendMessageLastClickedEl = null;
        action.steps.push({
            trigger: function() {
                this.validatePage();
                const el = this.getFirstVisibleElement('.o_ChatterTopbar_buttonSendMessage:not([disabled])');
                if (el) {
                    if (el.classList.contains('o-active')) {
                        return el;
                    } else if (el !== sendMessageLastClickedEl) {
                        el.click();
                        sendMessageLastClickedEl = el;
                    }
                } else {
                    this.searchInXmlDocNotebookTab('.oe_chatter');
                }
                return null;
            }.bind(this),
            action: (el) => {
                el.scrollIntoView();
            },
        }, {
            trigger: function() {
                this.validatePage();
                return this.getFirstVisibleElement('.o_Composer_buttonAttachment:not([disabled])');
            }.bind(this),
            action: dragAndDrop.bind(this, 'dragenter', this.data.dataTransfer),
        }, {
            trigger: function () {
                this.validatePage();
                return this.getFirstVisibleElement('.o_Composer_dropZone');
            }.bind(this),
            action: dragAndDrop.bind(this, 'drop', this.data.dataTransfer),
        }, this.unblockUI);
        return action;
    }
}
