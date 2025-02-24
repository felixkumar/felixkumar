/* @odoo-module */
import { registerPatch } from '@mail/model/model_core';
import { attr, many, one } from '@mail/model/model_field';
import { clear, insert, link } from '@mail/model/model_field_command';

registerPatch({
    name: 'Chatter',
    recordMethods: {
        async refresh() {
            var res = await this._super();
             debugger
            if(this.webRecord && this.webRecord.data && this.webRecord.data.id && !isNaN(this.webRecord.data.id))
                this.openAttachmentBoxView()
            return res
        },
    }
});