/** @odoo-module **/

import { createWebClient, doAction } from "@web/../tests/webclient/helpers";
import { click, getFixture,} from "@web/../tests/helpers/utils";

const getOptionMockResponse = {
    "companies": [],
    "variants_source_id": 14,
    "has_inactive_variants": false,
    "available_variants": [],
    "selected_variant_id": 14,
    "sections_source_id": 14,
    "sections": [],
    "has_inactive_sections": false,
    "report_id": 14,
    "allow_domestic": false,
    "fiscal_position": "all",
    "available_vat_fiscal_positions": [],
    "date": {},
    "available_horizontal_groups": [],
    "selected_horizontal_group_id": null,
    "account_type": [],
    "all_entries": false,
    "aml_ir_filters": [],
    "buttons": [],
    "export_mode": null,
    "hide_0_lines": false,
    "multi_currency": false,
    "partner": false,
    "partner_categories": [],
    "selected_partner_ids": [],
    "partner_ids": [],
    "selected_partner_categories": [],
    "unreconciled": false,
    "rounding_unit": "decimals",
    "rounding_unit_names": {},
    "search_bar": false,
    "unfold_all": false,
    "unfolded_lines": [],
    "column_headers": [],
    "columns": [
        {
            "name": "A column",
            "column_group_key": "some_key",
            "expression_label": "a_column",
            "sortable": false,
            "figure_type": "string",
            "blank_if_zero": false,
            "style": ""
        },
    ],
    "column_groups": {"some_key": {"forced_options": {}, "forced_domain": []}
    },
}

const getReportInformationMockResponse = {
    "caret_options": {},
    "column_headers_render_data": {"level_colspan": [1], "level_repetitions": [1], "custom_subheaders": []},
    "column_groups_totals": {"some_key": {}},
    "context": {},
    "custom_display": {},
    "filters": {},
    "footnotes": {},
    "groups": {},
    "lines": [
        {
            "id": "~account.report~14|~res.partner~1",
            "name": "A partner",
            "columns": [
                {
                    "auditable": false,
                    "blank_if_zero": false,
                    "column_group_key": "some_key",
                    "currency": null,
                    "currency_symbol": "",
                    "digits": 1,
                    "expression_label": "a_column",
                    "figure_type": "string",
                    "green_on_positive": false,
                    "has_sublines": false,
                    "is_zero": false,
                    "name": "",
                    "no_format": null,
                    "report_line_id": null,
                    "sortable": false
                },
            ],
            "level": 1,
            "trust": "normal",
            "unfoldable": true,
            "unfolded": false,
            "expand_function": "some_expand_function"
        },
    ],
    "warnings": {},
    "report": { "company_name": "YourCompany", "company_country_code": "US", "company_currency_symbol": "$", "name": "A report", "root_report_id": "account.report()"}
}

const getExpandedLinesMockResponse = [
    {
        "id": "~account.report~14|~res.partner~1|0~account.move.line~1",
        "parent_id": "~account.report~14|~res.partner~1",
        "name": "first move line",
        "columns": [
            {
                "auditable": false,
                "blank_if_zero": false,
                "column_group_key": "some_key",
                "currency": null,
                "currency_symbol": "$",
                "digits": 1,
                "expression_label": "a_column",
                "figure_type": "string",
                "green_on_positive": false,
                "has_sublines": false,
                "is_zero": false,
                "name": "first value",
                "no_format": "first value",
                "report_line_id": null,
                "sortable": false
            },
        ],
        "level": 3
    },
    {
        "id": "~account.report~14|~res.partner~1|0~account.move.line~11",
        "parent_id": "~account.report~14|~res.partner~1",
        "name": "second move line",
        "columns": [
            {
                "auditable": false,
                "blank_if_zero": false,
                "column_group_key": "some_key",
                "currency": null,
                "currency_symbol": "$",
                "digits": 1,
                "expression_label": "a_column",
                "figure_type": "string",
                "green_on_positive": false,
                "has_sublines": false,
                "is_zero": false,
                "name": "second value",
                "no_format": "second value",
                "report_line_id": null,
                "sortable": false
            },
        ],
        "level": 3
    },
]

QUnit.module("Account Reports", (hooks) => {
    let target;

    hooks.beforeEach(async() => {
        target = getFixture();
    })

    QUnit.test("Test unfold loaded line", async function (assert) {
        async function mockRpcReport(route, args) {
            if (args.method == 'get_options') {
                return getOptionMockResponse;
            }
            if (args.method == 'get_report_information') {
                return getReportInformationMockResponse;
            }
            if (args.method == 'get_expanded_lines') {
                mockRpcReport.getExpandedLineCallCount = (mockRpcReport.getExpandedLineCallCount || 0) + 1;
                return getExpandedLinesMockResponse;
            }
        }
        const webClient = await createWebClient({
            serverData: { },
            mockRPC: mockRpcReport,
        });
        await doAction(webClient, {
            type: "ir.actions.client",
            tag: "account_report",
            params: {},
        });

        await click(target.querySelector('.btn_foldable'));
        await click(target.querySelector('.btn_foldable'));
        await click(target.querySelector('.btn_foldable'));

        // Only one call to get_expanded_lines, as we unfolded/folded/unfolded the same line
        assert.strictEqual(1, mockRpcReport.getExpandedLineCallCount);

        //Only one line marked as unfolded
        assert.strictEqual(1, target.querySelectorAll('.unfolded').length);
    });
});
