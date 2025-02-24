odoo.define("point_of_sale.tour.PoSSettleDue", function (require) {
    "use strict";

    const { ProductScreen } = require("point_of_sale.tour.ProductScreenTourMethods");
    const { PartnerListScreen } = require("pos_settle_due.tour.PartnerListScreenTourMethods");
    const { getSteps, startSteps } = require("point_of_sale.tour.utils");
    var Tour = require("web_tour.tour");

    startSteps();
    ProductScreen.do.clickPartnerButton();
    PartnerListScreen.do.clickPartnerDetailsButton("A Partner");
    PartnerListScreen.check.settleButtonTextIs("Deposit money");
    PartnerListScreen.do.clickBack();
    PartnerListScreen.do.clickPartnerDetailsButton("B Partner");
    PartnerListScreen.check.settleButtonTextIs("Settle due accounts");
    Tour.register("SettleDueButtonPresent", { test: true, url: "/pos/ui" }, getSteps());
});
