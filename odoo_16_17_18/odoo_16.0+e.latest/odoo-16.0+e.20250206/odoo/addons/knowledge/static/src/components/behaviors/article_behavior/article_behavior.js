/** @odoo-module */

import { _t } from "web.core";
import { AbstractBehavior } from "@knowledge/components/behaviors/abstract_behavior/abstract_behavior";
import { encodeDataBehaviorProps } from "@knowledge/js/knowledge_utils";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";

const { useEffect } = owl;


export class ArticleBehavior extends AbstractBehavior {
    setup () {
        super.setup();
        this.actionService = useService('action');
        this.dialogService = useService('dialog');
        useEffect(() => {
            /**
             * @param {Event} event
             */
            const onLinkClick = async event => {
                event.preventDefault();
                event.stopPropagation();
                // TODO: remove when the model correctly asks the htmlField if
                // it is dirty. This askChanges is necessary because the
                // /article Behavior can be used outside of Knowledge.
                await this.props.record.askChanges();
                this.openArticle();
            };
            this.props.anchor.addEventListener('click', onLinkClick);
            return () => {
                this.props.anchor.removeEventListener('click', onLinkClick);
            };
        });
    }

    /**
     * Some `/article` blocks had their behavior-props encoded with
     * `JSON.stringify` instead of `encodeDataBehaviorProps`. This override is
     * there to ensure that props are encoded with the correct format.
     * TODO ABD: this logic should be ultimately part of a knowledge upgrade.
     * @see AbstractBehavior
     * @override
     */
    setupAnchor() {
        super.setupAnchor();
        if (!this.props.readonly) {
            try {
                // JSON.parse will crash if the props are already encoded,
                // in that case there is no need to update them.
                this.props.anchor.dataset.behaviorProps = encodeDataBehaviorProps(
                    JSON.parse(this.props.anchor.dataset.behaviorProps)
                );
            } catch {}
        }
    }

    async openArticle () {
        try {
            await this.actionService.doAction('knowledge.ir_actions_server_knowledge_home_page', {
                additionalContext: {
                    res_id: parseInt(this.props.article_id)
                }
            });
        } catch (_) {
            this.dialogService.add(AlertDialog, {
                title: _t('Error'),
                body: _t("This article was deleted or you don't have the rights to access it."),
                confirmLabel: _t('Ok'),
            });
        }
    }
}

ArticleBehavior.template = "knowledge.ArticleBehavior";
ArticleBehavior.components = {};
ArticleBehavior.props = {
    ...AbstractBehavior.props,
    display_name: { type: String, optional: false },
    article_id: { type: Number, optional: false }
};
