/** @odoo-module **/

import { HtmlField } from "@web_editor/js/backend/html_field";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";


export class ExtraResources extends HtmlField {
    /*
    * The method to show extra resources list when the title is hovered
    */
    _onShowExtraResources(event) {
        this._onHideExtraResources();
        this.hint = document.createElement("div");
        this.hint.setAttribute("class", "business-appointment-extra-resources-hint");
        this.hint.innerHTML = this.props.value;
        event.currentTarget.after(this.hint);
    }
    /*
    * The method to hide extra resources list when the title is out
    */
    _onHideExtraResources() {
        if (this.hint) { this.hint.remove() };
    }
};

ExtraResources.supportedTypes = ["html"];
ExtraResources.template = "business_appointment.ExtraResources";
ExtraResources.props = { ...HtmlField.props };

registry.category("fields").add("extraResourcesHint", ExtraResources);
