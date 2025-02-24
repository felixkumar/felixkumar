/** @odoo-module **/

import tour from 'web_tour.tour';
import helper from 'mrp_workorder.tourHelper';

tour.register('test_add_component', {test: true}, [
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(2);
            helper.assertValidatedCheckLength(0);
            helper.assertQtyToProduce(1, 1);
            helper.assertCurrentCheck('Register Consumed Materials "Elon Musk"');
            helper.assertComponent('Elon Musk', 'readonly', 1, 1);
        }
    },
    {trigger: '.btn[name="button_start"]'},
    {
        trigger: '.o_workorder_icon_btn',
        extra_trigger: '.btn[name="button_pending"]',
    },
    {trigger: '.o_tablet_popups'},
    {trigger: '.btn:contains("Add Component")'},
    {trigger: '.modal-title:contains("Add Component")'},
    {
        trigger: "div.o_field_widget[name='product_id'] input ",
        position: 'bottom',
        run: 'text extra',
    }, {
        trigger: '.ui-menu-item > a:contains("extra")',
        in_modal: false,
        auto: true,
    }, {
        trigger: "div.o_field_widget[name='product_qty'] input",
        in_modal: true,
        position: 'bottom',
        run: 'text 3',
    },
    {trigger: '.btn-primary[name="add_product"]'},
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(3);
            helper.assertValidatedCheckLength(0);
            helper.assertQtyToProduce(1, 1);
            helper.assertCurrentCheck('Register Consumed Materials "extra"');
            helper.assertComponent('extra', 'editable', 3, 3);
        }
    }, {
        trigger: "div.o_field_widget[name='lot_id'] input ",
        position: 'bottom',
        run: 'text lot1',
    }, {
        trigger: '.ui-menu-item > a:contains("lot1")',
        in_modal: false,
        auto: true,
    }, {
        trigger: '.o_tablet_client_action',
        run: () => {
            helper.assertCheckLength(3);
            helper.assertValidatedCheckLength(0);
            helper.assertQtyToProduce(1, 1);
            helper.assertCurrentCheck('Register Consumed Materials "extra"');
            helper.assertComponent('extra', 'editable', 3, 3);
            helper.assert($('div.o_field_widget[name="lot_id"] input').val(), 'lot1');
        }
    },
    // go to Elon Musk step (second one since 'extra')
    {trigger: '.o_tablet_step:nth-child(2)'},
    {trigger: '.o_selected:contains("Elon")'},
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(3);
            helper.assertValidatedCheckLength(0);
            helper.assertQtyToProduce(1, 1);
            helper.assertCurrentCheck('Register Consumed Materials "Elon Musk"');
            helper.assertComponent('Elon Musk', 'readonly', 1, 1);
        }
    },
    // go to metal cylinder step
    {trigger: '.btn[name="action_next"]'},
    {trigger: 'div[name="component_id"]:contains("Metal")'},
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertComponent('Metal cylinder', 'editable', 2, 2);
            helper.assertCheckLength(3);
            helper.assertValidatedCheckLength(1);
            helper.assertQtyToProduce(1, 1);
            helper.assertCurrentCheck('Register Consumed Materials "Metal cylinder"');
        }
    }, {
        trigger: 'input[id="qty_done"]',
        position: 'bottom',
        run: 'text 1',
    }, {
        trigger: 'div.o_field_widget[name="lot_id"] input',
        position: 'bottom',
        run: 'text mc1',
    },
    {trigger: '.o_workorder_icon_btn'},
    {trigger: '.o_tablet_popups'},
    {trigger: '.btn:contains("Add By-product")'},
    {trigger: '.modal-title:contains("Add By-Product")'},
    {
        trigger: "div.o_field_widget[name='product_id'] input ",
        position: 'bottom',
        run: 'text extra-bp',
    }, {
        trigger: '.ui-menu-item > a:contains("extra-bp")',
        in_modal: false,
        auto: true,
    }, {
        trigger: "div.o_field_widget[name='product_qty'] input",
        in_modal: true,
        position: 'bottom',
        run: 'text 1',
    },
    {trigger: '.btn-primary[name="add_product"]'},
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(4);
            helper.assertValidatedCheckLength(1);
            helper.assertQtyToProduce(1, 1);
            helper.assertCurrentCheck('Register By-products "extra-bp"');
            helper.assertComponent('extra-bp', 'editable', 1, 1);
        }
    }, {
        trigger: "div.o_field_widget[name='lot_id'] input ",
        position: 'bottom',
        run: 'text lot2',
    }, {
        trigger: '.ui-menu-item > a:contains("lot2")',
        in_modal: false,
        auto: true,
    },
    {trigger: '.btn[name=action_next]'},
    {
        trigger: 'div[name="component_id"]:contains("Metal")',
        run: function () {
            helper.assertCheckLength(4);
            helper.assertValidatedCheckLength(2);
            helper.assertQtyToProduce(1, 1);
            helper.assertCurrentCheck('Register Consumed Materials "Metal cylinder"');
            helper.assertComponent('Metal cylinder', 'editable', 2, 2);
        }
    },
    {trigger: '.btn[name=action_next]'},
    // go back to the first not done check
    {
        trigger: 'div[name="component_id"]:contains("extra")',
        run: function () {
            helper.assertComponent('extra', 'editable', 3, 3);
            helper.assertCheckLength(4);
            helper.assertValidatedCheckLength(3);
            helper.assertQtyToProduce(1, 1);
            helper.assertCurrentCheck('Register Consumed Materials "extra"');
        }
    },
    {trigger: '.btn[name=action_next]'},
    // we have the rainbow man once
    {
        trigger: '.o_tablet_step:nth-child(5)',
        run: function () {
            helper.assertRainbow(true);
        }
    },
    {trigger: '.o_reward_rainbow_man'},
    {
        trigger: 'h1:contains("Good Job")',
        run: function () {
            helper.assertDoneButton(true);
        }
    },
    // we do not have it twice
    {trigger: '.o_tablet_step:nth-child(2)'},
    {
        trigger: 'div[name="component_id"]:contains("Elon")',
        run: function () {
            helper.assertCheckLength(5);
            helper.assertValidatedCheckLength(4);
            helper.assertQtyToProduce(1, 1);
            helper.assertCurrentCheck('Register Consumed Materials "Elon Musk"');
            helper.assertComponent('Elon Musk', 'readonly', 1, 0);
        }
    },
    {trigger: '.o_tablet_step:nth-child(5)'},
    {
        trigger: 'h1:contains("Good Job")',
        run: function () {
            helper.assertRainbow(false);
            helper.assertDoneButton(true);
        }
    },
    {
        trigger: "input[id='finished_lot_id']",
        position: 'bottom',
        run: 'text F0001',
    },
    {
        trigger: '.ui-menu-item > a:contains("F0001")',
        in_modal: false,
        auto: true,
    },
    {trigger: '.btn[name=do_finish]'},
    {trigger: '.o_searchview_input'},
]);

