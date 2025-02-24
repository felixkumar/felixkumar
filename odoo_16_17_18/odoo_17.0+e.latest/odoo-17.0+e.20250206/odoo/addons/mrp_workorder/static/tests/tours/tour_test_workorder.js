/** @odoo-module **/

import { registry } from "@web/core/registry";
import helper from "@mrp_workorder/../tests/tours/tour_helper_mrp_workorder";


registry.category("web_tour.tours").add('test_serial_tracked_and_register', {test: true, steps: () => [
    {
        trigger: '.o_tablet_client_action',
        run: function() {
            helper.assert($('input[id="finished_lot_id_0"]').val(), 'Magic Potion_1');
        }
    },
    { trigger: '.o_tablet_client_action' },
    {
        // sn should have been updated to match move_line sn
        trigger: 'div.o_field_widget[name="lot_id"] input ',
        run: function() {
            helper.assert($('input[id="lot_id_0"]').val(), 'Magic_2');
        }
    },
    { trigger: '.o_tablet_client_action' },
    { trigger: '.btn[name="button_start"]' },
    {
        trigger: 'div.o_field_widget[name="lot_id"] input ',
        position: 'bottom',
        run: 'text Magic_3',
    },
    { trigger: '.ui-menu-item > a:contains("Magic_3")' },
    { trigger: '.o_tablet_client_action' },
    {
        trigger: 'div.o_field_widget[name="finished_lot_id"] input ',
        position: 'bottom',
        run: 'text Magic Potion_2',
    },
    { trigger: '.ui-menu-item > a:contains("Magic Potion_2")' },
    {
        // comp sn shouldn't change when produced sn is changed
        trigger: 'div.o_field_widget[name="lot_id"] input',
        run: function() {
            helper.assert($('input[id="lot_id_0"]').val(), 'Magic_3');
        }
    },
    { trigger: '.o_tablet_client_action' },
    {
        trigger: 'div.o_field_widget[name="lot_id"] input ',
        position: 'bottom',
        run: 'text Magic_1',
    },
    { trigger: '.ui-menu-item > a:contains("Magic_1")' },
    { trigger: '.o_tablet_client_action' },
    {
        // produced sn shouldn't change when comp sn is changed
        trigger: 'div.o_field_widget[name="finished_lot_id"] input ',
        run: function() {
            helper.assert($('input[id="finished_lot_id_0"]').val(), 'Magic Potion_2');
        }
    },
    { trigger: '.o_tablet_client_action' },
    { trigger: '.btn-primary[name="action_next"]' },
    { trigger: 'button[name=do_finish]' },
    { trigger: '.o_searchview_input' },
]});

registry.category("web_tour.tours").add('test_access_shop_floor_with_multicomany', {
    test: true,
    url: '/web#cids=1&action=menu',
    steps: () => [{
        content: 'Select Shop Floor app',
        trigger: 'a.o_app:contains("Shop Floor")',
    },{
        content: 'Close the select workcenter panel',
        trigger: 'button.btn-close',
    },{
        content: 'Check that we entered the app with first company',
        trigger: 'div.o_mrp_display',
    },{
        content: 'Go back to home menu',
        trigger: '.o_home_menu',
    },{
        content: 'Click on switch  company menu',
        trigger: '.o_switch_company_menu button',
    },{
        content: 'Select another company',
        trigger: 'div[role="button"]:contains("Test Company")',
    },{
        context: 'Check that we switched companies',
        trigger: '.o_switch_company_menu button span:contains("Test Company")',
        isCheck: true,
    },{
        content: 'Select Shop Floor app',
        trigger: 'a.o_app:contains("Shop Floor")',
    },{
        content: 'Close the select workcenter panel again',
        trigger: '.btn-close',
    },{
        content: 'Check that we entered the app with second company',
        trigger: 'div.o_mrp_display',
    },{
        content: 'Check that the WO is not clickable',
        trigger: 'div.o_mrp_display_record.o_disabled',
        isCheck: true,
    }]
})

