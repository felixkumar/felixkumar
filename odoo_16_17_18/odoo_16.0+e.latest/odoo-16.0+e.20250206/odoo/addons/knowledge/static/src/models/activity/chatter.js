/** @odoo-module **/

import { registerPatch } from '@mail/model/model_core';
import core from 'web.core';

registerPatch({
    name: 'Chatter',
    recordMethods: {
        async onClickChatterSearchArticle(event) {
            if (this.isTemporary) {
                const saved = await this.doSaveRecord();
                if (!saved) {
                    return;
                }
            }
            core.bus.trigger("openMainPalette", {
                searchValue: "?",
            });
        },
    },
});
