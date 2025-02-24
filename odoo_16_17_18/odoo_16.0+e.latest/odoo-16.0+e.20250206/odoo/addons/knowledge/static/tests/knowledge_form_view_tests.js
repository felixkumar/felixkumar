/** @odoo-module */

import { onWillStart } from "@odoo/owl";
import { makeDeferred, mockSendBeacon, nextTick, patchWithCleanup } from "@web/../tests/helpers/utils";
import { makeView, setupViewRegistries } from "@web/../tests/views/helpers";
import { registry } from "@web/core/registry";
import { patch, unpatch } from "@web/core/utils/patch";
import { HtmlField } from "@web_editor/js/backend/html_field";
import { parseHTML } from "@web_editor/js/editor/odoo-editor/src/utils/utils";
import { makeFakeMessagingServiceForKnowledge } from "@knowledge/../tests/mock_services";
import { TemplateBehavior } from "@knowledge/components/behaviors/template_behavior/template_behavior";
import { KnowledgeArticleFormController } from "@knowledge/js/knowledge_controller";
const serviceRegistry = registry.category("services");

let serverData;
let arch;
let htmlField;
let htmlFieldPromise;
let formController;
let record;

QUnit.module("Knowledge - Ensure body save scenarios", (hooks) => {
    hooks.beforeEach(() => {
        patchWithCleanup(KnowledgeArticleFormController.prototype, {
            setup() {
                this._super(...arguments);
                formController = this;
            }
        });
        htmlFieldPromise = makeDeferred();
        patchWithCleanup(HtmlField.prototype, {
            async startWysiwyg() {
                await this._super(...arguments);
                await nextTick();
                htmlFieldPromise.resolve(this);
            }
        });
        record = {
            id: 1,
            display_name: "Article",
            body: "<p class='test_target'><br></p>",
        };
        serverData = {
            models: {
                knowledge_article: {
                    fields: {
                        display_name: {string: "Displayed name", type: "char"},
                        body: {string: "Body", type: "html"},
                    },
                    records: [record],
                    methods: {
                        get_sidebar_articles() {
                            return {articles: [], favorite_ids: []};
                        }
                    }
                }
            },
        };
        arch = `
            <form js_class="knowledge_article_view_form">
                <sheet>
                    <div t-ref="tree"/>
                    <div t-ref="root">
                        <div class="o_knowledge_editor">
                            <field name="body" widget="html"/>
                        </div>
                    </div>
                </sheet>
            </form>
        `;
        setupViewRegistries();
        serviceRegistry.add('messaging', makeFakeMessagingServiceForKnowledge());
    });

    //--------------------------------------------------------------------------
    // TESTS
    //--------------------------------------------------------------------------

    QUnit.test("Ensure save on beforeLeave when Behaviors mutex is not idle and when it is", async function (assert) {
        /**
         * This test forces a call to the beforeLeave function of the KnowledgeFormController. It
         * simulates that we leave the form view.
         *
         * The function will be called 2 times successively:
         * 1- at a controlled time when a Behavior is in the process of being
         *    mounted, but not finished, to ensure that the saved article value is
         *    not corrupted (no missing html node).
         * 2- at a controlled time when every Behavior was successfully mounted and
         *    no other Behavior is being mounted, to ensure that the saved article
         *    value contains information updated from the Behavior nodes.
         */

        assert.expect(4);
        let writeCount = 0;
        await makeView({
            type: "form",
            resModel: "knowledge_article",
            serverData,
            arch,
            resId: 1,
            mockRPC(route, args) {
                if (
                    route === '/web/dataset/call_kw/knowledge_article/write' &&
                    args.model === 'knowledge_article'
                ) {
                    if (writeCount === 0) {
                        // The first expected `write` value should be the
                        // unmodified blueprint, since OWL has not finished
                        // mounting the Behavior nodes.
                        assert.notOk(editor.editable.querySelector('[data-prop-name="content"]'));
                        assert.equal(editor.editable.querySelector('.witness').textContent, "WITNESS_ME!");
                    } else if (writeCount === 1) {
                        // Change the expected `write` value, the "witness node"
                        // should have been cleaned since it serves no purpose
                        // for this Behavior in the OWL template.
                        assert.notOk(editor.editable.querySelector('.witness'));
                        assert.equal(editor.editable.querySelector('[data-prop-name="content"]').innerHTML, "<p><br></p>");
                    } else {
                        // This should never be called and will fail if it is.
                        assert.ok(writeCount === 1, "Write should only be called 2 times during this test");
                    }
                    writeCount += 1;
                }
            }
        });
        // Let the htmlField be mounted and recover the Component instance.
        htmlField = await htmlFieldPromise;
        const editor = htmlField.wysiwyg.odooEditor;

        // Patch to control when the next mounting is done.
        const isAtWillStart = makeDeferred();
        const pauseWillStart = makeDeferred();
        patch(TemplateBehavior.prototype, "TEMPLATE_DELAY_MOUNT_TEST_PATCH", {
            setup() {
                this._super(...arguments);
                onWillStart(async () => {
                    isAtWillStart.resolve();
                    await pauseWillStart;
                    unpatch(TemplateBehavior.prototype, "TEMPLATE_DELAY_MOUNT_TEST_PATCH");
                });
            }
        });
        // Introduce a Behavior blueprint with an "witness node" that does not
        // serve any purpose except for the fact that it should be left
        // untouched until OWL completely finishes its mounting process
        // and at that point it will be replaced by the rendered OWL template.
        const behaviorHTML = `
            <div class="o_knowledge_behavior_anchor o_knowledge_behavior_type_template">
                <div class="witness">WITNESS_ME!</div>
            </div>
        `;
        const anchor = parseHTML(behaviorHTML).firstChild;
        const target = editor.editable.querySelector(".test_target");
        // The BehaviorState MutationObserver will try to start the mounting
        // process for the Behavior with the anchor node as soon as it is in
        // the DOM.
        editor.editable.replaceChild(anchor, target);
        // Validate the mutation as a normal user history step.
        editor.historyStep();

        // Wait for the Template Behavior onWillStart lifecycle step.
        await isAtWillStart;

        // Attempt a save when the mutex is not idle. It should save the
        // unchanged blueprint of the Behavior.
        await formController.beforeLeave();

        // Allow the Template Behavior to go past the `onWillStart` lifecycle
        // step.
        pauseWillStart.resolve();

        // Wait for the mount mutex to be idle. The Template Behavior should
        // be fully mounted after this.
        await htmlField.updateBehaviors();

        // Attempt a save when the mutex is idle.
        await formController.beforeLeave();
    });

    QUnit.test("Ensure save on beforeUnload when Behaviors mutex is not idle and when it is", async function (assert) {
        /**
         * This test forces a call to the beforeUnload function of the KnowledgeFormController. It
         * simulates that the close the browser/tab when being on that form view.
         *
         * The function will be called 2 times successively:
         * 1- at a controlled time when a Behavior is in the process of being
         *    mounted, but not finished, to ensure that the saved article value is
         *    not corrupted (no missing html node).
         * 2- at a controlled time when every Behavior was successfully mounted and
         *    no other Behavior is being mounted, to ensure that the saved article
         *    value contains information updated from the Behavior nodes.
         */

        mockSendBeacon((route) => {
            if (route === '/web/dataset/call_kw/knowledge_article/write') {
                if (writeCount === 0) {
                    // The first expected `write` value should be the
                    // unmodified blueprint, since OWL has not finished
                    // mounting the Behavior nodes.
                    assert.notOk(editor.editable.querySelector('[data-prop-name="content"]'));
                    assert.equal(editor.editable.querySelector('.witness').textContent, "WITNESS_ME!");
                } else if (writeCount === 1) {
                    // Change the expected `write` value, the "witness node"
                    // should have been cleaned since it serves no purpose
                    // for this Behavior in the OWL template.
                    assert.notOk(editor.editable.querySelector('.witness'));
                    assert.equal(editor.editable.querySelector('[data-prop-name="content"]').innerHTML, "<p><br></p>");
                } else {
                    // This should never be called and will fail if it is.
                    assert.ok(writeCount === 1, "Write should only be called 2 times during this test");
                }
                writeCount += 1;
            }
        });

        assert.expect(4);
        let writeCount = 0;
        await makeView({
            type: "form",
            resModel: "knowledge_article",
            serverData,
            arch,
            resId: 1,
        });
        // Let the htmlField be mounted and recover the Component instance.
        htmlField = await htmlFieldPromise;
        const editor = htmlField.wysiwyg.odooEditor;

        // Patch to control when the next mounting is done.
        const isAtWillStart = makeDeferred();
        const pauseWillStart = makeDeferred();
        patch(TemplateBehavior.prototype, "TEMPLATE_DELAY_MOUNT_TEST_PATCH", {
            setup() {
                this._super(...arguments);
                onWillStart(async () => {
                    isAtWillStart.resolve();
                    await pauseWillStart;
                    unpatch(TemplateBehavior.prototype, "TEMPLATE_DELAY_MOUNT_TEST_PATCH");
                });
            }
        });
        // Introduce a Behavior blueprint with an "witness node" that does not
        // serve any purpose except for the fact that it should be left
        // untouched until OWL completely finishes its mounting process
        // and at that point it will be replaced by the rendered OWL template.
        const behaviorHTML = `
            <div class="o_knowledge_behavior_anchor o_knowledge_behavior_type_template">
                <div class="witness">WITNESS_ME!</div>
            </div>
        `;
        const anchor = parseHTML(behaviorHTML).firstChild;
        const target = editor.editable.querySelector(".test_target");
        // The BehaviorState MutationObserver will try to start the mounting
        // process for the Behavior with the anchor node as soon as it is in
        // the DOM.
        editor.editable.replaceChild(anchor, target);
        // Validate the mutation as a normal user history step.
        editor.historyStep();

        // Wait for the Template Behavior onWillStart lifecycle step.
        await isAtWillStart;

        // Attempt a save when the mutex is not idle. It should save the
        // unchanged blueprint of the Behavior.
        await formController.beforeUnload();
        await nextTick();

        // Allow the Template Behavior to go past the `onWillStart` lifecycle
        // step.
        pauseWillStart.resolve();

        // Wait for the mount mutex to be idle. The Template Behavior should
        // be fully mounted after this.
        await htmlField.updateBehaviors();

        // Attempt a save when the mutex is idle.
        await formController.beforeUnload();
        await nextTick();
    });
});