tour.register('test_add_step', {test: true}, [
    { trigger: '.o_tablet_client_action' },
    {
        trigger: 'input[id="qty_producing"]',
        position: 'bottom',
        run: 'text 1',
    },
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(2);
            helper.assertValidatedCheckLength(0);
            helper.assertQtyToProduce(1, 1);
            helper.assertCurrentCheck('Gather Magic Step');
        }
    },
    { trigger: '.btn[name="button_start"]' },
    {
        trigger: '.o_workorder_icon_btn',
        extra_trigger: '.btn[name="button_pending"]',
    },
    // add new step with title + instruction
    { trigger: '.o_tablet_popups' },
    { trigger: '.btn:contains("Add a Step")' },
    { trigger: '.modal-title:contains("Add a Step")' },
    {
        trigger: "div[name=title] input",
        position: 'bottom',
        run: 'text New Magical Step',
    }, {
        trigger: "div[name=note] p",
        position: 'bottom',
        run: 'text Do extra magic',
    },
    { trigger: '.btn-primary[name="add_check_in_chain"]' },
    // still on original step after adding new step
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(3);
            helper.assertQtyToProduce(1, 1);
            helper.assertCurrentCheck('Gather Magic Step');
        }
    },
    // go to new step + check that it's correct
    { trigger: '.o_tablet_step:nth-child(2)' },
    { trigger: '.o_selected:contains("New Magical Step")' },
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(3);
            helper.assertQtyToProduce(1, 1);
            helper.assertCurrentCheck("New Magical Step");
        }
    },
    { trigger: 'div[name=note]:contains("Do extra magic")' },
    { trigger: '.o_tablet_client_action' },
    // add new step with NO title + NO instruction
    { trigger: 'button[name=openMenuPopup]' },
    { trigger: '.o_tablet_popups' },
    { trigger: '.btn:contains("Add a Step")' },
    { trigger: '.modal-title:contains("Add a Step")' },
    { trigger: '.btn-primary[name="add_check_in_chain"]' },
    // go to new step + check that it's correct
    { trigger: '.o_tablet_step:nth-child(3)' },
    { trigger: '.o_selected:contains("instructions")' },
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(4);
            helper.assertQtyToProduce(1, 1);
            helper.assertCurrentCheck("instructions");
            helper.assert($('div[name=note]').text().trim(), '');
        }
    },
    // complete all steps + Close WO
    { trigger: '.o_tablet_client_action' },
    { trigger: '.o_tablet_step:nth-child(1)' },
    { trigger: '.o_selected:contains("Gather Magic Step")' },
    { trigger: 'button[name=action_next]' },
    { trigger: '.o_tablet_client_action' },
    { trigger: 'div[name=note]:contains("Do extra magic")' },
    { trigger: 'button[name=action_next]' },
    { trigger: '.o_tablet_client_action' },
    { trigger: '.o_selected:contains("instructions")' },
    { trigger: 'button[name=action_next]' },
    { trigger: '.o_tablet_client_action' },
    { trigger: 'div[name=note]:contains("Wave your hands in the air")' },
    { trigger: 'button[name=action_next]' },
    { trigger: 'button[name=do_finish]' },
    { trigger: '.o_searchview_input' },
]);

