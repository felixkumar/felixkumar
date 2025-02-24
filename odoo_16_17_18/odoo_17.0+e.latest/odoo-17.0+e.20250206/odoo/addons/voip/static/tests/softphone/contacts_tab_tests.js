/* @odoo-module */

import { startServer } from "@bus/../tests/helpers/mock_python_environment";

import { start } from "@mail/../tests/helpers/test_utils";

import { click, contains, insertText, scroll } from "@web/../tests/utils";

QUnit.module("contacts_tab");

QUnit.test("Partners with a phone number are displayed in Contacts tab", async () => {
    const pyEnv = await startServer();
    pyEnv["res.partner"].create([
        { display_name: "Michel Landline", phone: "+1-307-555-0120" },
        { display_name: "Maxim Mobile", mobile: "+257 114 7579" },
        { display_name: "Patrice Nomo" },
    ]);
    start();
    await click(".o_menu_systray button[title='Open Softphone']");
    await click(".nav-link", { text: "Contacts" });
    await contains(".o-voip-ContactsTab .list-group-item-action", { count: 2 });
    await contains(".o-voip-ContactsTab b", { text: "Michel Landline" });
    await contains(".o-voip-ContactsTab b", { text: "Maxim Mobile" });
    await contains(".o-voip-ContactsTab b", { text: "Patrice Nomo", count: 0 });
});

QUnit.test("Typing in the search bar fetches and displays the matching contacts", async () => {
    const pyEnv = await startServer();
    start();
    await click(".o_menu_systray button[title='Open Softphone']");
    await click(".nav-link", { text: "Contacts" });
    pyEnv["res.partner"].create([
        { display_name: "Morshu RTX", phone: "+61-855-527-77" },
        { display_name: "Gargamel", mobile: "+61-855-583-671" },
    ]);
    await insertText("input[placeholder=Search]", "Morshu");
    await contains(".o-voip-ContactsTab b", { text: "Morshu RTX" });
    await contains(".o-voip-ContactsTab b", { text: "Gargamel", count: 0 });
});

QUnit.test("Scrolling to bottom loads more contacts", async (assert) => {
    const pyEnv = await startServer();
    await start({
        async mockRPC(route, args, originalRPC) {
            if (args.method === "get_contacts") {
                assert.step("get_contacts");
            }
            return originalRPC(route, args);
        },
    });
    for (let i = 0; i < 10; ++i) {
        pyEnv["res.partner"].create({ name: `Contact ${i}`, phone: `09225 982 ext. ${i}` });
    }
    await click(".o_menu_systray button[title='Open Softphone']");
    await click(".nav-link", { text: "Contacts" });
    await contains(".o-voip-ContactsTab b", { count: 10 });
    for (let i = 0; i < 10; ++i) {
        pyEnv["res.partner"].create({ name: `Contact ${i + 10}`, phone: `040 2805 ext. ${i}` });
    }
    await contains(".o-voip-ContactsTab b", { count: 10 });
    await scroll(".o-voip-ContactsTab", "bottom");
    await contains(".o-voip-ContactsTab b", { count: 20 });
    assert.verifySteps(["get_contacts", "get_contacts"]);
});
