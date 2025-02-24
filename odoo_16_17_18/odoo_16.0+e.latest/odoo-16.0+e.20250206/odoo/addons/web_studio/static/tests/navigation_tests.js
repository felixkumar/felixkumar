/** @odoo-module **/
import {
    click,
    getFixture,
    legacyExtraNextTick,
    makeDeferred,
    nextTick,
    patchWithCleanup,
    triggerEvents,
} from "@web/../tests/helpers/utils";
import { registerCleanup } from "@web/../tests/helpers/cleanup";
import { contains } from "@web/../tests/utils";

import { toggleFilterMenu, toggleMenuItem } from "@web/../tests/search/helpers";
import { companyService } from "@web/webclient/company_service";
import { commandService } from "@web/core/commands/command_service";
import { createEnterpriseWebClient } from "@web_enterprise/../tests/helpers";
import { getActionManagerServerData } from "@web/../tests/webclient/helpers";
import { leaveStudio, openStudio, registerStudioDependencies } from "@web_studio/../tests/helpers";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { patch, unpatch } from "@web/core/utils/patch";
import { StudioView } from "@web_studio/client_action/studio_view";
import { StudioClientAction } from "@web_studio/client_action/studio_client_action";
import { ListEditorRenderer } from "@web_studio/client_action/view_editors/list/list_editor_renderer";

// -----------------------------------------------------------------------------
// Tests
// -----------------------------------------------------------------------------

