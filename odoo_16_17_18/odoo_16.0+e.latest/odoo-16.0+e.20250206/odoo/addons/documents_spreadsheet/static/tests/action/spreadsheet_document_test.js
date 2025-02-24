/** @odoo-module */
import spreadsheet from "@spreadsheet/o_spreadsheet/o_spreadsheet_extended";
import { doMenuAction } from "@spreadsheet/../tests/utils/ui";
import { createSpreadsheet } from "../spreadsheet_test_utils";
import { patchWithCleanup } from "@web/../tests/helpers/utils";
import { downloadFile } from "@web/core/network/download";
import { getCellValue } from "@spreadsheet/../tests/utils/getters";
import { getBasicServerData } from "@spreadsheet/../tests/utils/data";

const { topbarMenuRegistry } = spreadsheet.registries;
const { Model } = spreadsheet;
/** @typedef {import("@spreadsheet/o_spreadsheet/o_spreadsheet").Model} Model */

QUnit.module("spreadsheet_edition > spreadsheet component", {}, () => {
    QUnit.test("menu > download as json", async function (assert) {
        assert.expect(6);

        let downloadedData = null;
        patchWithCleanup(downloadFile, {
            _download: (data) => {
                assert.step("download");
                assert.ok(data.includes("Hello World"));
                assert.ok(data.includes("A3"));
                downloadedData = data;
            },
        });

        const serverData = getBasicServerData();
        const spreadsheet = serverData.models["documents.document"].records[1];
        spreadsheet.raw = JSON.stringify({
            sheets: [{ cells: { A3: { content: "Hello World" } } }],
        });

        const { env, model } = await createSpreadsheet({
            spreadsheetId: spreadsheet.id,
            serverData,
        });

        assert.strictEqual(getCellValue(model, "A3"), "Hello World");

        await doMenuAction(topbarMenuRegistry, ["file", "download_as_json"], env);
        assert.verifySteps(["download"]);

        const modelFromLoadedJSON = new Model(JSON.parse(downloadedData));
        assert.strictEqual(getCellValue(modelFromLoadedJSON, "A3"), "Hello World");
    });
});
