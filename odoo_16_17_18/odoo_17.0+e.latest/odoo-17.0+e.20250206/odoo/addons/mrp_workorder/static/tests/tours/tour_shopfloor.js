/** @odoo-module **/

import { registry } from "@web/core/registry";
import { TourError } from "@web_tour/tour_service/tour_utils";
import { stepUtils } from "./tour_step_utils";
import helper from "./tour_helper_mrp_workorder";

registry.category("web_tour.tours").add('test_shop_floor', {test: true, steps: () => [
    {
        content: 'Select the workcenter the first time we enter in shopfloor',
        trigger: 'button:has(input[name="Savannah"])'
    },
    {
        content: 'Select the second workcenter',
        extra_trigger: 'button.active:has(input[name="Savannah"])',
        trigger: 'button:has(input[name="Jungle"])'
    },
    {
        extra_trigger: 'button.active:has(input[name="Jungle"])',
        trigger: 'footer.modal-footer button.btn-primary'
    },
    {
        content: 'Open the employee panel',
        extra_trigger: '.o_control_panel_actions button:contains("Savannah")',
        trigger: 'button[name="employeePanelButton"]'
    },
    {
        content: 'Add operator button',
        trigger: 'button:contains("Operator")'
    },
    {
        content: 'Select the Marc Demo employee',
        trigger: '.modal-body .popup .selection div:contains("Marc Demo")'
    },
    {
        content: 'Go to workcenter Savannah from MO card',
        extra_trigger: '.o_mrp_employees_panel li.o_admin_user:contains(Marc Demo)',
        trigger: '.o_mrp_record_line button span:contains("Savannah")'
    },
    {
        content: 'Start the workorder on header click',
        extra_trigger: '.o_control_panel_actions button.active:contains("Savannah")',
        trigger: '.o_finished_product span:contains("Giraffe")'
    },
    {
        content: 'Register production check',
        extra_trigger: '.o_workorder_lot span:contains("lot")',
        trigger: '.o_workorder_lot .btn.fa-plus'
    },
    { trigger: 'button[barcode_trigger="next"]' },
    {
        content: 'Instruction check via form',
        trigger: '.modal-title:contains("Instructions")',
        run: 'scan O-BTN.next'
    },
    {
        content: 'Component not tracked registration and continue production',
        extra_trigger: '.modal-title:contains("Register legs")',
        trigger: 'button[barcode_trigger="continue"]'
    },
    {
        content: 'Add 2 units',
        extra_trigger: '.o_field_widget[name="qty_done"] input:propValue("0.00")',
        trigger: '.o_field_widget[name="qty_done"] input',
        run: 'text 2',
    },
    {
        extra_trigger: '.o_field_widget[name="qty_done"] input:propValue("2.00")',
        trigger: 'button[barcode_trigger="next"]'
    },
    {
        content: 'Set NE2 as 1st serial for tracked component',
        extra_trigger: '.o_field_widget[name="lot_id"] input:propValue("NE1")',
        trigger: '.o_field_widget[name="lot_id"] input',
        run: 'text NE2',
    },
    { trigger: '.ui-menu-item > a:contains("NE2")' },
    { trigger: 'button[barcode_trigger="continue"]' },
    {
        content: 'Accept NE1 as 2nd serial',
        extra_trigger: '.o_field_widget[name="lot_id"] input:propValue("NE1")',
        trigger: 'button[barcode_trigger="next"]',
    },
    {
        extra_trigger: '.modal-title:contains("Release")',
        trigger: '.modal-header .btn-close'
    },
    {
        content: 'Fast check last instruction step',
        extra_trigger: '.o_web_client:not(.modal-open)',
        trigger: '.o_mrp_record_line .fa-square-o',
    },
    {
        content: 'Close first operation',
        extra_trigger: '.o_mrp_record_line:contains("Release") button.text-success',
        trigger: '.card-footer button[barcode_trigger="cloWO"]',
    },
    {
        content: 'Switch to second workcenter for next operation',
        extra_trigger: '.o_nocontent_help',
        trigger: '.o_control_panel_actions button:contains("Jungle")',
    },
    {
        content: 'Open the WO setting menu again',
        trigger: '.o_mrp_display_record:contains("Release") .card-footer button.fa-ellipsis-v',
    },
    {
        content: 'Add an operation button',
        trigger: 'button[name="addComponent"]',
    },
    {
        content: 'Add Color',
        trigger: '.o_field_widget[name=product_id] input',
        run: 'text color'
    },
    { trigger: '.ui-menu-item > a:contains("Color")' },
    {
        extra_trigger: 'div.o_dialog input#product_id_0:propValue("Color")',
        trigger: 'button[name=add_product]',
    },
    {
        extra_trigger: 'body:not(.modal-open)',
        trigger: '.o_mrp_record_line .btn-outline-secondary:contains("2")'
    },
    { trigger: 'button[barcode_trigger=cloWO]' },
    { trigger: 'button[barcode_trigger=cloMO]' },
    {
        content: 'Leave shopfloor',
        extra_trigger: '.o_nocontent_help',
        trigger: '.o_home_menu .fa-sign-out',
    },
    { trigger: '.o_apps', isCheck: true }
]})

