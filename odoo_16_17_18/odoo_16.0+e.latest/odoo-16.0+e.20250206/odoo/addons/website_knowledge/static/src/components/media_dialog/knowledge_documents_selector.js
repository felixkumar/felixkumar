/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { KnowledgeDocumentSelector } from '@knowledge/components/media_dialog/knowledge_documents_selector';

patch(KnowledgeDocumentSelector.prototype, "website_knowledge_documents_selector", {
    /**
     * @override
     * As KnowledgeDocumentsSelector is an aggregate of multiple kinds of
     * files, images included, the domain should be adjusted with the same
     * constraints as @see image_selector.js
     */
    get attachmentsDomain() {
        const domain = this._super(...arguments);
        domain.push('|', ['url', '=', false], '!', ['url', '=like', '/web/image/website.%']);
        domain.push(['key', '=', false]);
        return domain;
    }
});
