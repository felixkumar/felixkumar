/** @odoo-module */

import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("test_operation_quality_check_barcode", {
    test: true,
    steps: () => [
        {
            trigger: ".button_operations",
        },
        {
            trigger: ".o_barcode_picking_type:has(.o_kanban_record_title:contains('Receipts'))",
        },
        {
            trigger: "button.o-kanban-button-new",
        },
        {
            trigger: ".o_barcode_lines",
            run: "scan product1",
        },
        {
            trigger: ".fa-pencil",
        },
        {
            trigger: ".o_digipad_button.o_increase",
        },
        {
            trigger: ".o_save",
        },
        {
            trigger: ".o_barcode_lines",
            run() {},
        },
        {
            trigger: ".o_barcode_lines",
            run: "scan product2",
        },
        {
            trigger:
                ".o_barcode_line:has(.o_barcode_line_title:contains(product2)) button.o_add_quantity",
        },
        {
            trigger: ".o_validate_page",
        },
        {
            trigger: ".modal-content:has(.modal-header:contains(product 1)) button[name=do_pass]",
        },
        {
            trigger: ".modal-content:has(.modal-header:contains(product 2)) button[name=do_fail]",
        },
        {
            trigger: ".o_validate_page",
        },
        {
            trigger: ".o_notification.border-success",
            run() {},
        },
    ],
});
