/** @odoo-module */

import { Component, useState, xml } from "@odoo/owl";
import { Domain } from "@web/core/domain";
import { click, editInput, getFixture, mount, nextTick, patchDate, patchWithCleanup, selectDropdownItem } from "@web/../tests/helpers/utils";
import { makeTestEnv } from "@web/../tests/helpers/mock_env";
import { makeView, setupViewRegistries } from "@web/../tests/views/helpers";
import { PlanningGanttRenderer } from "@planning/views/planning_gantt/planning_gantt_renderer";
import { View } from "@web/views/view";
import { clickCell, getCell, getPill, getTexts, hoverGridCell } from "@web_gantt/../tests/helpers";


let serverData;
let target;
QUnit.module('SalePlanning > Views > GanttView', {
    async beforeEach() {
        patchDate(2021, 9, 10, 8, 0, 0);
        setupViewRegistries();
        target = getFixture();
        serverData = {
            models: {
                'planning.slot': {
                    fields: {
                        id: { string: 'ID', type: 'integer' },
                        name: { string: 'Name', type: 'char' },
                        role_id: { string: 'Role', type: 'many2one', relation: 'planning.role' },
                        sale_line_id: { string: 'Sale Order Item', type: 'many2one', relation: 'sale.order.line' },
                        resource_id: { string: 'Resource', type: 'many2one', relation: 'resource.resource' },
                        start_datetime: { string: 'Start Datetime', type: 'datetime' },
                        end_datetime: { string: 'End Datetime', type: 'datetime' },
                        allocated_percentage: { string: "Allocated percentage", type: "float" },
                    },
                    records: [
                        {
                            id: 1,
                            name: 'Shift 1',
                            role_id: 1,
                            sale_line_id: 1,
                            resource_id: false,
                            start_datetime: '2021-10-12 08:00:00',
                            end_datetime: '2021-10-12 12:00:00',
                            allocated_percentage: 0.5,
                        },
                    ],
                },
                'planning.role': {
                    fields: {
                        id: { string: 'ID', type: 'integer' },
                        name: { string: 'Name', type: 'char' },
                    },
                    records: [
                        { 'id': 1, name: 'Developer' },
                        { 'id': 2, name: 'Support Tech' },
                    ],
                },
                'sale.order.line': {
                    fields: {
                        id: { string: 'ID', type: 'integer' },
                        name: { string: 'Product Name', type: 'char' },
                    },
                    records: [
                        { id: 1, name: 'Computer Configuration' },
                    ],
                },
                'resource.resource': {
                    fields: {
                        id: { string: 'ID', type: 'integer' },
                        name: { string: 'Name', type: 'char' },
                    },
                    records: [
                        { 'id': 1, name: 'Chaganlal' },
                        { 'id': 2, name: 'Jarvo' },
                    ],
                },
            },
        };
    }
});

QUnit.test('Process domain for plan dialog', async function (assert) {
    let renderer;
    patchWithCleanup(PlanningGanttRenderer.prototype, {
        setup() {
            super.setup(...arguments);
            renderer = this;
        }
    });

    const env = await makeTestEnv({
        serverData,
        async mockRPC(_, args) {
            if (args.method === "gantt_resource_work_interval") {
                return  [
                    { false: [["2021-10-12 08:00:00", "2022-10-12 12:00:00"]] },
                ];
            }
        },
    });

    class Parent extends Component {
        setup() {
            this.state = useState({
                arch: `<gantt js_class="planning_gantt" date_start="start_datetime" date_stop="end_datetime" default_scale="week"/>`,
                resModel: 'planning.slot',
                type: "gantt",
                domain: [['start_datetime', '!=', false], ['end_datetime', '!=', false]],
                fields: serverData.models['planning.slot'].fields,
            });
        }
    }
    Parent.template = xml`<View t-props="state"/>`;
    Parent.components = { View };

    const parent = await mount(Parent, target, { env });

    let expectedDomain = Domain.and([
        Domain.and([
            new Domain(['&', ...Domain.TRUE.toList({}), ...Domain.TRUE.toList({})]),
            ['|', ['start_datetime', '=', false], ['end_datetime', '=', false]],
        ]),
        [['sale_line_id', '!=', false]],
    ]);
    assert.deepEqual(
        renderer.getPlanDialogDomain(),
        expectedDomain.toList()
    );

    parent.state.domain = ['|', ['role_id', '=', false], '&', ['resource_id', '!=', false], ['start_datetime', '=', false]];
    await nextTick();

    expectedDomain = Domain.and([
        Domain.and([
            new Domain([
                '|', ['role_id', '=', false],
                    '&', ['resource_id', '!=', false], ...Domain.TRUE.toList({}),
            ]),
            ['|', ['start_datetime', '=', false], ['end_datetime', '=', false]],
        ]),
        [['sale_line_id', '!=', false]],
    ]);
    assert.deepEqual(
        renderer.getPlanDialogDomain(),
        expectedDomain.toList()
    );

    parent.state.domain = ['|', ['start_datetime', '=', false], ['end_datetime', '=', false]];
    await nextTick();

    expectedDomain = Domain.and([
        Domain.and([
            Domain.TRUE,
            ['|', ['start_datetime', '=', false], ['end_datetime', '=', false]],
        ]),
        [['sale_line_id', '!=', false]],
    ]);
    assert.deepEqual(
        renderer.getPlanDialogDomain(),
        expectedDomain.toList()
    );
});

