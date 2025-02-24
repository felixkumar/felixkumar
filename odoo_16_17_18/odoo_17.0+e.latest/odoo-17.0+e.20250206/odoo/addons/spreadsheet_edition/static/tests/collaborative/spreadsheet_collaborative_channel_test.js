/** @odoo-module */

import { registry } from "@web/core/registry";
import { ormService } from "@web/core/orm_service";
import { nextTick } from "@web/../tests/helpers/utils";
import { makeTestEnv } from "@web/../tests/helpers/mock_env";

import { SpreadsheetCollaborativeChannel } from "@spreadsheet_edition/bundle/o_spreadsheet/collaborative/spreadsheet_collaborative_channel";

import { EventBus } from "@odoo/owl";

class MockBusService {
    constructor() {
        this.channels = [];
        this._bus = new EventBus();
    }

    start() {}

    addChannel(name) {
        this.channels.push(name);
    }

    addEventListener(eventName, handler) {
        this._bus.addEventListener("notif", handler);
    }

    notify(message) {
        this._bus.trigger("notif", [message]);
    }
}

function setupEnvWithMockBus() {
    const busService = new MockBusService();
    const rpc = function (route, params) {
        // Mock the server behavior: new revisions are pushed in the bus
        if (params.method === "dispatch_spreadsheet_message") {
            const [documentId, message] = params.args;
            busService.notify({ type: "spreadsheet", payload: { id: documentId, ...message } });
            return true;
        }
    };
    registry.category("services").add("orm", ormService);
    registry.category("services").add("bus_service", {
        start: () => busService,
    });
    return makeTestEnv({ mockRPC: rpc });
}

QUnit.module("spreadsheet_edition > SpreadsheetCollaborativeChannel");

QUnit.test("sending a message forward it to the registered listener", async function (assert) {
    const env = await setupEnvWithMockBus();
    const channel = new SpreadsheetCollaborativeChannel(env, "my.model", 5);
    channel.onNewMessage("anId", (message) => {
        assert.step("message");
        assert.strictEqual(message.greeting, "hello", "It should have the correct message content");
    });
    channel.sendMessage({ greeting: "hello" });
    await nextTick();
    assert.verifySteps(["message", "message"], "It should have received the message");
});

QUnit.test("previous messages are forwarded when registering a listener", async function (assert) {
    const env = await setupEnvWithMockBus();
    const channel = new SpreadsheetCollaborativeChannel(env, "my.model", 5);
    channel.sendMessage({ greeting: "hello" });
    channel.onNewMessage("anId", (message) => {
        assert.step("message");
        assert.strictEqual(message.greeting, "hello", "It should have the correct message content");
    });
    await nextTick();
    assert.verifySteps(["message", "message"], "It should have received the pending message");
});

QUnit.test("the channel does not care about other bus messages", async function (assert) {
    assert.expect(1);
    const env = await setupEnvWithMockBus();
    const channel = new SpreadsheetCollaborativeChannel(env, "my.model", 5);
    channel.onNewMessage("anId", () => assert.step("message"));
    env.services.bus_service.notify("a-random-channel", "a-random-message");
    await nextTick();
    assert.verifySteps([], "The message should not have been received");
});

QUnit.test("Message accepted by the server is immediately handled", async function (assert) {
    const busService = new MockBusService();
    const rpc = async function (route, params) {
        // Mock the server to accept the revision
        if (params.method === "dispatch_spreadsheet_message") {
            return true;
        }
    };
    registry.category("services").add("bus_service", {
        start: () => busService,
    });
    const env = await makeTestEnv({ mockRPC: rpc });
    const channel = new SpreadsheetCollaborativeChannel(env, "my.model", 5);
    channel.onNewMessage("anId", (message) => {
        assert.step("message");
        assert.strictEqual(message.greeting, "hello", "It should have the correct message content");
    });
    channel.sendMessage({ greeting: "hello" });
    await nextTick();
    assert.verifySteps(["message"], "It should have handle the accepted message");
});

QUnit.test("Message refused by the server is not immediately handled", async function (assert) {
    const busService = new MockBusService();
    const rpc = async function (route, params) {
        // Mock the server to refuse the revision
        if (params.method === "dispatch_spreadsheet_message") {
            return false;
        }
    };
    registry.category("services").add("bus_service", {
        start: () => busService,
    });
    const env = await makeTestEnv({ mockRPC: rpc });
    const channel = new SpreadsheetCollaborativeChannel(env, "my.model", 5);
    channel.onNewMessage("anId", (message) => {
        assert.step("message");
    });
    channel.sendMessage({ greeting: "hello" });
    await nextTick();
    assert.verifySteps([], "It should not have handle the refused message");
});
