/** @odoo-module */

import { registry } from "@web/core/registry";
import { RPCError } from "@web/core/network/rpc_service";

export function mockJoinSpreadsheetSession(resModel) {
    return function (route, args) {
        const [id] = args.args;
        const record = this.models[resModel].records.find((record) => record.id === id);
        if (!record) {
            const error = new RPCError(`Spreadsheet ${id} does not exist`);
            error.data = {};
            throw error;
        }
        return {
            raw: record.raw,
            name: record.name,
            is_favorited: record.is_favorited,
            revisions: [],
            isReadonly: false,
        };
    };
}

registry
    .category("mock_server")
    .add("documents.document/get_spreadsheets_to_display", function () {
        return this.models["documents.document"].records
            .filter((document) => document.handler === "spreadsheet")
            .map((spreadsheet) => ({
                name: spreadsheet.name,
                id: spreadsheet.id,
            }));
    })
    .add(
        "documents.document/join_spreadsheet_session",
        mockJoinSpreadsheetSession("documents.document")
    )
    .add("documents.document/dispatch_spreadsheet_message", () => false)
    .add("spreadsheet.template/fetch_template_data", function (route, args) {
        const [id] = args.args;
        const record = this.models["spreadsheet.template"].records.find(
            (record) => record.id === id
        );
        if (!record) {
            const error = new RPCError(`Spreadsheet Template ${id} does not exist`);
            error.data = {};
            throw error;
        }
        return {
            data: record.data,
            name: record.name,
            isReadonly: false,
        };
    });