QUnit.test("Show shift form dialog only when shifts to plan", async function (assert) {
    assert.expect(3);

    // Additionally to 'Shift 1', we create a new unplanned shift 'Shift 2' which has a sale_line_id, no start_datetime and no end_datetime values
    serverData.models["planning.slot"].records = [serverData.models["planning.slot"].records[0], { name: "Shift 2", id: 2, role_id: 1, sale_line_id: 1 }]
    serverData.views = {
        "planning.slot,false,form": `<form js_class="planning_form"><field name="name"/></form>`,
        "planning.slot,false,list": `<tree><field name="name"/></tree>`,
    };

    await makeView({
        type: "gantt",
        resModel: "planning.slot",
        serverData,
        arch: `<gantt js_class="planning_gantt" date_start="start_datetime" date_stop="end_datetime" default_scale="week"/>`,
        mockRPC(_, args) {
            if (args.method === "gantt_resource_work_interval") {
                return  [
                    { false: [["2021-10-12 08:00:00", "2022-10-12 12:00:00"]] },
                ];
            }
        },
    });

    // First, we click on a cell and check that the shift form dialog opens up with the shifts to plan (as 'Shift 2' is a shift to plan)
    await hoverGridCell(1, 4);
    await clickCell(1, 4);
    assert.strictEqual(target.querySelector(".modal-title").textContent, "Plan");
    assert.strictEqual(target.querySelector(".o_data_cell").textContent, "Shift 2");

    // We then plan 'Shift 2'
    await click(target, ".o_data_cell");

    // There should be no more shifts to plan. So when we click again on the cell, only the create form view of shifts should open up
    await hoverGridCell(1, 4);
    await clickCell(1, 4);
    assert.strictEqual(target.querySelector(".modal-title").textContent, "Add Shift");
});

QUnit.test("Open a dialog to schedule a plan using Open Shift", async (assert) => {
    serverData.models['planning.slot'].records = [
        { id: 2, sale_line_id: 1 },
    ];

    serverData.views = {
        "planning.slot,false,list": `
            <tree>
                <field name="sale_line_id"/>
            </tree>`,
        "planning.slot,false,form": `
            <form>
                <field name="resource_id"/>
                <field name="start_datetime"/>
                <field name="end_datetime"/>
                <field name="name"/>
            </form>`,
    };

    await makeView({
        arch: '<gantt js_class="planning_gantt" date_start="start_datetime" date_stop="end_datetime" default_scale="week"/>',
        resModel: "planning.slot",
        type: "gantt",
        serverData,
        async mockRPC(_, args) {
            if (args.method === "gantt_resource_work_interval") {
                return [];
            }
        },
        groupBy: ["resource_id"],
    });

    await hoverGridCell(1, 1);
    await clickCell(1, 1);
    await click(target, ".modal-footer .o_create_button");

    await selectDropdownItem(target, "resource_id", "Jarvo");
    await editInput(target, ".o_field_widget[name='name'] input", 'Shift');
    await editInput(target, ".o_field_widget[name='start_datetime'] input", '2021-10-12 09:00:00');
    await editInput(target, ".o_field_widget[name='end_datetime'] input", '2021-10-12 12:00:00');

    await click(target, ".o_form_button_save");

    const cell = getCell(2, 3);
    assert.hasAttrValue(cell, "data-row-id", '[{"resource_id":[2,"Jarvo"]}]');

    const shiftPill = getPill("Shift");
    await click(shiftPill);
    assert.deepEqual(getTexts(".o_popover .popover-body span"), [
        "Shift",
        "10/12/2021, 9:00 AM",
        "10/12/2021, 12:00 PM",
    ]);
});
