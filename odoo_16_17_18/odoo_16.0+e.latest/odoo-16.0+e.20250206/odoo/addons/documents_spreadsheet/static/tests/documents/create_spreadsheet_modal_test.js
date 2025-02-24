/** @odoo-module */

import { createDocumentsView } from "@documents/../tests/documents_test_utils";

import { startServer } from "@mail/../tests/helpers/test_utils";

import {
    editInput,
    triggerEvent,
    getFixture,
    click,
    patchWithCleanup,
    nextTick,
} from "@web/../tests/helpers/utils";
import { getBasicData } from "@spreadsheet/../tests/utils/data";

import { mockActionService } from "@documents_spreadsheet/../tests/spreadsheet_test_utils";
import { setupViewRegistries } from "@web/../tests/views/helpers";
import { registry } from "@web/core/registry";
import { fileUploadService } from "@web/core/file_upload/file_upload_service";
import { DocumentsKanbanRenderer } from "@documents/views/kanban/documents_kanban_renderer";

const serviceRegistry = registry.category("services");

const TEST_TEMPLATES = [
    { id: 3, name: "Template 3", data: btoa("{}") },
    { id: 4, name: "Template 4", data: btoa("{}") },
    { id: 5, name: "Template 5", data: btoa("{}") },
    { id: 6, name: "Template 6", data: btoa("{}") },
    { id: 7, name: "Template 7", data: btoa("{}") },
    { id: 8, name: "Template 8", data: btoa("{}") },
    { id: 9, name: "Template 9", data: btoa("{}") },
    { id: 10, name: "Template 10", data: btoa("{}") },
    { id: 11, name: "Template 11", data: btoa("{}") },
    { id: 12, name: "Template 12", data: btoa("{}") },
];

async function getDocumentBasicData(views = {}) {
    const pyEnv = await startServer();
    const documentsFolderId1 = pyEnv["documents.folder"].create({
        name: "Workspace1",
        description: "Workspace",
        has_write_access: true,
    });
    const mailAliasId1 = pyEnv["mail.alias"].create({ alias_name: "hazard@rmcf.es" });
    pyEnv["documents.share"].create({
        name: "Share1",
        folder_id: documentsFolderId1,
        alias_id: mailAliasId1,
    });
    pyEnv["spreadsheet.template"].create([
        { name: "Template 1", data: btoa("{}") },
        { name: "Template 2", data: btoa("{}") },
    ]);
    return {
        models: {
            ...getBasicData(),
            ...pyEnv.getData(),
        },
        views,
    };
}

/**
 * @typedef InitArgs
 * @property {Object} serverData
 * @property {Array} additionalTemplates
 * @property {Function} mockRPC label of the filter
 */

/**
 *  @param {InitArgs} args
 */
async function initTestEnvWithKanban(args = {}) {
    const data =
        args.serverData ||
        (await getDocumentBasicData({
            "spreadsheet.template,false,search": `<search><field name="name"/></search>`,
        }));
    data.models["spreadsheet.template"].records = data.models[
        "spreadsheet.template"
    ].records.concat(args.additionalTemplates || []);

    return await createDocumentsView({
        type: "kanban",
        resModel: "documents.document",
        serverData: data,
        arch: /*xml*/ `
            <kanban js_class="documents_kanban"><templates><t t-name="kanban-box">
                <div><field name="name"/></div>
            </t></templates></kanban>
        `,
        mockRPC: args.mockRPC || (() => {}),
    });
}

async function initTestEnvWithBlankSpreadsheet() {
    const pyEnv = await startServer();
    const documentsFolderId1 = pyEnv["documents.folder"].create({ has_write_access: true });
    pyEnv["documents.document"].create({
        name: "My spreadsheet",
        raw: "{}",
        is_favorited: false,
        folder_id: documentsFolderId1,
        handler: "spreadsheet",
    });
    const serverData = {
        models: pyEnv.getData(),
        views: {
            "spreadsheet.template,false,search": `<search><field name="name"/></search>`,
        },
    };
    return await initTestEnvWithKanban({ serverData });
}

let target;