let serverData;
let target;
QUnit.module("Studio", (hooks) => {
    hooks.beforeEach(() => {
        target = getFixture();
        serverData = getActionManagerServerData();
        registerStudioDependencies();
        const serviceRegistry = registry.category("services");
        serviceRegistry.add("company", companyService);

        // tweak a bit the default config to better fit with studio needs:
        //  - add some menu items we can click on to test the navigation
        //  - add a one2many field in a form view to test the one2many edition
        serverData.menus = {
            root: { id: "root", children: [1, 2, 3], name: "root", appID: "root" },
            1: {
                id: 1,
                children: [11, 12],
                name: "Partners",
                appID: 1,
                actionID: 4,
                xmlid: "app_1",
            },
            11: {
                id: 11,
                children: [],
                name: "Partners (Action 4)",
                appID: 1,
                actionID: 4,
                xmlid: "menu_11",
            },
            12: {
                id: 12,
                children: [],
                name: "Partners (Action 3)",
                appID: 1,
                actionID: 3,
                xmlid: "menu_12",
            },
            2: {
                id: 2,
                children: [],
                name: "Ponies",
                appID: 2,
                actionID: 8,
                xmlid: "app_2",
            },
            3: {
                id: 3,
                children: [],
                name: "Client Action",
                appID: 3,
                actionID: 9,
                xmlid: "app_3",
            },
        };
        serverData.models.partner.fields.date = { string: "Date", type: "date" };
        serverData.models.partner.fields.pony_id = {
            string: "Pony",
            type: "many2one",
            relation: "pony",
        };
        serverData.models.pony.fields.partner_ids = {
            string: "Partners",
            type: "one2many",
            relation: "partner",
            relation_field: "pony_id",
        };
        serverData.views["pony,false,form"] = `
            <form>
                <field name="name"/>
                <field name='partner_ids'>
                    <form>
                        <sheet>
                            <field name='display_name'/>
                        </sheet>
                    </form>
                </field>
            </form>`;
    });

    QUnit.module("Studio Navigation");

    QUnit.test("Studio not available for non system users", async function (assert) {
        assert.expect(2);

        patchWithCleanup(session, { is_system: false });
        await createEnterpriseWebClient({ serverData });
        assert.containsOnce(target, ".o_main_navbar");

        assert.containsNone(target, ".o_main_navbar .o_web_studio_navbar_item a");
    });

    QUnit.test("open Studio with act_window", async function (assert) {
        assert.expect(22);

        const mockRPC = async (route) => {
            assert.step(route);
        };
        await createEnterpriseWebClient({ serverData, mockRPC });
        assert.containsOnce(target, ".o_home_menu");

        // open app Partners (act window action)
        await click(target.querySelector(".o_app[data-menu-xmlid=app_1]"));
        await legacyExtraNextTick();

        assert.containsOnce(target, ".o_kanban_view");
        assert.verifySteps(
            [
                "/web/webclient/load_menus",
                "/web/action/load",
                "/web/dataset/call_kw/partner/get_views",
                "/web/dataset/call_kw/partner/web_search_read",
            ],
            "should have loaded the action"
        );
        assert.containsOnce(target, ".o_main_navbar .o_web_studio_navbar_item a");

        await openStudio(target);

        assert.verifySteps(
            [
                "/web_studio/activity_allowed",
                "/web_studio/get_studio_view_arch",
                "/web/dataset/call_kw/partner/get_views",
                "/web/dataset/call_kw/partner/web_search_read",
            ],
            "should have opened the action in Studio"
        );

        assert.containsOnce(
            target,
            ".o_web_studio_client_action .o_web_studio_kanban_view_editor",
            "the kanban view should be opened"
        );
        assert.containsOnce(
            target,
            ".o_kanban_record:contains(yop)",
            "the first partner should be displayed"
        );
        assert.containsOnce(target, ".o_studio_navbar .o_web_studio_leave a");

        await leaveStudio(target);

        assert.verifySteps(
            [
                "/web/action/load",
                "/web/dataset/call_kw/partner/get_views",
                "/web/dataset/call_kw/partner/web_search_read",
            ],
            "should have reloaded the previous action edited by Studio"
        );

        assert.containsNone(target, ".o_web_studio_client_action", "Studio should be closed");
        assert.containsOnce(
            target,
            ".o_kanban_view .o_kanban_record:contains(yop)",
            "the first partner should be displayed in kanban"
        );
    });

    QUnit.test("open Studio with act_window and viewType", async function (assert) {
        await createEnterpriseWebClient({ serverData });

        // open app Partners (act window action), sub menu Partners (action 3)
        await click(target.querySelector(".o_app[data-menu-xmlid=app_1]"));
        // the menu is rendered once the action is ready, so potentially in the next animation frame
        await nextTick();
        await click(target, ".o_menu_sections .o_nav_entry:nth-child(2)");
        assert.containsOnce(target, ".o_list_view");

        await click(target.querySelector(".o_data_row .o_data_cell")); // open a record
        assert.containsOnce(target, ".o_form_view");

        await openStudio(target);
        assert.containsOnce(
            target,
            ".o_web_studio_client_action .o_web_studio_form_view_editor",
            "the form view should be opened"
        );
        assert.strictEqual(
            $(target).find('.o_field_widget[name="foo"]').text(),
            "yop",
            "the first partner should be displayed"
        );
    });

    QUnit.test("reload the studio view", async function (assert) {
        assert.expect(5);

        const webClient = await createEnterpriseWebClient({ serverData });

        // open app Partners (act window action), sub menu Partners (action 3)
        await click(target.querySelector(".o_app[data-menu-xmlid=app_1]"));
        await legacyExtraNextTick();
        assert.strictEqual(
            $(target).find(".o_kanban_record:contains(yop)").length,
            1,
            "the first partner should be displayed"
        );

        await click(target.querySelector(".o_kanban_record")); // open a record
        await legacyExtraNextTick();
        assert.containsOnce(target, ".o_form_view");
        assert.strictEqual(
            $(target).find(".o_form_view input:propValue(yop)").length,
            1,
            "should have open the same record"
        );

        let prom = makeDeferred();
        patch(StudioView.prototype, "web_studio.Test.StudioView", {
            setup() {
                this._super();
                owl.onMounted(() => {
                    prom.resolve();
                });
            },
        });
        await openStudio(target);
        await prom;
        prom = makeDeferred();
        await webClient.env.services.studio.reload();
        await prom;
        unpatch(StudioView.prototype, "web_studio.Test.StudioView");

        assert.containsOnce(
            target,
            ".o_web_studio_client_action .o_web_studio_form_view_editor",
            "the studio view should be opened after reloading"
        );
        assert.strictEqual(
            $(target).find(".o_form_view span:contains(yop)").length,
            1,
            "should have open the same record"
        );
    });

    QUnit.test("switch view and close Studio", async function (assert) {
        assert.expect(6);

        await createEnterpriseWebClient({ serverData });
        // open app Partners (act window action)
        await click(target.querySelector(".o_app[data-menu-xmlid=app_1]"));
        await legacyExtraNextTick();
        assert.containsOnce(target, ".o_kanban_view");

        await openStudio(target);
        assert.containsOnce(target, ".o_web_studio_client_action .o_web_studio_kanban_view_editor");

        // click on tab "Views"
        await click(target.querySelector(".o_web_studio_menu .o_web_studio_menu_item a"));
        assert.containsOnce(target, ".o_web_studio_action_editor");

        // open list view
        await click(
            target.querySelector(
                ".o_web_studio_views .o_web_studio_view_type[data-type=list] .o_web_studio_thumbnail"
            )
        );
        await legacyExtraNextTick();

        assert.containsOnce(target, ".o_web_studio_client_action .o_web_studio_list_view_editor");

        await leaveStudio(target);

        assert.containsNone(target, ".o_web_studio_client_action", "Studio should be closed");
        assert.containsOnce(target, ".o_list_view", "the list view should be opened");
    });

    QUnit.test("navigation in Studio with act_window", async function (assert) {
        assert.expect(28);

        const mockRPC = async (route) => {
            assert.step(route);
        };

        await createEnterpriseWebClient({ serverData, mockRPC });
        // open app Partners (act window action)
        await click(target.querySelector(".o_app[data-menu-xmlid=app_1]"));
        await legacyExtraNextTick();

        assert.verifySteps(
            [
                "/web/webclient/load_menus",
                "/web/action/load",
                "/web/dataset/call_kw/partner/get_views",
                "/web/dataset/call_kw/partner/web_search_read",
            ],
            "should have loaded the action"
        );

        await openStudio(target);

        assert.verifySteps(
            [
                "/web_studio/activity_allowed",
                "/web_studio/get_studio_view_arch",
                "/web/dataset/call_kw/partner/get_views",
                "/web/dataset/call_kw/partner/web_search_read",
            ],
            "should have opened the action in Studio"
        );

        assert.containsOnce(
            target,
            ".o_web_studio_client_action .o_web_studio_kanban_view_editor",
            "the kanban view should be opened"
        );
        assert.strictEqual(
            $(target).find(".o_kanban_record:contains(yop)").length,
            1,
            "the first partner should be displayed"
        );

        await click(target.querySelector(".o_studio_navbar .o_menu_toggle"));

        assert.containsOnce(target, ".o_studio_home_menu");

        // open app Ponies (act window action)
        await click(target.querySelector(".o_app[data-menu-xmlid=app_2]"));
        await legacyExtraNextTick();

        assert.verifySteps(
            [
                "/web/action/load",
                "/web_studio/activity_allowed",
                "/web_studio/get_studio_view_arch",
                "/web/dataset/call_kw/pony/get_views",
                "/web/dataset/call_kw/pony/web_search_read",
            ],
            "should have opened the navigated action in Studio"
        );

        assert.containsOnce(
            target,
            ".o_web_studio_client_action .o_web_studio_list_view_editor",
            "the list view should be opened"
        );
        assert.strictEqual(
            $(target).find(".o_list_view .o_data_cell").text(),
            "Twilight SparkleApplejackFluttershy",
            "the list of ponies should be correctly displayed"
        );

        await leaveStudio(target);

        assert.verifySteps(
            [
                "/web/action/load",
                "/web/dataset/call_kw/pony/get_views",
                "/web/dataset/call_kw/pony/web_search_read",
            ],
            "should have reloaded the previous action edited by Studio"
        );

        assert.containsNone(target, ".o_web_studio_client_action", "Studio should be closed");
        assert.containsOnce(target, ".o_list_view", "the list view should be opened");
        assert.strictEqual(
            $(target).find(".o_list_view .o_data_cell").text(),
            "Twilight SparkleApplejackFluttershy",
            "the list of ponies should be correctly displayed"
        );
    });

    QUnit.test("keep action context when leaving Studio", async function (assert) {
        assert.expect(5);

        let nbLoadAction = 0;
        const mockRPC = async (route, args) => {
            if (route === "/web/action/load") {
                nbLoadAction++;
                if (nbLoadAction === 2) {
                    assert.strictEqual(
                        args.additional_context.active_id,
                        1,
                        "the context should be correctly passed when leaving Studio"
                    );
                }
            }
        };
        serverData.actions[4].context = "{'active_id': 1}";

        await createEnterpriseWebClient({
            serverData,
            mockRPC,
        });
        // open app Partners (act window action)
        await click(target.querySelector(".o_app[data-menu-xmlid=app_1]"));
        await legacyExtraNextTick();

        assert.containsOnce(target, ".o_kanban_view");

        await openStudio(target);

        assert.containsOnce(target, ".o_web_studio_kanban_view_editor");

        await leaveStudio(target);

        assert.containsOnce(target, ".o_kanban_view");
        assert.strictEqual(nbLoadAction, 2, "the action should have been loaded twice");
    });

    QUnit.test("user context is unpolluted when entering studio in error", async (assert) => {
        patchWithCleanup(StudioClientAction.prototype, {
            setup() {
                throw new Error("Boom");
            },
        });
        registry.category("services").add("error", { start() {} });

        const handler = (ev) => {
            assert.strictEqual(ev.reason.cause.message, "Boom");
            assert.step("error");
            ev.preventDefault();
        };
        window.addEventListener("unhandledrejection", handler);
        registerCleanup(() => window.removeEventListener("unhandledrejection", handler));

        const mockRPC = (route, args) => {
            if (route === "/web/dataset/call_kw/partner/get_views") {
                assert.step(`get_views, context studio: "${args.kwargs.context.studio}"`);
            }
        };
        await createEnterpriseWebClient({
            serverData,
            mockRPC,
        });
        // open app Partners (act window action)
        await click(target.querySelector(".o_app[data-menu-xmlid=app_1]"));
        await legacyExtraNextTick();
        assert.verifySteps([`get_views, context studio: "undefined"`]);

        assert.containsOnce(target, ".o_kanban_view");

        await openStudio(target);
        assert.verifySteps(["error"]);

        assert.containsNone(target, ".o_web_studio_kanban_view_editor");
        assert.containsOnce(target, ".o_kanban_view");

        await click(target.querySelector(".o_menu_sections a[data-menu-xmlid=menu_12]"));
        assert.containsOnce(target, ".o_list_view");
        assert.verifySteps([`get_views, context studio: "undefined"`]);
    });

    QUnit.test("error bubbles up if first rendering", async (assert) => {
        const _console = window.console;
        window.console = Object.assign(Object.create(_console), {
            warn(msg) {
                assert.step(msg);
            },
        });
        registerCleanup(() => {
            window.console = _console;
        });

        patchWithCleanup(ListEditorRenderer.prototype, {
            setup() {
                throw new Error("Boom");
            },
        });
        registry.category("services").add("error", { start() {} });

        const handler = (ev) => {
            assert.strictEqual(ev.reason.cause.cause.message, "Boom");
            assert.step("error");
            ev.preventDefault();
        };
        window.addEventListener("unhandledrejection", handler);
        registerCleanup(() => window.removeEventListener("unhandledrejection", handler));

        await createEnterpriseWebClient({
            serverData,
        });
        // open app Partners (act window action)
        await click(target.querySelector(".o_app[data-menu-xmlid=app_1]"));
        await nextTick();
        await click(target.querySelector(".o_menu_sections [data-menu-xmlid=menu_12]"));
        assert.containsOnce(target, ".o_list_view");

        await openStudio(target);
        assert.verifySteps([
            "[Owl] Unhandled error. Destroying the root component", // (legacy) owl_compatibility-specific
            "error",
        ]);
        // FIXME : due to https://github.com/odoo/owl/issues/1298,
        // the visual result is not asserted here, ideally we'd want to be in the studio
        // action, with a blank editor
    });

    QUnit.test("open same record when leaving form", async function (assert) {
        await createEnterpriseWebClient({ serverData });
        // open app Ponies (act window action)
        await click(target.querySelector(".o_app[data-menu-xmlid=app_2]"));
        assert.containsOnce(target, ".o_list_view");
        // Dont'pick the first record for testing
        await click(target.querySelectorAll(".o_data_row .o_data_cell")[1]);
        assert.strictEqual(
            target.querySelector(".o_form_view .o_field_widget[name=name] input").value,
            "Applejack"
        );
        assert.containsOnce(target, ".o_form_view");

        await openStudio(target);
        assert.strictEqual(
            target.querySelector(
                ".o_form_view .o_field_widget[data-studio-xpath='/form[1]/field[1]'] span"
            ).textContent,
            "Applejack"
        );
        assert.containsOnce(target, ".o_web_studio_client_action .o_web_studio_form_view_editor");

        await leaveStudio(target);
        assert.containsOnce(target, ".o_form_view");
        assert.containsOnce(target, ".o_form_view .o_field_widget[name=name] input");
        assert.strictEqual(
            target.querySelector(".o_form_view .o_field_widget[name=name] input").value,
            "Applejack"
        );
    });

    QUnit.test("open Studio with non editable view", async function (assert) {
        assert.expect(2);

        serverData.menus[99] = {
            id: 9,
            children: [],
            name: "Action with Grid view",
            appID: 9,
            actionID: 99,
            xmlid: "app_9",
        };
        serverData.menus.root.children.push(99);
        serverData.actions[99] = {
            id: 99,
            xml_id: "some.xml_id",
            name: "Partners Action 99",
            res_model: "partner",
            type: "ir.actions.act_window",
            views: [
                [42, "grid"],
                [2, "list"],
                [false, "form"],
            ],
        };
        serverData.views["partner,42,grid"] = `
            <grid>
                <field name="foo" type="row"/>
                <field name="id" type="measure"/>
                <field name="date" type="col">
                    <range name="week" string="Week" span="week" step="day"/>
                </field>
            </grid>`;

        await createEnterpriseWebClient({
            serverData,
            legacyParams: { withLegacyMockServer: true },
        });
        await click(target.querySelector(".o_app[data-menu-xmlid=app_9]"));
        await legacyExtraNextTick();

        assert.containsOnce(target, ".o_grid_view");

        await openStudio(target);

        assert.containsOnce(
            target,
            ".o_web_studio_action_editor",
            "action editor should be opened (grid is not editable)"
        );
    });

    QUnit.test(
        "open list view with sample data gives empty list view in studio",
        async function (assert) {
            assert.expect(2);

            serverData.models.pony.records = [];
            serverData.views["pony,false,list"] = `<tree sample="1"><field name="name"/></tree>`;

            await createEnterpriseWebClient({
                serverData,
            });
            // open app Ponies (act window action)
            await click(target.querySelector(".o_app[data-menu-xmlid=app_2]"));
            await legacyExtraNextTick();

            assert.ok(
                [...target.querySelectorAll(".o_list_table .o_data_row")].length > 0,
                "there should be some sample data in the list view"
            );

            await openStudio(target);
            await legacyExtraNextTick();

            assert.containsNone(
                target,
                ".o_list_table .o_data_row",
                "the list view should not contain any data"
            );
        }
    );

    QUnit.test("kanban in studio should always ignore sample data", async function (assert) {
        serverData.models.pony.fields.m2o = {
            string: "m2o",
            relation: "partner",
            type: "many2one",
        };

        serverData.actions[8].views = [[false, "kanban"]];
        serverData.models.pony.records = [];
        serverData.views["pony,false,kanban"] = `
                <kanban sample="1" default_group_by="m2o">
                    <t t-name="kanban-box">
                        <field name="name"/>
                        <field name="m2o" />
                    </t>
                </kanban>`;

        await createEnterpriseWebClient({
            serverData,
        });
        // open app Ponies (act window action)
        await click(target.querySelector(".o_app[data-menu-xmlid=app_2]"));
        await legacyExtraNextTick();

        assert.ok(
            [...target.querySelectorAll(".o_kanban_view .o_kanban_examples_ghost")].length > 0,
            "there should be some sample data in the kanban view"
        );

        await openStudio(target);
        await legacyExtraNextTick();

        assert.containsOnce(
            target,
            ".o_web_studio_kanban_view_editor .o_kanban_group .o_kanban_record:not(.o_kanban_ghost):not(.o_kanban_demo)",
            "the kanban view should not contain any sample data"
        );

        assert.containsNone(target, "o_web_studio_kanban_view_editor .o_view_nocontent");
    });

    QUnit.test("entering a kanban keeps the user's domain", async (assert) => {
        serverData.views["pony,false,kanban"] = `
            <kanban>
                <field name="display_name" />
                <templates>
                    <t t-name="kanban-box">
                        <field name="display_name" />
                    </t>
                </templates>
            </kanban>
        `;

        serverData.views["pony,58,search"] = `
            <search>
                <filter name="apple" string="apple" domain="[('name', 'ilike', 'Apple')]" />
            </search>
        `;

        serverData.menus[43] = {
            id: 43,
            children: [],
            name: "kanban",
            appID: 43,
            actionID: 43,
            xmlid: "app_43",
        };
        serverData.menus.root.children.push(43);
        serverData.actions[43] = {
            id: 43,
            name: "Pony Action 43",
            res_model: "pony",
            type: "ir.actions.act_window",
            views: [[false, "kanban"]],
            search_view_id: [58],
            xml_id: "action_43",
        };

        const mockRPC = async (route, args) => {
            if (args.method === "web_search_read") {
                assert.step(`${args.method}: ${JSON.stringify(args.kwargs)}`);
            }
        };

        await createEnterpriseWebClient({
            serverData,
            mockRPC,
        });
        assert.verifySteps([]);
        await click(target.querySelector(".o_app[data-menu-xmlid=app_43]"));
        assert.containsOnce(target, ".o_kanban_view");
        assert.verifySteps([
            `web_search_read: {"limit":40,"offset":0,"order":"","context":{"lang":"en","uid":7,"tz":"taht","allowed_company_ids":[1],"bin_size":true},"count_limit":10001,"domain":[],"fields":["display_name"]}`,
        ]);

        await toggleFilterMenu(target);
        await toggleMenuItem(target, "Apple");
        assert.verifySteps([
            `web_search_read: {"limit":40,"offset":0,"order":"","context":{"lang":"en","uid":7,"tz":"taht","allowed_company_ids":[1],"bin_size":true},"count_limit":10001,"domain":[["name","ilike","Apple"]],"fields":["display_name"]}`,
        ]);

        await openStudio(target);
        assert.containsOnce(target, ".o_web_studio_kanban_view_editor");
        assert.verifySteps([
            `web_search_read: {"limit":1,"offset":0,"order":"","context":{"lang":"en","uid":7,"tz":"taht","allowed_company_ids":[1],"studio":1,"bin_size":true},"count_limit":10001,"domain":[["name","ilike","Apple"]],"fields":["display_name"]}`,
        ]);
        assert.strictEqual(target.querySelector(".o_kanban_record").textContent, "Applejack");
    });

    QUnit.test(
        "open Studio with editable form view and check context propagation",
        async function (assert) {
            assert.expect(6);

            serverData.menus[43] = {
                id: 43,
                children: [],
                name: "Form with context",
                appID: 43,
                actionID: 43,
                xmlid: "app_43",
            };
            serverData.menus.root.children.push(43);
            serverData.actions[43] = {
                id: 43,
                name: "Pony Action 43",
                res_model: "pony",
                type: "ir.actions.act_window",
                views: [[false, "form"]],
                context: "{'default_type': 'foo'}",
                res_id: 4,
                xml_id: "action_43",
            };

            const mockRPC = async (route, args) => {
                if (route === "/web/dataset/call_kw/pony/read") {
                    // We pass here twice: once for the "classic" action
                    // and once when entering studio
                    assert.strictEqual(args.kwargs.context.default_type, "foo");
                }
                if (route === "/web/dataset/call_kw/partner/onchange") {
                    assert.ok(
                        !("default_type" in args.kwargs.context),
                        "'default_x' context value should not be propaged to x2m model"
                    );
                }
            };

            await createEnterpriseWebClient({
                serverData,
                mockRPC,
            });
            await click(target.querySelector(".o_app[data-menu-xmlid=app_43]"));
            await legacyExtraNextTick();

            assert.containsOnce(target, ".o_form_view");

            await openStudio(target);

            assert.containsOnce(
                target,
                ".o_web_studio_client_action .o_web_studio_form_view_editor",
                "the form view should be opened"
            );

            await click(target.querySelector(".o_web_studio_form_view_editor .o_field_one2many"));
            await click(
                target.querySelector(
                    '.o_web_studio_form_view_editor .o_field_one2many .o_web_studio_editX2Many[data-type="form"]'
                )
            );

            assert.containsOnce(
                target,
                ".o_web_studio_client_action .o_web_studio_form_view_editor",
                "the form view should be opened"
            );
        }
    );

    QUnit.test(
        "concurrency: execute a non editable action and try to enter studio",
        async function (assert) {
            // the purpose of this test is to ensure that there's no time window
            // during which if the icon isn't disabled, but the current action isn't
            // editable (typically, just after the current action has changed).
            assert.expect(5);

            const def = makeDeferred();
            serverData.actions[4].xml_id = false; // make action 4 non editable
            const webClient = await createEnterpriseWebClient({ serverData });
            assert.containsOnce(target, ".o_home_menu");

            webClient.env.bus.on("ACTION_MANAGER:UI-UPDATED", null, () => {
                assert.containsOnce(target, ".o_kanban_view");
                assert.hasClass(target.querySelector(".o_web_studio_navbar_item"), "o_disabled");
                def.resolve();
            });

            // open app Partners (non editable act window action)
            await click(target.querySelector(".o_app[data-menu-xmlid=app_1]"));
            await def;

            assert.containsOnce(target, ".o_kanban_view");
            assert.hasClass(target.querySelector(".o_web_studio_navbar_item"), "o_disabled");
        }
    );

    QUnit.test("command palette inside studio", async (assert) => {
        registry.category("services").add("command", commandService);
        await createEnterpriseWebClient({ serverData });
        await openStudio(target);

        // disable opacity: 0 in tests
        // doesn't have any effect on the test itself
        document.body.classList.add("debug");
        registerCleanup(() => document.body.classList.remove("debug"));
        target.classList.add("debug");

        assert.containsOnce(target, ".o_studio_home_menu");
        const hiddenInput = target.querySelector("input.o_search_hidden");
        hiddenInput.value = "Part";
        await triggerEvents(hiddenInput, null, ["input"]);
        assert.containsOnce(target, ".o_command_palette");

        await click(target.querySelector(".o_command_palette .o_command"));
        await nextTick();
        assert.containsNone(target, ".o_studio_home_menu");
        assert.containsOnce(target, ".o_studio .o_web_studio_kanban_view_editor");
    });

    QUnit.test("command palette inside studio with error", async (assert) => {
        serverData.menus.root.children.push(99);
        serverData.menus[99] = {
            id: 99,
            children: [],
            actionID: 99,
            xmlid: "testMenu",
            name: "On Error",
            appID: 99,
        };
        serverData.actions[99] = {
            id: 99,
            type: "ir.actions.act_window",
            res_model: "partner",
            views: [[false, "list"]],
            name: "test action",
            groups_id: [],
        };

        registry.category("services").add("command", commandService);
        await createEnterpriseWebClient({ serverData });
        await openStudio(target);

        // disable opacity: 0 in tests
        // doesn't have any effect on the test itself
        document.body.classList.add("debug");
        registerCleanup(() => document.body.classList.remove("debug"));
        target.classList.add("debug");

        assert.containsOnce(target, ".o_studio_home_menu");
        const hiddenInput = target.querySelector("input.o_search_hidden");
        hiddenInput.value = "On Error";

        await triggerEvents(hiddenInput, null, ["input"]);
        assert.containsOnce(target, ".o_command_palette");

        await click(target.querySelector(".o_command_palette .o_command"));
        await nextTick();
        assert.containsOnce(target, "div.o_notification[role=alert]");
    });

    QUnit.test("load with active_id active_ids", async (assert) => {
        const webClient = await createEnterpriseWebClient({
            serverData,
            mockRPC: (route, args) => {
                if (args.method === "get_views") {
                    assert.step("get_views");
                    assert.deepEqual(args.kwargs.context, {
                        active_id: 451,
                        active_ids: [451],
                        allowed_company_ids: [1],
                        lang: false,
                        no_address_format: true,
                        some_key: [451],
                        studio: true,
                        tz: "taht",
                        uid: 7,
                    });
                }
            },
        });
        serverData.actions[4].context = `{"some_key": active_ids}`;
        webClient.env.bus.trigger("test:hashchange", {
            action: "studio",
            mode: "editor",
            _action: "4",
            _view_type: "form",
            _tab: "views",
            active_id: 451,
        });
        await contains(".o_web_studio_view_renderer .o_form_view");
        assert.verifySteps(["get_views"]);
    });
});
