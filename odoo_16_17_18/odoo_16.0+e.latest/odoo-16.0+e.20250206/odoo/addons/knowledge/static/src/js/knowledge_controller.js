/** @odoo-module */

import { FormController } from '@web/views/form/form_controller';

export class KnowledgeArticleFormController extends FormController {
    /**
     * @TODO remove when the model correctly asks the htmlField if it is dirty.
     * Ensure that all fields did have the opportunity to commit their changes
     * so as to set the record dirty if needed. This is what should be done
     * in the generic controller but is not because the html field reports
     * itself as dirty too often. This override can be omitted as soon as the
     * htmlField dirty feature is reworked/improved. It is needed in Knowledge
     * because the body of an article is its core feature and it's best that it
     * is saved more often than needed than the opposite.
     *
     * @override
     */
    async beforeLeave() {
        await this.model.root.askChanges();
        return super.beforeLeave();
    }
}

// Open articles in edit mode by default
KnowledgeArticleFormController.defaultProps = {
    ...FormController.defaultProps,
    mode: 'edit',
};
