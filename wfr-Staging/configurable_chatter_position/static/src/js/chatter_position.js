/** @odoo-module **/

import { session } from "@web/session";
import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { uiService , getMediaQueryLists} from "@web/core/ui/ui_service";

const MEDIAS = getMediaQueryLists();


patch(FormController.prototype, "configurable_chatter_position", {
    ClickChatterPositionButton(){
        var self = this;
        self.env.services.rpc("/configurable_chatter_position",{})
        .then(function(position){
            session.context_chatter_position = position;
            window.dispatchEvent(new Event('resize'));
        })
    }
});

patch(uiService, "configurable_chatter_position_service", {
    getSize() {
        var uiSize = MEDIAS.findIndex((media) => media.matches);
        if (session.context_chatter_position == 'chatter_bottom') {
            uiSize = uiSize >= 5 ? 5: uiSize;
        } else if (session.context_chatter_position == 'chatter_right') {
            uiSize = uiSize < 5 ? 6: uiSize;
        }
        return uiSize;
    }
});
