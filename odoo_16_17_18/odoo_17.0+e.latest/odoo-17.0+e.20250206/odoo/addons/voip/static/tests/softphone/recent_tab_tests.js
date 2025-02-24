/* @odoo-module */

import { startServer } from "@bus/../tests/helpers/mock_python_environment";

import { start } from "@mail/../tests/helpers/test_utils";

import { click, contains, scroll } from "@web/../tests/utils";

QUnit.module("recent_tab");

QUnit.test("Scrolling to bottom loads more recent calls", async (assert) => {
    const pyEnv = await startServer();
    await start({
        async mockRPC(route, args, originalRPC) {
            if (args.method === "get_recent_phone_calls") {
                assert.step("get_recent_phone_calls");
            }
            return originalRPC(route, args);
        },
    });
    for (let i = 0; i < 10; ++i) {
        pyEnv["voip.call"].create({
            phone_number: "(501) 884-5252",
            state: "terminated",
            user_id: pyEnv.currentUserId,
        });
    }
    await click(".o_menu_systray button[title='Open Softphone']");
    await click(".nav-link", { text: "Recent" });
    await contains(".list-group-item-action", { count: 10 });
    for (let i = 0; i < 10; ++i) {
        pyEnv["voip.call"].create({
            phone_number: "07765 862268",
            state: "terminated",
            user_id: pyEnv.currentUserId,
        });
    }
    await contains(".list-group-item-action", { count: 10 });
    await scroll(".o-voip-RecentTab", "bottom");
    await contains(".list-group-item-action", { count: 20 });
    assert.verifySteps(["get_recent_phone_calls", "get_recent_phone_calls"]);
});