registry.category("web_tour.tours").add("test_add_component_from_shop_foor", {
    test: true,
    steps: () => [
        {
            trigger: "button:has(input[name='Nuclear Workcenter'])",
            run: "click",
        },
        {
            trigger: "button.active:has(input[name='Nuclear Workcenter'])",
            isCheck: true,
        },
        {
            trigger: "button:contains('Confirm')",
            run: "click",
        },
        {
            context: "Check that we are in the MO view",
            trigger: ".o_mrp_display_records button:contains('Nuclear Workcenter')",
            isCheck: true,
        },
        {
            context: "Add Wood to the MO components",
            trigger: ".o_mrp_display_record .card-footer button.btn-light.py-3",
        },
        {
            trigger: ".o_mrp_menu_dialog",
            isCheck: true,
        },
        {
            trigger: "button:contains('Add Component')",
            run: "click",
        },
        {
            trigger: ".o_cell:has(div[name='product_id']) input.o_input",
            run: "text Super Wood",
        },
        {
            trigger: ".dropdown-item:contains('Super Wood')",
        },
        {
            trigger: "header.modal-header",
            run: "click",
        },
        {
            trigger: "button:contains('Add Component')",
            run: "click",
        },
        {
            context: "Check that the Wood is visible on the MO",
            trigger: ".o_mrp_record_line:contains('Super Wood')",
            isCheck: true,
        },
        {
            context: "Swap to the WO view of the Nuclear Workcenter",
            trigger: "button.btn-light:contains('Nuclear Workcenter')",
            run: "click",
        },
        {
            context: "Check that we are in the WO view",
            trigger: ".o_mrp_display_records .card-header .card-title:contains('Super Operation')",
            isCheck: true,
        },
        {
            context: "Add Courage to the WO components",
            trigger: ".o_mrp_display_record .card-footer button.btn-light.py-3",
            run: "click",
        },
        {
            trigger: ".o_mrp_menu_dialog",
            isCheck: true,
        },
        {
            trigger: "button:contains('Add Component')",
            run: "click",
        },
        {
            trigger: ".o_cell:has(div[name='product_id']) input.o_input",
            run: "text Courage",
        },
        {
            trigger: ".dropdown-item:contains('Courage')",
            run: "click",
        },
        {
            trigger: "header.modal-header",
            run: "click",
        },
        {
            trigger: "button:contains('Add Component')",
            run: "click",
        },
        {
            context: "Check that the Courage is visible on the WO",
            trigger: ".o_mrp_record_line span:contains('Courage')",
            isCheck: true,
        },
        {
            context: "Go back to the MO",
            trigger: "button.btn:contains('All MO')",
            run: "click",
        },
        {
            context: "Check that we are in the MO view",
            trigger: ".o_mrp_display_records button:contains('Nuclear Workcenter')",
            isCheck: true,
        },
        {
            context: "Check that the Courage is visible on the MO",
            trigger: ".o_mrp_record_line span:contains('Courage')",
            isCheck: true,
        },
    ],
});

registry
    .category("web_tour.tours")
    .add("test_add_component_from_shop_foor_in_multi_step_manufacturing", {
        test: true,
        steps: () => [
            {
                trigger: "button:has(input[name='Nuclear Workcenter'])",
                run: "click",
            },
            {
                trigger: "button.active:has(input[name='Nuclear Workcenter'])",
                run: () => {},
            },
            {
                trigger: "button:contains(Confirm)",
                run: "click",
            },
            {
                context: "Check that we are in the MO view",
                trigger: ".o_mrp_display_records button:contains(Nuclear Workcenter)",
                run: () => {},
            },
            {
                context: "Add Wood to the MO components",
                trigger: ".o_mrp_display_record .card-footer button.btn-light.py-3",
                run: "click",
            },
            {
                trigger: ".o_mrp_menu_dialog",
                run: () => {},
            },
            {
                trigger: "button:contains(Add Component)",
                run: "click",
            },
            {
                trigger: ".o_cell:has(div[name='product_id']) input.o_input",
                run: "text Courage",
            },
            {
                trigger: ".dropdown-item:contains(Courage)",
                run: "click",
            },
            {
                trigger: "header.modal-header",
                run: "click",
            },
            {
                trigger: "button:contains(Add Component)",
                run: "click",
            },
            {
                context: "Check that the Wood is visible on the MO",
                trigger: ".o_mrp_record_line:contains(Courage)",
                run: () => {},
            },
        ],
    });
