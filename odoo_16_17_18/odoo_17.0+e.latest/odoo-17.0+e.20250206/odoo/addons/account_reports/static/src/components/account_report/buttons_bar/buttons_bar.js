/** @odoo-module */

import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";

import { Component, useState } from "@odoo/owl";

export class AccountReportButtonsBar extends Component {
    static template = "account_reports.AccountReportButtonsBar";
    static props = {};

    static components = {
        Dropdown,
        DropdownItem,
    };

    setup() {
        this.controller = useState(this.env.controller);
    }

    //------------------------------------------------------------------------------------------------------------------
    // Buttons
    //------------------------------------------------------------------------------------------------------------------
    get buttons() {
        const buttons = {
            'single': this.singleButtons(),
            'grouped': this.groupedButtons(),
        };

        // If we don't have any button with the 'always_show' at 'True',
        // we take the first one by default.
        if (!buttons.single.length && buttons.grouped.length) {
            buttons.single[0] = buttons.grouped[0];
            buttons.grouped.shift();
        }

        return buttons;
    }

    groupedButtons() {
        const buttons = [];

        for (const button of this.controller.buttons)
            if (!button.always_show)
                buttons.push(button);

        return buttons;
    }

    singleButtons() {
        const buttons = [];

        for (const button of this.controller.buttons)
            if (button.always_show)
                buttons.push(button);

        return buttons;
    }
}
