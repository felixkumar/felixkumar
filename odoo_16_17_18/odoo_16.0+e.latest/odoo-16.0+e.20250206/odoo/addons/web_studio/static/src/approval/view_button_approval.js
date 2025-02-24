/** @odoo-module */

import { ViewButton } from "@web/views/view_button/view_button";
import { ViewCompiler } from "@web/views/view_compiler";
import { patch } from "@web/core/utils/patch";

import { StudioApproval } from "@web_studio/approval/studio_approval";
import { useApproval } from "@web_studio/approval/approval_hook";

patch(ViewCompiler.prototype, "web_studio.ViewCompilerApproval", {
    compileButton(el, params) {
        const button = this._super(...arguments);
        const studioApproval = el.getAttribute("studio_approval") === "True";
        if (studioApproval) {
            button.setAttribute("studioApproval", studioApproval);
        }
        return button;
    },
});

patch(ViewButton.prototype, "web_studio.ViewButtonApproval", {
    setup() {
        this._super(...arguments);
        if (this.props.studioApproval) {
            let { type, name } = this.props.clickParams;
            if (type && type.endsWith("=")) {
                type = type.slice(0, -1);
            }
            const action = type === "action" && name;
            const method = type === "object" && name;
            this.approval = useApproval({
                getRecord: (props) => props.record,
                action,
                method,
            });

            const onClickViewButton = this.env.onClickViewButton;
            owl.useSubEnv({
                onClickViewButton: (params) => {
                    params.beforeExecute = this.checkBeforeExecute.bind(this);
                    onClickViewButton(params);
                },
            });
        }
    },
    async checkBeforeExecute() {
        this.approval.willCheck = true;
        if (!this.approval.resId) {
            const model = this.props.record.model;
            const rec = "resId" in model.root ? model.root : this.props.record;
            await rec.save({ stayInEdition: true, useSaveErrorDialog: !this.env.inDialog });
        } else if (this.props.record && this.props.record.isDirty) {
            await this.props.record.save({
                stayInEdition: true,
                useSaveErrorDialog: !this.env.inDialog,
            });
        }
        return this.approval.checkApproval();
    },
});

ViewButton.props.push("studioApproval?");
ViewButton.components = Object.assign(ViewButton.components || {}, { StudioApproval });