tour.register('test_remove_step', {test: true}, [
    { trigger: '.o_tablet_client_action' },
    {
        trigger: 'input[id="qty_producing"]',
        position: 'bottom',
        run: 'text 1',
    },
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(2);
            helper.assertValidatedCheckLength(0);
            helper.assertQtyToProduce(1, 1);
            helper.assertCurrentCheck('Gather Magic Step');
        }
    },
    { trigger: '.btn[name="button_start"]' },
    {
        trigger: '.o_workorder_icon_btn',
        extra_trigger: '.btn[name="button_pending"]',
    },
    // remove a step with a comment
    { trigger: '.o_tablet_popups' },
    { trigger: '.btn:contains("Delete this Step")' },
    { trigger: '.modal-title:contains("Remove Step")' },
    {
        trigger: "div[name=comment] input",
        position: 'bottom',
        run: 'text The magic is already within me',
    },
    { trigger: '.btn-primary[name="process"]' },
    // original step still shows even though it is "removed"
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(2);
            helper.assertValidatedCheckLength(0);
            helper.assertCurrentCheck('Gather Magic Step');
        }
    },
    // original current step is deleted => should be displayed differently when another step selected
    { trigger: '.o_tablet_step:nth-child(2)' },
    { trigger: '.o_selected:contains("Cast Magic Step")' },
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(2);
            helper.assertValidatedCheckLength(0);
            helper.assertCurrentCheck('Cast Magic Step');
        }
    },
    { trigger: '.o_deleted' },
    // return to first step to complete the step
    { trigger: '.o_selected:contains("Gather Magic Step")' },
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(2);
            helper.assertValidatedCheckLength(0);
            helper.assertCurrentCheck("Gather Magic Step");
        }
    },
    // go to second step + remove it without a comment
    { trigger: '.btn-primary[name="action_next"]' },
    { trigger: '.o_selected:contains("Cast Magic Step")' },
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(2);
            helper.assertValidatedCheckLength(1);
            helper.assertCurrentCheck("Cast Magic Step");
        }
    },
    { trigger: 'button[name=openMenuPopup]' },
    { trigger: '.o_tablet_popups' },
    { trigger: '.btn:contains("Delete this Step")' },
    { trigger: '.modal-title:contains("Remove Step")' },
    { trigger: '.btn-primary[name="process"]' },
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(2);
            helper.assertValidatedCheckLength(1);
            helper.assertCurrentCheck('Cast Magic Step');
        }
    },
    // add temporary new step in last position
    { trigger: 'button[name=openMenuPopup]' },
    { trigger: '.o_tablet_popups' },
    { trigger: '.btn:contains("Add a Step")' },
    { trigger: '.modal-title:contains("Add a Step")' },
    {
        trigger: "div[name=title] input",
        position: 'bottom',
        run: 'text Temporary Magic Step',
    },
    { trigger: '.btn-primary[name="add_check_in_chain"]' },
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(3);
            helper.assertValidatedCheckLength(1);
            helper.assertCurrentCheck('Cast Magic Step');
        }
    },
    { trigger: '.btn-primary[name="action_next"]' },
    { trigger: '.o_selected:contains("Temporary Magic Step")' },
    // last (and also added) step
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(3);
            helper.assertValidatedCheckLength(2);
            helper.assertCurrentCheck("Temporary Magic Step");
        }
    },
    // remove added step from PLM BoM
    { trigger: 'button[name=openMenuPopup]' },
    { trigger: '.o_tablet_popups' },
    { trigger: '.btn:contains("Delete this Step")' },
    { trigger: '.modal-title:contains("Remove Step")' },
    { trigger: '.btn-primary[name="process"]' },
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(3);
            helper.assertValidatedCheckLength(2);
            helper.assertCurrentCheck("Temporary Magic Step");
        }
    },
    // remove added step from WO
    { trigger: 'button[name=openMenuPopup]' },
    { trigger: '.o_tablet_popups' },
    { trigger: '.btn:contains("Delete this Step")' },
    { trigger: '.modal-title:contains("Remove Step")' },
    { trigger: '.btn-primary[name="process"]' },
    // should automatically go to summary page
    { trigger: 'button[name=do_finish]' },
    { trigger: '.o_searchview_input' },
]);

