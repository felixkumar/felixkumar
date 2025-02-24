/** @odoo-module */

export function settleButtonTextIs(name) {
    return [
        {
            content: "check the content of the settle button",
            trigger: `.button.settle-due:contains(${name})`,
            run: () => {},
        },
    ];
}