registry.category("web_tour.tours").add("test_shop_floor_my_wo_filter_with_pin_user", {
    test: true,
    steps: () => [
        // Select the right workcenter.
        { trigger: 'button:has(input[name="Winter\'s Workshop"])' },
        {
            extra_trigger: 'button.active:has(input[name="Winter\'s Workshop"])',
            trigger: "footer.modal-footer button.btn-primary",
        },
        // Open the employee panel and select first and second employees.
        {
            extra_trigger: '.o_control_panel_actions button:contains("Winter\'s Workshop")',
            trigger: 'button[name="employeePanelButton"]'
        },
        { trigger: 'button:contains("Operator")' },
        { trigger: '.modal-body .popup .selection div:contains("John Snow")' },
        {
            extra_trigger: '.o_mrp_employees_panel .o_admin_user:contains("John Snow")',
            trigger: 'button:contains("Operator")',
        },
        { trigger: '.modal-body .popup .selection div:contains("Queen Elsa")' },
        // Enter the PIN code for second employee.
        ...stepUtils.enterPIN("41213"),
        {
            content: "Display right Workcenter",
            extra_trigger: '.o_mrp_employees_panel .o_admin_user:contains("Queen Elsa")',
            trigger: '.o_control_panel_actions button:contains("Winter\'s Workshop")',
        },
        {
            content: "Start the first WO with the second employee",
            extra_trigger: 'button:contains("Winter\'s Workshop").active',
            trigger: ".o_mrp_display_record:first-child .card-title",
        },
        {
            extra_trigger: ".o_mrp_display_record.o_active",
            trigger: ".o_mrp_employees_panel li:contains(John Snow)",
        },
        {
            content: "Start the second WO with the first employee",
            extra_trigger: ".o_admin_user:contains(John Snow)",
            trigger: ".o_mrp_display_record:last-child .card-title",
        },

        {
            content: 'Display "My WO" workorders',
            extra_trigger: ".o_mrp_display_record:contains('TEST/00002').o_active",
            trigger: ".o_control_panel_actions button:contains(My WO)",
        },
        // Check the right WO is displayed.
        {
            trigger: ".o_control_panel_actions button:contains(My WO).active",
            run: () => {
                const currentEmployeeEl = document.querySelector(".o_admin_user div.fw-bold");
                helper.assert(currentEmployeeEl.innerText, "John Snow");
                const records = document.querySelectorAll(".o_mrp_display_record");
                helper.assert(records.length, 1);
                const recordTitle = records[0].querySelector(".card-title>span").innerText;
                helper.assert(recordTitle, "TEST/00002 - Build the Snowman");
            },
        },
        // Select the second employee and check only the right WO is shown.
        { trigger: ".o_mrp_employees_panel li:contains(Queen Elsa)" },
        ...stepUtils.enterPIN("41213"),
        {
            trigger: ".o_admin_user:contains(Queen Elsa)",
            run: () => {
                const currentEmployeeEl = document.querySelector(".o_admin_user div.fw-bold");
                helper.assert(currentEmployeeEl.innerText, "Queen Elsa");
                const records = document.querySelectorAll(".o_mrp_display_record");
                helper.assert(records.length, 1);
                const recordTitle = records[0].querySelector(".card-title>span").innerText;
                helper.assert(recordTitle, "TEST/00001 - Build the Snowman");
            },
        },
        // Select again the first employee and check again only its WO is displayed.
        { trigger: ".o_mrp_employees_panel li:contains(John Snow)" },
        {
            trigger: ".o_admin_user:contains(John Snow)",
            run: () => {
                const currentEmployeeEl = document.querySelector(".o_admin_user div.fw-bold");
                helper.assert(currentEmployeeEl.innerText, "John Snow");
                const records = document.querySelectorAll(".o_mrp_display_record");
                helper.assert(records.length, 1);
                const recordTitle = records[0].querySelector(".card-title>span").innerText;
                helper.assert(recordTitle, "TEST/00002 - Build the Snowman");
            },
        },
    ],
});

