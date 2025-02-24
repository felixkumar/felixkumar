/** @odoo-module */

import { _t, _lt } from "@web/core/l10n/translation";

import spreadsheet, {
    initCallbackRegistry,
} from "@spreadsheet/o_spreadsheet/o_spreadsheet_extended";

import PivotAutofillPlugin from "./plugins/pivot_autofill_plugin";
import PivotSidePanel from "./side_panels/pivot_list_side_panel";

import "./autofill";
import "./operational_transform";
import { insertPivot } from "./pivot_init_callback";

const { uiPluginRegistry, sidePanelRegistry, cellMenuRegistry } = spreadsheet.registries;

uiPluginRegistry.add("odooPivotAutofillPlugin", PivotAutofillPlugin);

sidePanelRegistry.add("PIVOT_PROPERTIES_PANEL", {
    title: () => _t("Pivot properties"),
    Body: PivotSidePanel,
});

initCallbackRegistry.add("insertPivot", insertPivot);

cellMenuRegistry.add("pivot_properties", {
    name: _lt("See pivot properties"),
    sequence: 170,
    action(env) {
        const { col, row } = env.model.getters.getPosition();
        const sheetId = env.model.getters.getActiveSheetId();
        const pivotId = env.model.getters.getPivotIdFromPosition(sheetId, col, row);
        env.model.dispatch("SELECT_PIVOT", { pivotId });
        env.openSidePanel("PIVOT_PROPERTIES_PANEL", {});
    },
    isVisible: (env) => {
        const { col, row } = env.model.getters.getPosition();
        const sheetId = env.model.getters.getActiveSheetId();
        return env.model.getters.isExistingPivot(env.model.getters.getPivotIdFromPosition(sheetId, col, row));
    },
});