tour.register('test_update_step', {test: true}, [
    { trigger: '.o_tablet_client_action' },
    {
        trigger: 'input[id="qty_producing"]',
        position: 'bottom',
        run: 'text 1',
    },
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(2);
            helper.assertValidatedCheckLength(0);
            helper.assertQtyToProduce(1, 1);
            helper.assertCurrentCheck('Gather Magic Step');
        }
    },
    { trigger: '.btn[name="button_start"]' },
    {
        trigger: '.o_workorder_icon_btn',
        extra_trigger: '.btn[name="button_pending"]',
    },
    // update step with NO title + NO instruction + NO comment
    {trigger: 'button[name=openMenuPopup]'},
    {trigger: '.o_tablet_popups'},
    {trigger: '.btn:contains("Update Instruction")'},
    {trigger: '.modal-title:contains("Update Instruction")'},
    {
        trigger: "div[name=title] input",
        position: 'bottom',
        run: function () {
            $("input").val('');
        },
    },
    { trigger: '.btn-primary[name="process"]' },
    {
        content: "Check that step updated correctly (i.e. title is unchanged when blank title submitted)",
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCurrentCheck('Gather Magic Step');
            helper.assert($('div[name=note]').text().trim(), '');
        }
    },
    // update step with title + instruction + comment
    {trigger: 'button[name=openMenuPopup]'},
    {trigger: '.o_tablet_popups'},
    {trigger: '.btn:contains("Update Instruction")'},
    {trigger: '.modal-title:contains("Update Instruction")'},
    {
        trigger: "div[name=title] input",
        position: 'bottom',
        run: 'text Pre-magic Step',
    }, {
        trigger: "div[name=note] p",
        position: 'bottom',
        run: 'text This is the step before magic is done',
    },
    {
        trigger: "div[name=comment] input",
        position: 'bottom',
        run: 'text This step was inaccurate',
    },
    { trigger: '.btn-primary[name="process"]' },
    {
        content: "Check that step updated correctly (i.e. title is unchanged when blank title submitted)",
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCurrentCheck('Pre-magic Step');
            helper.assert($('div[name=note]').text().trim(), 'This is the step before magic is done');
        }
    },
    // go to second step + remove it without a comment
    { trigger: '.btn-primary[name="action_next"]' },
    { trigger: '.o_selected:contains("Cast Magic Step")' },
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(2);
            helper.assertValidatedCheckLength(1);
            helper.assertCurrentCheck("Cast Magic Step");
        }
    },
    { trigger: 'button[name=openMenuPopup]' },
    { trigger: '.o_tablet_popups' },
    { trigger: '.btn:contains("Delete this Step")' },
    { trigger: '.modal-title:contains("Remove Step")' },
    { trigger: '.btn-primary[name="process"]' },
    // update instructions for step that is missing from plm bom
    {
        trigger: '.o_tablet_client_action',
        run: function () {
            helper.assertCheckLength(2);
            helper.assertValidatedCheckLength(1);
            helper.assertCurrentCheck("Cast Magic Step");
        }
    },
    {trigger: 'button[name=openMenuPopup]'},
    {trigger: '.o_tablet_popups'},
    {trigger: '.btn:contains("Update Instruction")'},
    {trigger: '.modal-title:contains("Update Instruction")'},
    {
        trigger: "div[name=note] p",
        position: 'bottom',
        run: 'text What will happen with this update?!',
    },
    { trigger: '.btn-primary[name="process"]' },
    { trigger: '.btn-primary[name="action_next"]' },
    { trigger: 'button[name=do_finish]' },
    { trigger: '.o_searchview_input' },
]);

tour.register('test_serial_tracked_and_register', {test: true}, [
    {
        trigger: '.o_tablet_client_action',
        run: function() {
            helper.assert($('input[id="finished_lot_id"]').val(), 'Magic Potion_1');
        }
    },
    { trigger: '.o_tablet_client_action' },
    {
        // sn should have been updated to match move_line sn
        trigger: 'div.o_field_widget[name="lot_id"] input ',
        run: function() {
            helper.assert($('input[id="lot_id"]').val(), 'Magic_2');
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
            helper.assert($('input[id="lot_id"]').val(), 'Magic_3');
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
            helper.assert($('input[id="finished_lot_id"]').val(), 'Magic Potion_2');
        }
    },
    { trigger: '.o_tablet_client_action' },
    { trigger: '.btn-primary[name="action_next"]' },
    { trigger: 'button[name=do_finish]' },
    { trigger: '.o_searchview_input' },
]);
