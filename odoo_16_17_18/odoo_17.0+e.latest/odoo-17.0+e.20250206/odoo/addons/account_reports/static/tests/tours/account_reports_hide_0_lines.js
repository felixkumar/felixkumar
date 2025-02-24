/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Asserts } from "./asserts";

registry.category("web_tour.tours").add('account_reports_hide_0_lines', {
    test: true,
    url: '/web?#action=account_reports.action_account_report_bs',
    steps: () => [
        {
            content: 'test if the Bank and Cash line is present (but the value is 0)',
            trigger: '.line_name:contains("Bank and Cash Accounts")',
        },
        {
            content: 'test if the Current Year Unallocated Earnings line is present (but the value is 0)',
            trigger: '.line_name:contains("Current Year Unallocated Earnings")',
        },
        {
            content: 'test if the Unallocated Earnings line is present (but value is different from 0 and so should be there after the hide_0_lines',
            trigger: '.line_name:contains("Unallocated Earnings")',
        },
        {
            content: "Open options selector",
            trigger: "#filter_extra_options button",
            run: 'click',
        },
        {
            content: "Select the hide line at 0 option",
            trigger: ".dropdown-item:contains('Hide lines at 0')",
            run: 'click',
        },
        {
            content: 'test if the Unallocated Earnings line is still present',
            trigger: '.line_name:contains("Unallocated Earnings")',
        },
        {
            content: 'test if the Bank and Cash line is not present',
            trigger: '.o_content',
            run: () => {
                const count = $(".d-none:contains('Bank and Cash Accounts')").length;
                Asserts.check(
                    count > 0,
                    "The Bank and Cash line is hidden.",
                    "The Bank and Cash line should be hidden by the Hide lines at 0 feature but it isn't."
                );
            },
        },
        {
            content: 'test if the Current Year Unallocated Earnings line is not present',
            trigger: '.o_content',
            run: () => {
                const count = $(".d-none:contains('Current Year Unallocated Earnings')").length;
                Asserts.check(
                    count > 0,
                    "The Current Year Unallocated Earnings line is hidden.",
                    "The Current Year Unallocated Earnings line should be hidden by the Hide lines at 0 feature but it isn't."
                );
            },
        },
        {
            content: "Click again to open the options selector",
            trigger: "#filter_extra_options button",
            run: 'click',
        },
        {
            content: "Select the hide lines at 0 option again",
            trigger: ".dropdown-item:contains('Hide lines at 0')",
            run: 'click',
        },
        {
            content: 'test again if the Bank and Cash line is present (but the value is 0)',
            trigger: '.line_name:contains("Bank and Cash Accounts")',
            run: () => null,
        },
    ]
});

registry.category("web_tour.tours").add('account_reports_hide_0_lines_with_string_columns', {
    test: true,
    url: '/web?#action=account_reports.action_account_report_general_ledger',
    steps: () => [
        {
            content: "test if the 211000 Account Payable line is present (but the value is 0)",
            trigger: ".name:contains('211000 Account Payable')",
            run: "click",
        },
        {
            content: "test if the MISC item line is present with string values set up, but all amounts are at 0",
            trigger: ".name:contains('Coucou les biloutes')",
        },
        {
            content: "Open options selector",
            trigger: "#filter_extra_options button",
            run: 'click',
        },
        {
            content: "Select the hide line at 0 option",
            trigger: ".dropdown-item:contains('Hide lines at 0')",
            run: 'click',
        },
        {
            content: "test if the MISC item line is hidden",
            trigger: ".o_content",
            run: () => {
                const count = $(".d-none:contains('Coucou les biloutes')").length;
                Asserts.check(
                    count > 0,
                    "The MISC item line is hidden.",
                    "The MISC item line should be hidden by the Hide lines at 0 feature but it isn't."
                );
            },
        },
        {
            content: "Click again to open the options selector",
            trigger: "#filter_extra_options button",
            run: 'click',
        },
        {
            content: "Select the hide lines at 0 option again",
            trigger: ".dropdown-item:contains('Hide lines at 0')",
            run: 'click',
        },
        {
            content: "Test again if the MISC item line is present (but the value is 0)",
            trigger: ".name:contains('Coucou les biloutes')",
            run: () => null,
        },
    ]
});
