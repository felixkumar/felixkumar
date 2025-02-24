/** @odoo-module */
import tour from "web_tour.tour";

tour.register(
    "web_enterprise.test_studio_list_upsell",
    {
        test: true,
    },
    [
        {
            trigger: ".o_list_view",
        },
        {
            trigger: ".o_optional_columns_dropdown > button",
        },
        {
            trigger: ".o_optional_columns_dropdown .dropdown-item-studio",
            isCheck: true,
        },
    ]
);
