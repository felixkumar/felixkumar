/** @odoo-module */

import { device } from "web.config";
import * as LegacyControlPanel from "web.ControlPanel";
import { useBackButton } from "web_mobile.hooks";
import { patch } from "@web/core/utils/patch";
import { ControlPanelSearchDialog } from "@web/search/control_panel/control_panel";


if (device.isMobile) {
    patch(LegacyControlPanel.prototype, "web_mobile", {
        setup() {
            this._super(...arguments);
            useBackButton(this._onBackButton.bind(this), () => this.state.showMobileSearch);
        },

        //---------------------------------------------------------------------
        // Handlers
        //---------------------------------------------------------------------

        /**
         * close mobile search on back-button
         * @private
         */
        _onBackButton() {
            this._resetSearchState();
        },
    });

    patch(ControlPanelSearchDialog.prototype, "web_mobile", {
        setup() {
            this._super(...arguments);
            useBackButton(this._onBackButton.bind(this));
        },

        //---------------------------------------------------------------------
        // Handlers
        //---------------------------------------------------------------------

        /**
         * close mobile search on back-button
         * @private
         */
        _onBackButton() {
            this.props.close();
        },
    });
}