registry.category("web_tour.tours").add('test_generate_serials_in_shopfloor', {test: true, steps: () => [
    {
        content: 'Make sure workcenter is available',
        trigger: 'button:has(input[name="Assembly Line"])',
    },
    {
        content: 'Confirm workcenter',
        extra_trigger: 'button.active:has(input[name="Assembly Line"])',
        trigger: 'button:contains("Confirm")',
    },
    {
        content: 'Select workcenter',
        trigger: 'button.btn-light:contains("Assembly Line")',
    },
    {
        content: 'Open the wizard',
        trigger: '.o_mrp_record_line .text-truncate:contains("Register byprod")',
    },
    {
        content: 'Open the serials generation wizard',
        trigger: '.o_widget_generate_serials button',
    },
    {
        content: 'Input a serial',
        trigger: '#next_serial_0',
        run: 'text 00001',
    },
    {
        content: 'Generate the serials',
        trigger: 'button.btn-primary:contains("Generate")',
    },
    {
        content: 'Save and close the wizard',
        trigger: '.o_form_button_save:contains("Save")',
    },
    {
        content: 'Set production as done',
        trigger: 'button.btn-primary:contains("Mark as Done")',
    },
    {
        content: 'Close production',
        trigger: 'button.btn-primary:contains("Close Production")',
        isCheck: true,
    },
]})

registry.category("web_tour.tours").add('test_canceled_wo', {
    test: true, steps: () => [
        {
            content: 'Make sure workcenter is available',
            trigger: 'button:has(input[name="Assembly Line"])',
        },
        {
            content: 'Confirm workcenter',
            extra_trigger: 'button.active:has(input[name="Assembly Line"])',
            trigger: 'button:contains("Confirm")',
        },
        {
            content: 'Check MO',
            trigger: 'button.btn-light:contains("Assembly Line")',
            isCheck: true,
            run: () => {
                if (document.querySelectorAll("ul button:not(.btn-secondary)").length > 1)
                    throw new TourError("Multiple Workorders");
            }
        },
    ]
})

registry.category("web_tour.tours").add('test_updated_quality_checks', {test: true, steps: () => [
    {
        content: 'Make sure workcenter is available',
        trigger: 'button:has(input[name="Assembly Line"])',
    },
    {
        content: 'Confirm workcenter',
        extra_trigger: 'button.active:has(input[name="Assembly Line"])',
        trigger: 'button:contains("Confirm")',
    },
    {
        content: 'Select workcenter',
        trigger: 'button.btn-light:contains("Assembly Line")',
    },
    {
        content: 'Open register production',
        extra_trigger: '.o_control_panel_actions button.active:contains("Assembly Line")',
        trigger: '.o_mrp_record_line span:contains("Register Production")',
    },
    {
        content: 'Register production check',
        trigger: '.o_workorder_lot .btn.fa-plus',
        extra_trigger: '.o_workorder_lot span:contains("serial")',
    },
    { trigger: 'button[barcode_trigger="next"]' },
    {
        content: 'Quantity shown 1 of 1',
        extra_trigger: '.o_field_widget[name="qty_done"] input:propValue("1.00")',
        trigger: 'span[name="component_remaining_qty"]:contains("1.00")',
        isCheck: true,
    },
]})

