odoo.define("pos_settle_due.tour.PartnerListScreenTourMethods", function (require) {
    "use strict";

    const { createTourMethods } = require("point_of_sale.tour.utils");
    const { Do, Check, Execute } = require("point_of_sale.tour.PartnerListScreenTourMethods");

    class CheckExt extends Check {
        settleButtonTextIs(name) {
            return [
                {
                    content: "check the content of the settle button",
                    trigger: `.button.settle-due:contains(${name})`,
                    run: () => {},
                },
            ];
        }
    }
    return createTourMethods("PartnerListScreen", Do, CheckExt, Execute);
});
