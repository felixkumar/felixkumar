odoo.define('stock_inventory_count_tus.inventory_count', function (require) {
    "use strict";

    var fieldRegistry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');
    var basicFields = require('web.basic_fields');

    var core = require('web.core');
    var QWeb = core.qweb;

    var CountWidget = AbstractField.extend({
        start: function () {
            this._super.apply(this, arguments);
        }
    });
//    debugger
    fieldRegistry.add('count_widget', CountWidget);

    return CountWidget;
});