QUnit.module(
    "documents_spreadsheet > create spreadsheet from template modal",
    {
        beforeEach() {
            setupViewRegistries();
            target = getFixture();
            serviceRegistry.add("file_upload", fileUploadService);
            serviceRegistry.add("documents_pdf_thumbnail", {
                start() {
                    return {
                        enqueueRecords: () => {},
                    };
                },
            });
            // Historically the inspector had the preview on the kanban, due to it being
            // controlled with a props we simply force the kanban view to also have it during the tests
            // to ensure that the functionality stays the same, while keeping the tests as is.
            patchWithCleanup(DocumentsKanbanRenderer.prototype, {
                getDocumentsInspectorProps() {
                    const result = this._super(...arguments);
                    result.withFilePreview = true;
                    return result;
                },
            });
        },
    },
    () => {
        QUnit.test("Create spreadsheet from kanban view opens a modal", async function (assert) {
            await initTestEnvWithKanban();
            await click(target, ".o_documents_kanban_spreadsheet");
            assert.ok(
                $(".o-spreadsheet-templates-dialog").length,
                "should have opened the template modal"
            );
            assert.ok(
                $(".o-spreadsheet-templates-dialog .modal-body .o_searchview").length,
                "The Modal should have a search view"
            );
        });

        QUnit.test("Create spreadsheet from list view opens a modal", async function (assert) {
            await createDocumentsView({
                type: "list",
                resModel: "documents.document",
                serverData: await getDocumentBasicData({
                    "spreadsheet.template,false,search": `<search><field name="name"/></search>`,
                }),
                arch: `<tree js_class="documents_list"></tree>`,
            });
            await click(target, ".o_documents_kanban_spreadsheet");
            assert.ok(
                $(".o-spreadsheet-templates-dialog").length,
                "should have opened the template modal"
            );
            assert.ok(
                $(".o-spreadsheet-templates-dialog .modal-body .o_searchview").length,
                "The Modal should have a search view"
            );
        });

        QUnit.test("Can search template in modal with searchbar", async function (assert) {
            await initTestEnvWithKanban();
            await click(target, ".o_documents_kanban_spreadsheet");
            const dialog = target.querySelector(".o-spreadsheet-templates-dialog");
            assert.equal(dialog.querySelectorAll(".o-template:not(.o-template-ghost-item)").length, 3);
            assert.equal(dialog.querySelector(".o-template").textContent, "Blank spreadsheet");

            const searchInput = dialog.querySelector(".o_searchview_input");
            await editInput(searchInput, null, "Template 1");
            await triggerEvent(searchInput, null, "keydown", { key: "Enter" });
            assert.equal(dialog.querySelectorAll(".o-template:not(.o-template-ghost-item)").length, 2);
            assert.equal(dialog.querySelector(".o-template").textContent, "Blank spreadsheet");
        });

        QUnit.test("Can fetch next templates", async function (assert) {
            let fetch = 0;
            const mockRPC = async function (route, args) {
                if (route === "/web/dataset/search_read" && args.model === "spreadsheet.template") {
                    fetch++;
                    assert.equal(args.limit, 9);
                    assert.step("fetch_templates");
                    if (fetch === 1) {
                        assert.equal(args.offset, 0);
                    } else if (fetch === 2) {
                        assert.equal(args.offset, 9);
                    }
                }
                if (args.method === "search_read" && args.model === "ir.model") {
                    return [{ name: "partner" }];
                }
            };
            await initTestEnvWithKanban({ additionalTemplates: TEST_TEMPLATES, mockRPC });

            await click(target, ".o_documents_kanban_spreadsheet");
            const dialog = document.querySelector(".o-spreadsheet-templates-dialog");

            assert.equal(dialog.querySelectorAll(".o-template:not(.o-template-ghost-item)").length, 10);
            await click(dialog.querySelector(".o_pager_next"));
            assert.verifySteps(["fetch_templates", "fetch_templates"]);
        });

        QUnit.test("Disable create button if no template is selected", async function (assert) {
            assert.expect(2);
            await initTestEnvWithKanban({ additionalTemplates: TEST_TEMPLATES });
            // open template dialog
            await click(target, ".o_documents_kanban_spreadsheet");
            const dialog = document.querySelector(".o-spreadsheet-templates-dialog");

            // select template
            await triggerEvent(dialog.querySelectorAll(".o-template-image")[1], null, "focus");

            // change page; no template should be selected
            await click(dialog.querySelector(".o_pager_next"));
            assert.containsNone(dialog, ".o-template-selected");
            const createButton = dialog.querySelector(".o-spreadsheet-create");
            await click(createButton);
            assert.ok(createButton.attributes.disabled);
        });

        QUnit.test("Can create a blank spreadsheet from template dialog", async function (assert) {
            const mockDoAction = (action) => {
                assert.step("redirect");
                assert.equal(action.tag, "action_open_spreadsheet");
                assert.deepEqual(action.params, {
                    alwaysCreate: true,
                    createFromTemplateId: null,
                    createFromTemplateName: undefined,
                    createInFolderId: 1,
                });
            };
            const kanban = await initTestEnvWithBlankSpreadsheet();
            mockActionService(kanban.env, mockDoAction);

            // ### With confirm button
            await click(target, ".o_documents_kanban_spreadsheet");
            let dialog = document.querySelector(".o-spreadsheet-templates-dialog");
            // select blank spreadsheet
            await triggerEvent(dialog.querySelectorAll(".o-template img")[0], null, "focus");
            await click(dialog.querySelector(".o-spreadsheet-create"));
            assert.verifySteps(["redirect"]);

            // ### With double click on image
            await click(target, ".o_documents_kanban_spreadsheet");
            dialog = document.querySelector(".o-spreadsheet-templates-dialog");
            await triggerEvent(dialog.querySelectorAll(".o-template img")[0], null, "focus");
            await triggerEvent(dialog.querySelectorAll(".o-template img")[0], null, "dblclick");
            assert.verifySteps(["redirect"]);

            // ### With enter key
            await click(target, ".o_documents_kanban_spreadsheet");
            dialog = document.querySelector(".o-spreadsheet-templates-dialog");
            await triggerEvent(dialog.querySelectorAll(".o-template img")[0], null, "focus");
            await triggerEvent(dialog.querySelectorAll(".o-template img")[0], null, "keydown", {
                key: "Enter",
            });
            assert.verifySteps(["redirect"]);
        });

        QUnit.test("Can create a spreadsheet from a template", async function (assert) {
            const mockDoAction = (action) => {
                assert.step("redirect");
                assert.equal(action.tag, "action_open_spreadsheet");
                assert.deepEqual(action.params, {
                    alwaysCreate: true,
                    createFromTemplateId: 1,
                    createFromTemplateName: "Template 1",
                    createInFolderId: 1,
                });
            };
            const kanban = await initTestEnvWithKanban({ additionalTemplates: TEST_TEMPLATES });
            mockActionService(kanban.env, mockDoAction);

            // ### With confirm button
            await click(target, ".o_documents_kanban_spreadsheet");
            let dialog = document.querySelector(".o-spreadsheet-templates-dialog");
            // select blank spreadsheet
            await triggerEvent(dialog.querySelectorAll(".o-template-image")[1], null, "focus");
            await click(dialog.querySelector(".o-spreadsheet-create"));
            assert.verifySteps(["redirect"]);

            // ### With double click on image
            await click(target, ".o_documents_kanban_spreadsheet");
            dialog = document.querySelector(".o-spreadsheet-templates-dialog");
            await triggerEvent(dialog.querySelectorAll(".o-template-image")[1], null, "focus");
            await triggerEvent(dialog.querySelectorAll(".o-template-image")[1], null, "dblclick");
            assert.verifySteps(["redirect"]);

            // ### With enter key
            await click(target, ".o_documents_kanban_spreadsheet");
            dialog = document.querySelector(".o-spreadsheet-templates-dialog");
            await triggerEvent(dialog.querySelectorAll(".o-template-image")[1], null, "focus");
            await triggerEvent(dialog.querySelectorAll(".o-template-image")[1], null, "keydown", {
                key: "Enter",
            });
            assert.verifySteps(["redirect"]);
        });

        QUnit.test("Offset reset to zero after searching for template in template dialog", async function (assert) {
            const mockRPC = async function (route, args) {
                if (route === "/web/dataset/search_read" && args.model === "spreadsheet.template") {
                    assert.step(JSON.stringify({ offset: args.offset, limit: args.limit }));
                }
            };

            await initTestEnvWithKanban({ additionalTemplates: TEST_TEMPLATES, mockRPC });

            await click(target, ".o_documents_kanban_spreadsheet");
            const dialog = document.querySelector(".o-spreadsheet-templates-dialog");

            assert.equal(dialog.querySelectorAll(".o-template:not(.o-template-ghost-item)").length, 10);
            await click(dialog.querySelector(".o_pager_next"));
            assert.verifySteps([
                JSON.stringify({ offset: 0, limit: 9 }),
                JSON.stringify({ offset: 9, limit: 9 }),
            ]);

            const searchInput = dialog.querySelector(".o_searchview_input");
            await editInput(searchInput, null, "Template 1");
            await triggerEvent(searchInput, null, "keydown", { key: "Enter" });
            await nextTick();

            assert.equal(
                dialog.querySelectorAll(".o-template:not(.o-template-ghost-item)").length,
                5
            ); // Blank template, Template 1, Template 10, Template 11, Template 12
            assert.verifySteps([
                JSON.stringify({ offset: 0, limit: 9 }),
            ]);
            assert.strictEqual(
                target.querySelector(".o_pager_value").textContent,
                "1-4",
                "Pager should be reset to 1-4 after searching for a template"
            );
        });
    }
);