registry.category("web_tour.tours").add("test_update_tracked_consumed_materials_in_shopfloor", {
    test: true,
    steps: () => [
        {
            trigger: "button:has(input[name='Lovely Workcenter'])",
            run: "click",
        },
        {
            trigger: "button.active:has(input[name='Lovely Workcenter'])",
            isCheck: true,
        },
        {
            trigger: "button:contains('Confirm')",
            run: "click",
        },
        {
            content: "Check that we are in the MO view",
            trigger: ".o_mrp_display_records button:contains('Lovely Workcenter')",
            isCheck: true,
        },
        {
            content: "Swap to the WO view of the Lovely Workcenter",
            trigger: "button.btn-light:contains('Lovely Workcenter')",
            run: "click",
        },
        {
            content: "Open register production",
            trigger: '.o_mrp_record_line span:contains("Register component")',
            run: "click",
        },
        {
            trigger: ".modal-header .modal-title:contains('Register component')",
            isCheck: true,
        },
        {
            content: "Register SN002",
            trigger: ".o_workorder_lot input",
            run: "text SN002",
        },
        {
            trigger: ".dropdown-item:contains('SN002')",
            run: "click",
        },
        {
            trigger: ".modal-header",
            run: "click",
        },
        {
            trigger: "button:contains('Continue consumption')",
            run: "click",
        },
        {
            content: "check that the quantity was correctly updated",
            trigger: "span[name='component_remaining_qty']:contains('1.00')",
            isCheck: true,
        },
        //  Register SN004 => not available so should take from WH/Stock
        {
            trigger: ".o_workorder_lot input",
            run: "text SN004",
        },
        {
            trigger: ".dropdown-item:contains('SN004')",
            run: "click",
        },
        {
            trigger: ".modal-header",
            run: "click",
        },
        {
            trigger: "button:contains('Continue consumption')",
            run: "click",
        },
        {
            trigger: ".o_field_widget[name='lot_id'] input:propValue('')",
            isCheck: true,
        },
        {
            content: "Register SN003",
            trigger: ".o_workorder_lot input",
            run: "text SN003",
        },
        {
            trigger: ".dropdown-item:contains('SN003')",
            run: "click",
        },
        {
            trigger: ".modal-header",
            run: "click",
        },
        {
            trigger: "button:contains('Validate')",
            run: "click",
        },
        {
            content: "Check that action buttons are disabled during the last click",
            trigger: ".modal-header",
            run: () => {
                const buttons = document.querySelectorAll(".modal-footer button");
                const disabledButtons = document.querySelectorAll(".modal-footer button:disabled");
                if (!buttons.length | (buttons.length != disabledButtons.length)) {
                    throw new TourError("Button not disabled");
                }
            },
        },
        {
            content: "Check that SN002 is well registered",
            trigger: ".o_mrp_record_line:contains('SN002')",
            isCheck: true,
        },
        {
            content: "Check that SN003 is well registered",
            trigger: ".o_mrp_record_line:contains('SN003')",
            isCheck: true,
        },
        {
            content: "Check that SN004 is well registered",
            trigger: ".o_mrp_record_line:contains('SN004')",
            isCheck: true,
        },
    ],
});

registry.category("web_tour.tours").add("test_under_consume_materials_in_shopfloor", {
    test: true,
    steps: () => [
        {
            trigger: "button:has(input[name='Lovely Workcenter'])",
            run: "click",
        },
        {
            trigger: "button.active:has(input[name='Lovely Workcenter'])",
            isCheck: true,
        },
        {
            trigger: "button:contains('Confirm')",
            run: "click",
        },
        {
            content: "Check that we are in the MO view",
            trigger: ".o_mrp_display_records button:contains('Lovely Workcenter')",
            isCheck: true,
        },
        {
            content: "Swap to the WO view of the Lovely Workcenter",
            trigger: "button.btn-light:contains('Lovely Workcenter')",
            run: "click",
        },
        {
            content: "Open register production",
            trigger: '.o_mrp_record_line span:contains("Register component")',
            run: "click",
        },
        {
            trigger: ".modal-header .modal-title:contains('Register component')",
            isCheck: true,
        },
        {
            trigger: ".o_field_widget[name='qty_done'] input",
            run: "click",
        },
        {
            trigger: ".o_field_widget[name='qty_done'] input",
            run: "text 3",
        },
        {
            trigger: ".modal-header",
            run: "click",
        },
        {
            trigger: "button:contains('Continue consumption')",
            run: "click",
        },
        {
            trigger: "span[name='component_remaining_qty']:contains('7.00')",
            isCheck: true,
        },
        {
            trigger: ".o_field_widget[name='qty_done'] input",
            run: "click",
        },
        {
            trigger: ".o_field_widget[name='qty_done'] input",
            run: "text 2",
        },
        {
            trigger: ".modal-header",
            run: "click",
        },
        {
            trigger: "button:contains('Validate')",
            run: "click",
        },
        {
            content: "Check that the componenet registration has been completed",
            trigger: ".btn:contains('Mark as Done')",
            isCheck: true,
        },
    ],
});
