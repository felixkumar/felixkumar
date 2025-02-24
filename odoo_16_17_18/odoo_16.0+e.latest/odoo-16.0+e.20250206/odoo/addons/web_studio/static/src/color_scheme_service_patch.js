/** @odoo-module */

import { ColorSchemeService } from "@web_enterprise/webclient/color_scheme/color_scheme_service";

import { browser } from "@web/core/browser/browser";
import { patch } from "@web/core/utils/patch";

patch(ColorSchemeService.prototype, "web_studio/webclient/color_scheme", {
    get effectiveColorScheme() {
        return browser.location.hash.includes("action=studio")
            ? "light"
            : this._super(...arguments);
    },
});
