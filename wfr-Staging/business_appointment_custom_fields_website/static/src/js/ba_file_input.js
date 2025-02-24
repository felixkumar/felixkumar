/** @odoo-module **/

import publicWidget from "web.public.widget";

publicWidget.registry.baBinaryOnFocus = publicWidget.Widget.extend({
    selector: ".ba_custom_fields_portal",
    events: {"focus .ba_binary_input": "_onShowFile",},
    _onShowFile: function (event) {
        if (event.currentTarget.type != "file") {
            event.preventDefault();
            event.stopPropagation(); 
            event.currentTarget.type = "file";
        };
    },
});
