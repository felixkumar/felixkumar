/** @odoo-module **/

import { ComponentWrapper } from 'web.OwlCompatibility';
import { qweb as QWeb, _t } from 'web.core';
import Wysiwyg from 'web_editor.wysiwyg';
import { KnowledgeArticleLinkModal } from './wysiwyg/knowledge_article_link.js';
import { PromptEmbeddedViewNameDialogWrapper } from '../components/prompt_embedded_view_name_dialog/prompt_embedded_view_name_dialog.js';
import { preserveCursor } from '@web_editor/js/editor/odoo-editor/src/OdooEditor';
import { Markup } from 'web.utils';
import {
    encodeDataBehaviorProps,
} from "@knowledge/js/knowledge_utils";

Wysiwyg.include({
    /**
     * @override
     */
    resetEditor: async function () {
        await this._super(...arguments);
        this.$editable[0].dispatchEvent(new Event('refresh_behaviors'));
    },
    /**
     * @override
     */
    setValue: function () {
        // Temporary hack that will be removed in 16.2 with the full
        // implementation of oeProtected in the editor.
        // purpose: ignore locks from Behavior components rendering
        // when the content of the editor is reset (those components will also
        // have to be reset anyway)
        if (this.odooEditor._observerUnactiveLabels.size) {
            [...this.odooEditor._observerUnactiveLabels].forEach(lock => {
                if (lock && lock.startsWith('knowledge_behavior_id_')) {
                    this.odooEditor.observerActive(lock);
                }
            });
        }
        this._super(...arguments);
    },
    /**
     * Check if the selection starts inside a table. This function can be used
     * as the `isDisabled` property of a command of the PowerBox to disable
     * a command in a table.
     * @returns {boolean} true if the command should be filtered
     */
    _filterCommandInTable: function () {
        let anchor = document.getSelection().anchorNode;
        if (anchor.nodeType !== Node.ELEMENT_NODE) {
            anchor = anchor.parentElement;
        }
        if (anchor && anchor.closest('table')) {
            return true;
        }
        return false;
    },
    /**
     * Check if the selection starts inside a Behavior element.
     * This function can be used as the `isDisabled` property of a command of
     * the PowerBox to disable a command in a template.
     * Example: The content of a /template block is destined to be used in
     * @see OdooEditor in modules other than Knowledge, where knowledge-specific
     * commands may not be available, so commands inserting a non-supported
     * Behavior in the /template content should be disabled.
     * @returns {boolean} true if the command should be filtered
     */
    _filterCommandInBehavior: function () {
        let anchor = document.getSelection().anchorNode;
        if (anchor.nodeType !== Node.ELEMENT_NODE) {
            anchor = anchor.parentElement;
        }
        if (anchor && anchor.closest('.o_knowledge_behavior_anchor')) {
            return true;
        }
        return false;
    },
    /**
     * @override
     * @returns {Array[Object]}
     */
    _getPowerboxOptions: function () {
        const options = this._super();
        const {commands, categories} = options;
        categories.push({ name: _t('Media'), priority: 50 });
        commands.push({
            category: _t('Media'),
            name: _t('Article'),
            priority: 10,
            description: _t('Link an article.'),
            fontawesome: 'fa-file',
            isDisabled: () => this.options.isWebsite || this.options.inIframe,
            callback: () => {
                this._insertArticleLink();
            },
        });
        if (this.options.knowledgeCommands) {
            categories.push({ name: _t('Knowledge'), priority: 10 });
            commands.push({
                category: _t('Knowledge'),
                name: _t('File'),
                priority: 20,
                description: _t('Embed a file.'),
                fontawesome: 'fa-file',
                isDisabled: () => this._filterCommandInBehavior() || this._filterCommandInTable(),
                callback: () => {
                    this.openMediaDialog({
                        noVideos: true,
                        noImages: true,
                        noIcons: true,
                        noDocuments: true,
                        knowledgeDocuments: true,
                    });
                }
            }, {
                category: _t('Knowledge'),
                name: _t('Template'),
                priority: 10,
                description: _t('Add a template section.'),
                fontawesome: 'fa-pencil-square',
                isDisabled: () => this._filterCommandInBehavior() || this._filterCommandInTable(),
                callback: () => {
                    this._insertTemplate();
                },
            }, {
                category: _t('Knowledge'),
                name: _t('Table Of Content'),
                priority: 30,
                description: _t('Add a table of content.'),
                fontawesome: 'fa-bookmark',
                isDisabled: () => this._filterCommandInBehavior() || this._filterCommandInTable(),
                callback: () => {
                    this._insertTableOfContent();
                },
            }, {
                category: _t('Knowledge'),
                name: _t('Item Kanban'),
                priority: 40,
                description: _t('Insert a Kanban view of article items'),
                fontawesome: 'fa-th-large',
                isDisabled: () => this._filterCommandInBehavior() || this._filterCommandInTable(),
                callback: () => {
                    const restoreSelection = preserveCursor(this.odooEditor.document);
                    const viewType = 'kanban';
                    this._openEmbeddedViewDialog(viewType, name => {
                        restoreSelection();
                        this._insertEmbeddedView('knowledge.knowledge_article_item_action', viewType, name, {
                            active_id: this.options.recordInfo.res_id,
                            default_parent_id: this.options.recordInfo.res_id,
                            default_icon: '📄',
                            default_is_article_item: true,
                        });
                    });
                }
            }, {
                category: _t('Knowledge'),
                name: _t('Item List'),
                priority: 50,
                description: _t('Insert a List view of article items'),
                fontawesome: 'fa-th-list',
                isDisabled: () => this._filterCommandInBehavior() || this._filterCommandInTable(),
                callback: () => {
                    const restoreSelection = preserveCursor(this.odooEditor.document);
                    const viewType = 'list';
                    this._openEmbeddedViewDialog(viewType, name => {
                        restoreSelection();
                        this._insertEmbeddedView('knowledge.knowledge_article_item_action', viewType, name, {
                            active_id: this.options.recordInfo.res_id,
                            default_parent_id: this.options.recordInfo.res_id,
                            default_icon: '📄',
                            default_is_article_item: true,
                        });
                    });
                }
            }, {
                category: _t('Knowledge'),
                name: _t('Index'),
                priority: 60,
                description: _t('Show the first level of nested articles.'),
                fontawesome: 'fa-list',
                isDisabled: () => this._filterCommandInBehavior() || this._filterCommandInTable(),
                callback: () => {
                    this._insertArticlesStructure(true);
                }
            }, {
                category: _t('Knowledge'),
                name: _t('Article Structure'),
                priority: 60,
                description: _t('Show all nested articles.'),
                fontawesome: 'fa-list',
                isDisabled: () => this._filterCommandInBehavior() || this._filterCommandInTable(),
                callback: () => {
                    this._insertArticlesStructure(false);
                }
            });
        }
        return {...options, commands, categories};
    },
    /**
     * Notify @see FieldHtmlInjector that behaviors need to be injected
     * @see KnowledgeBehavior
     *
     * @param {Element} anchor
     */
    _notifyNewBehavior(anchor) {
        const behaviorsData = [];
        const type = Array.from(anchor.classList).find(className => className.startsWith('o_knowledge_behavior_type_'));
        if (type) {
            behaviorsData.push({
                anchor: anchor,
                behaviorType: type,
                setCursor: true,
            });
        }
        this.$editable.trigger('refresh_behaviors', { behaviorsData: behaviorsData});
    },
    /**
     * Insert a /toc block (table of content)
     */
    _insertTableOfContent: function () {
        const tableOfContentBlock = $(QWeb.render('knowledge.abstract_behavior', {
            behaviorType: "o_knowledge_behavior_type_toc",
        }))[0];
        const [container] = this.odooEditor.execCommand('insert', tableOfContentBlock);
        this._notifyNewBehavior(container);
    },
    /**
     * Insert a /structure block.
     * It will list all the articles that are direct children of this one.
     * @param {boolean} childrenOnly
     */
    _insertArticlesStructure: function (childrenOnly) {
        const articlesStructureBlock = $(QWeb.render('knowledge.articles_structure_wrapper', {
            childrenOnly: childrenOnly
        }))[0];
        const [container] = this.odooEditor.execCommand('insert', articlesStructureBlock);
        this._notifyNewBehavior(container);
    },
    /**
     * Insert a /template block
     */
    _insertTemplate() {
        const templateBlock = $(QWeb.render('knowledge.abstract_behavior', {
            behaviorType: "o_knowledge_behavior_type_template",
        }))[0];
        const [container] = this.odooEditor.execCommand('insert', templateBlock);
        this._notifyNewBehavior(container);
    },
    /**
     * Insert a /article block (through a dialog)
     */
    _insertArticleLink: function () {
        const restoreSelection = preserveCursor(this.odooEditor.document);
        const dialog = new KnowledgeArticleLinkModal(this, {});
        dialog.on('save', this, article => {
            if (article) {
                const articleLinkBlock = $(QWeb.render('knowledge.wysiwyg_article_link', {
                    href: '/knowledge/article/' + article.id,
                    data: encodeDataBehaviorProps({
                        article_id: article.id,
                        display_name: article.display_name,
                    }),
                }))[0];
                dialog.close();
                restoreSelection();
                const nameNode = document.createTextNode(article.display_name);
                articleLinkBlock.appendChild(nameNode);
                const [anchor] = this.odooEditor.execCommand('insert', articleLinkBlock);
                this._notifyNewBehavior(anchor);
            }
        });
        dialog.on('closed', this, () => {
            restoreSelection();
        });
        dialog.open();
    },
    /**
     * Inserts a view in the editor
     * @param {String} actWindowId - Act window id of the action
     * @param {String} viewType - View type
     * @param {String} name - Name
     * @param {Object} context - Context
     */
    _insertEmbeddedView: async function (actWindowId, viewType, name, context={}) {
        const restoreSelection = preserveCursor(this.odooEditor.document);
        restoreSelection();
        context.knowledge_embedded_view_framework = 'owl';
        const embeddedViewBlock = $(await this._rpc({
            model: 'knowledge.article',
            method: 'render_embedded_view',
            args: [[this.options.recordInfo.res_id], actWindowId, viewType, name, context],
        }))[0];
        const [container] = this.odooEditor.execCommand('insert', embeddedViewBlock);
        this._notifyNewBehavior(container);
    },
    /**
     * Notify the @see FieldHtmlInjector when a /file block is inserted from a
     * @see MediaDialog
     *
     * @private
     * @override
     */
    _onMediaDialogSave(params, element) {
        if (element.classList.contains('o_is_knowledge_file')) {
            params.restoreSelection();
            element.classList.remove('o_is_knowledge_file');
            element.classList.add('o_image');
            const extension = (element.title && element.title.split('.').pop()) || element.dataset.mimetype;
            const fileBlock = $(QWeb.render('knowledge.WysiwygFileBehavior', {
                behaviorType: "o_knowledge_behavior_type_file",
                fileName: element.title,
                fileImage: Markup(element.outerHTML),
                behaviorProps: encodeDataBehaviorProps({
                    fileName: element.title,
                    fileExtension: extension,
                }),
                fileExtension: extension,
            }))[0];
            const [container] = this.odooEditor.execCommand('insert', fileBlock);
            this._notifyNewBehavior(container);
            // need to set cursor (anchor.sibling)
        } else {
            return this._super(...arguments);
        }
    },
    /**
     * Inserts the dialog allowing the user to specify name for the embedded view.
     * @param {String} viewType
     * @param {Function} save
     */
    _openEmbeddedViewDialog: function (viewType, save) {
        // TODO: remove the wrapper when the wysiwyg is converted to owl.
        const dialog = new ComponentWrapper(this, PromptEmbeddedViewNameDialogWrapper, {
            isNew: true,
            viewType: viewType,
            save: save
        });
        dialog.mount(document.body);
    },
});
