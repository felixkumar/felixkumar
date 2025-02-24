/** @odoo-module **/

import { AccountMoveLineListController,AccountMoveLineListView } from "@account_accountant/components/move_line_list/move_line_list"


AccountMoveLineListView.Renderer.props = [
    "activeActions?",
    "list",
    "archInfo",
    "openRecord",
    "onAdd?",
    "cycleOnTab?",
    "allowSelectors?",
    "editable?",
    "noContentHelp?",
    "nestedKeyOptionalFieldsData?",
    "readonly?",
    'setSelectedRecord?',
    "ks_update_field_data?",
    "ks_initialize_lvm_data?",
    "list_data?",
    "ks_renderer_update?"
];





