/* @odoo-module */

export const stepUtils = {
    enterPIN(code) {
        const steps = [];
        for (const c of code) {
            steps.push({ trigger: `.popup-numpad button:contains(${c})` });
        }
        steps.push({
            extra_trigger: `.popup-input:contains('${''.padEnd(code.length, "•")}')`,
            trigger: "footer .btn-primary",
            in_modal: true,
            run: 'click',
        });
        return steps;
    }
};
