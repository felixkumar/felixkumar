/** @odoo-module **/

import { markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

import '@hr_payroll/js/tours/hr_payroll';

patch(registry.category("web_tour.tours").get("payroll_tours"), {
    steps() {
        const originalSteps = super.steps();
        const payrollStartStepIndex = originalSteps.findIndex((step) => step.id === "hr_payroll_start");
        originalSteps.splice(payrollStartStepIndex + 1, 0, {
            trigger: 'a.nav-link:contains(Contract Details)',
            content: markup(_t('Click on <strong>Contract Details</strong> to access contract information.')),
            position: 'bottom',
        },
        {
            trigger: `.o_notebook div[name='hr_responsible_id'] input`,
            content: markup(_t('Select an <strong>HR Responsible</strong> for the contract.')),
            position: 'bottom',
            run: 'click',
        },
        {
            trigger: ".ui-autocomplete > li > a:not(:has(i.fa))",
            auto: true,
        },
    );
        return originalSteps;
    }
});
