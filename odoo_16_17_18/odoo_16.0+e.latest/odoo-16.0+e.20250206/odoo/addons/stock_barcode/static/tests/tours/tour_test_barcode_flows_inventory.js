/** @odoo-module */

import helper from 'stock_barcode.tourHelper';
import tour from 'web_tour.tour';

tour.register('test_inventory_adjustment', {test: true}, [

    {
        trigger: '.button_inventory',
    },

    {
        trigger: '.o_scan_message.o_scan_product',
        run: function () {
            helper.assertScanMessage('scan_product');
            helper.assertValidateVisible(true);
            helper.assertValidateIsHighlighted(false);
            helper.assertValidateEnabled(false);
        }
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan product1',
    },
    {
        trigger: '.o_barcode_line',
        run: function () {
            // Checks the product code and name are on separate lines.
            const $line = helper.getLine({barcode: 'product1'});
            helper.assert($line.find('.o_barcode_line_details > .o_barcode_line_title > .o_barcode_product_ref').length, 1);
            helper.assert($line.find('.o_barcode_line_details .product-label').length, 1);
        }
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan product1',
    },

    {
        trigger: '.o_edit',
    },

    {
        trigger: '.o_field_widget[name="inventory_quantity"]',
        run: function () {
            helper.assertFormQuantity('2');
        }
    },

    {
        trigger: '.o_save',
    },

    {
        trigger: '.o_barcode_line',
        run: function () {
            // Checks the product code and name are on separate lines.
            const $line = helper.getLine({barcode: 'product1'});
            helper.assert($line.find('.o_barcode_line_details > .o_barcode_line_title > .o_barcode_product_ref').length, 1);
            helper.assert($line.find('.o_barcode_line_details .product-label').length, 1);
        }
    },

    {
        trigger: '.o_add_line',
    },

    {
        trigger: ".o_field_widget[name=product_id] input",
        run: 'text product2',
    },

    {
        trigger: ".ui-menu-item > a:contains('product2')",
    },

    {
        trigger: ".o_field_widget[name=inventory_quantity] input",
        run: 'text 2',
    },

    {
        trigger: '.o_save',
    },

    {
        extra_trigger: '.o_scan_message.o_scan_product',
        trigger: '.o_barcode_line',
        run: 'scan O-BTN.validate',
    },

    {
        trigger: '.o_stock_barcode_main_menu',
    },

    {
        trigger: '.o_notification.border-success',
        run: function () {
            helper.assertErrorMessage('The inventory adjustment has been validated');
        },
    },
]);

tour.register('test_inventory_adjustment_dont_update_location', {test: true}, [
    { trigger: '.button_inventory' },
    {
        trigger: '.o_barcode_client_action',
        run: function () {
            helper.assertLinesCount(2);
            const [line1, line2] = helper.getLine({ barcode: 'product1' });
            helper.assertLineQuantityOnReservedQty(0, '0 / 5');
            helper.assertLineQuantityOnReservedQty(1, '0 / 5');
            helper.assertLineSourceLocation(line1, "WH/Stock");
            helper.assertLineSourceLocation(line2, "WH/Stock/Section 2");
        }
    },
    // Scan WH/Stock/Section 1.
    { trigger: '.o_barcode_client_action', run: "scan LOC-01-01-00" },
    { trigger: '.o_barcode_line:first-child' },
    { trigger: '.o_barcode_line.o_selected button.o_add_quantity' },
    {
        trigger: 'button.o_remove_unit:not([disabled])',
        run: function () {
            helper.assertLinesCount(2);
            const selectedLine = document.querySelector(".o_barcode_line.o_selected");
            helper.assertLineQuantityOnReservedQty(0, '1 / 5');
            helper.assertLineSourceLocation(selectedLine, "WH/Stock");
        }
    },
    // Scans product1 -> A new line for this product should be created in Section 1.
    { trigger: '.o_barcode_client_action', run: "scan product1" },
    {
        trigger: '.o_barcode_line:nth-child(3)',
        run: function () {
            helper.assertLinesCount(3);
            const selectedLine = document.querySelector(".o_barcode_line.o_selected");
            helper.assertLineQuantityOnReservedQty(0, '1 / 5');
            helper.assertLineSourceLocation(selectedLine, "WH/Stock/Section 1");
        }
    },
    { trigger: '.o_apply_page.btn-success' },
    { trigger: '.o_notification.border-success' },
]);

tour.register('test_inventory_adjustment_multi_company', {test: true}, [
    // Open the company switcher.
    { trigger: ".o_switch_company_menu > button" },
    // Ensure the first company is selected and open the Barcode App, then the Inventory Adjustment.
    {
        extra_trigger: ".o_switch_company_menu .oe_topbar_name:contains('Comp A')",
        trigger: "[data-menu-xmlid='stock_barcode.stock_barcode_menu'] > .o_app_icon",
    },
    { trigger: "button.button_inventory" },
    // Scan product1 and product_no_company, they should be added in the inventory adj.
    { trigger: ".o_barcode_client_action", run: "scan product1" },
    { trigger: ".o_barcode_line[data-barcode='product1']", run: "scan product_no_company" },
    // Try to scan product2 who belongs to the second company -> Should not be found.
    { trigger: ".o_barcode_line[data-barcode='product_no_company']", run: "scan product2" },
    { trigger: ".o_notification.border-danger button.o_notification_close" },
    {
        trigger: ".o_barcode_client_action",
        run: function() {
            helper.assertLinesCount(2);
        }
    },
    // Validate the Inventory Adjustment.
    { trigger: ".o_apply_page.btn-success" },

    // Go back on the App Switcher and change the company.
    { trigger: ".o_stock_barcode_main_menu a.o_stock_barcode_menu" },
    { trigger: ".o_switch_company_menu > button" },
    { trigger: ".o_switch_company_menu .company_label:contains('Comp B')" },
    // Open again the Barcode App then the Inventory Adjustment.
    {
        extra_trigger: ".o_switch_company_menu .oe_topbar_name:contains('Comp B')",
        trigger: "[data-menu-xmlid='stock_barcode.stock_barcode_menu'] > .o_app_icon",
     },
    { trigger: "button.button_inventory" },
    // Scan product2 and product_no_company, they should be added in the inventory adj.
    { trigger: ".o_barcode_client_action", run: "scan product2" },
    { trigger: ".o_barcode_line[data-barcode='product2']", run: "scan product_no_company" },
    // Try to scan product1 who belongs to the first company -> Should not be found.
    { trigger: ".o_barcode_line[data-barcode='product_no_company']", run: "scan product1" },
    { trigger: ".o_notification.border-danger button.o_notification_close" },
    {
        trigger: ".o_barcode_client_action",
        run: function() {
            helper.assertLinesCount(2);
        }
    },
    // Validate the Inventory Adjustment.
    { trigger: '.o_barcode_line', run: 'scan O-BTN.validate' },
    {
        trigger: '.o_stock_barcode_main_menu',
        extra_trigger: '.o_notification.border-success',
        run: function () {
            helper.assertErrorMessage('The inventory adjustment has been validated');
        },
    },
]);

tour.register('test_inventory_adjustment_multi_location', {test: true}, [

    {
        trigger: '.button_inventory',
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan LOC-01-00-00'
    },

    {
        trigger: '.o_scan_message:contains("WH/Stock")',
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan product1',
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan product1',
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan product2',
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan LOC-01-01-00'
    },

    {
        trigger: '.o_scan_message:contains("WH/Stock/Section 1")',
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan product2',
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan LOC-01-02-00'
    },

    {
        trigger: '.o_scan_message:contains("WH/Stock/Section 2")',
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan product1',
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan O-BTN.validate',
    },

    {
        trigger: '.o_stock_barcode_main_menu',
        run: function () {
            helper.assertErrorMessage('The inventory adjustment has been validated');
        },
    },
]);

tour.register('test_inventory_adjustment_tracked_product', {test: true}, [

    {
        trigger: '.button_inventory',
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan productlot1',
    },

    {
        trigger: '.o_barcode_line:contains("productlot1")',
        run: 'scan lot1',
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan lot1',
    },

    {
        trigger: '.o_barcode_line.o_selected .qty-done:contains(2)',
        run: 'scan productserial1',
    },

    {
        trigger: '.o_barcode_line:contains("productserial1")',
        run: 'scan serial1',
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan serial1',
    },

    {
        trigger: '.o_notification.border-danger',
        run: function () {
            // Check that other lines is correct
            let $line = helper.getLine({barcode: 'productserial1'});
            helper.assertLineQty($line, "1");
            helper.assert($line.find('.o_line_lot_name').text().trim(), 'serial1');
            $line = helper.getLine({barcode: 'productlot1'});
            helper.assertLineQty($line, "2");
            helper.assert($line.find('.o_line_lot_name').text().trim(), 'lot1');
            helper.assertErrorMessage('The scanned serial number is already used.');
        },
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan serial2',
    },
    { trigger: '.o_barcode_line.o_selected .btn.o_toggle_sublines .fa-caret-down' },

    {
        trigger: '.o_barcode_line:contains("serial2")',
        run: 'scan productlot1',
    },

    {
        trigger: '.o_barcode_line:contains("productlot1")',
        run: 'scan lot1',
    },

    {
        trigger: '.o_barcode_line .qty-done:contains(3)',
        run: 'scan productserial1',
    },

    {
        trigger: '.o_barcode_line:contains("productserial1")',
        run: 'scan serial3',
    },

    {
        trigger: ':contains("productserial1") .o_sublines .o_barcode_line:contains("serial3")',
        run: function () {
            helper.assertLinesCount(2);
            helper.assertSublinesCount(3);
        },
    },

    // Edit a line to trigger a save.
    {
        trigger: '.o_add_line',
    },

    {
        trigger: '.o_field_widget[name="product_id"]',
    },
    {
        trigger: '.o_discard',
    },

    // Scan tracked by lots product, then scan new lots.
    {
        trigger: '.o_sublines .o_barcode_line:nth-child(3)',
        run: function () {
            helper.assertLinesCount(2);
            helper.assertSublinesCount(3);
        },
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan productlot1',
    },
    {
        trigger: '.o_barcode_line.o_selected:contains("productlot1")',
        run: 'scan lot2',
    },
    { trigger: '.o_barcode_line.o_selected .btn.o_toggle_sublines .fa-caret-down' },
    {
        trigger: '.o_barcode_line .o_barcode_line:contains("lot2")',
        run: 'scan lot3',
    },

    // Must have 6 lines in two groups: lot1, lot2, lot3 and serial1, serial2, serial3.
    // Grouped lines for `productlot1` should be unfolded.
    {
        trigger: '.o_barcode_line:contains("productlot1") .o_sublines>.o_barcode_line.o_selected:contains("lot3")',
        run: function () {
            helper.assertLinesCount(2);
            helper.assertSublinesCount(3);
        }
    },
    ...tour.stepUtils.validateBarcodeForm(),

    {
        trigger: '.o_stock_barcode_main_menu',
        run: function () {
            helper.assertErrorMessage('The inventory adjustment has been validated');
        },
    },
]);

tour.register('test_inventory_adjustment_tracked_product_multilocation', {test: true}, [
    { trigger: '.button_inventory' },
    {
        trigger: '.o_barcode_line',
        run: function() {
            const [line1, line2] = helper.getLine({barcode: 'productlot1'});
            helper.assertLineSourceLocation(line1, "WH/Stock/Section 1");
            helper.assertLineQuantityOnReservedQty(0, "3 / 3");
            helper.assertLineSourceLocation(line2, "WH/Stock/Section 2");
            helper.assertLineQuantityOnReservedQty(1, "0 / 5");
        }
    },
    // Scans Section 1 then scans productlot1.
    { trigger: '.o_barcode_line', run: 'scan LOC-01-01-00' },
    {
        trigger: '.o_barcode_line:first-child [name=source_location].o_highlight',
        run: 'scan lot1',
    },
    {
        trigger: '.o_barcode_line:first-child.o_selected',
        run: function() {
            const [line1, line2] = helper.getLine({barcode: 'productlot1'});
            helper.assertLineSourceLocation(line1, "WH/Stock/Section 1");
            helper.assertLineQuantityOnReservedQty(0, "4 / 3");
            helper.assertLineSourceLocation(line2, "WH/Stock/Section 2");
            helper.assertLineQuantityOnReservedQty(1, "0 / 5");
        }
    },
]);

tour.register('test_inventory_adjustment_tracked_product_permissive_quants', {test: true}, [

    {
        trigger: '.button_inventory',
    },

    // Scan a product tracked by lot that has a quant without lot_id, then scan a product's lot.
    {
        trigger: '.o_barcode_client_action',
        run: 'scan productlot1',
    },
    {
        trigger: '.o_barcode_line:contains("productlot1")',
        run: 'scan lot1',
    },
    {
        trigger: '.o_barcode_client_action',
        run: 'scan lot1',
    },
    { trigger: '.o_barcode_line.o_selected .btn.o_toggle_sublines .fa-caret-down' },
    // Must have 2 lines in one group: one without lot and one with lot1.
    // Grouped lines for `productlot1` should be unfolded.
    {
        trigger: '.o_sublines .o_barcode_line.o_selected:contains("lot1") .qty-done:contains(2)',
        run: function () {
            helper.assertLinesCount(1);
            helper.assertSublinesCount(2);
        }
    },

    {
        trigger: '.o_barcode_line .o_barcode_line:not(:contains("lot1")) .o_line_button.o_set.o_difference'
    },
    {
        trigger: '.o_sublines .o_barcode_line:not(:contains("lot1")) .o_line_button.o_set:not(.o_difference)'
    },

    {
        trigger: '.o_sublines .o_barcode_line:not(:contains("lot1")) .o_line_button.o_set .fa-check',
        run: 'scan O-BTN.validate',
    },
    ...tour.stepUtils.validateBarcodeForm(),

    {
        trigger: '.o_stock_barcode_main_menu',
        run: function () {
            helper.assertErrorMessage('The inventory adjustment has been validated');
        },
    },
]);

tour.register('test_inventory_create_quant', {test: true}, [
    { trigger: '.button_inventory' },
    {
        trigger: '.o_barcode_client_action',
        run: function () {
            helper.assertLinesCount(0);
        }
    },

    // Scans product 1: must have 1 quantity and buttons +1/-1 must be visible.
    { trigger: '.o_barcode_client_action', run: 'scan product1' },
    {
        trigger: '.o_barcode_client_action .o_barcode_line',
        run: function () {
            helper.assertLinesCount(1);
            const $line = helper.getLine({barcode: 'product1'});
            helper.assertLineIsHighlighted($line, true);
            helper.assertLineQty($line, '1');
            helper.assertButtonIsVisible($line, 'add_quantity');
            helper.assertButtonIsVisible($line, 'remove_unit');
        }
    },

    // Edits the line to set the counted quantity to zero.
    { trigger: '.o_edit' },
    {
        trigger: '.o_field_widget[name="product_id"]',
        run: function() {
            helper.assertFormQuantity("1");
        },
    },
    {
        trigger: '.o_field_widget[name=inventory_quantity] input',
        run: 'text 0',
    },
    { trigger: '.o_save' },
    {
        trigger: '.o_barcode_client_action .o_barcode_line',
        run: function () {
            helper.assertLinesCount(1);
            const $line = helper.getLine({barcode: 'product1'});
            helper.assertLineQty($line, '0');
        }
    },
]);

tour.register('test_inventory_nomenclature', {test: true}, [

    {
        trigger: '.button_inventory',
    },

    {
        trigger: '.o_barcode_client_action',
        run: function() {
            helper.assertScanMessage('scan_product');
        },
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan 2145631123457', // 12.345 kg
    },

    {
        trigger: '.product-label:contains("product_weight")'
    },
    ...tour.stepUtils.validateBarcodeForm(),
    {
        trigger: '.o_stock_barcode_main_menu',
        run: function () {
            helper.assertErrorMessage('The inventory adjustment has been validated');
        },
    },
]);

tour.register('test_inventory_package', {test: true}, [

    {
        trigger: '.button_inventory',
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan PACK001',
    },

    {
        trigger: '.o_barcode_line:contains("product2") .o_edit',
    },

    {
        trigger: '[name="inventory_quantity"] input',
        run: 'text 21'
    },

    {
        trigger: '.o_save',
    },

    {
        trigger: '.o_apply_page',
    },

    {
        trigger: '.o_notification.border-success',
        run: function () {
            helper.assertErrorMessage('The inventory adjustment has been validated');
        },
    },

    {
        trigger: '.o_stock_barcode_main_menu',
    },
]);

tour.register('test_inventory_packaging', {test: true}, [
    { trigger: '.button_inventory' },
    // Scans a packaging when there is no existing quant for its product.
    { trigger: '.o_barcode_client_action', run: 'scan pack007' },
    {
        trigger: '.o_barcode_line',
        run: function() {
            const $line = helper.getLine({ barcode: "product1"});
            helper.assertLineQty($line, "15");
        }
    },
    { trigger: '.o_apply_page' },
    { trigger: '.o_notification.border-success' },
    { trigger: '.button_inventory' },
    // Scans a packaging when a quant for its product exists.
    {
        trigger: '.o_barcode_client_action',
        run: 'scan pack007',
    },
    // Verifies it takes the packaging's quantity.
    {
        extra_trigger: '.o_barcode_line .qty-done:contains(15)',
        trigger: '.o_apply_page',
    },
    { trigger: '.o_notification.border-success' },
]);

tour.register('test_inventory_owner_scan_package', {test: true}, [
    {
        trigger: '.button_inventory',
    },
    {
        trigger: '.o_barcode_client_action',
        run: 'scan P00001',
    },
    {
        trigger: '.o_barcode_client_action:contains("P00001")',
    },
    {
        trigger: '.o_barcode_client_action:contains("Azure Interior")',
    },
    ...tour.stepUtils.validateBarcodeForm(),
]);

tour.register('test_inventory_using_buttons', {test: true}, [
    { trigger: '.button_inventory' },

    // Scans product 1: must have 1 quantity and buttons +1/-1 must be visible.
    { trigger: '.o_barcode_client_action', run: 'scan product1' },
    {
        trigger: '.o_barcode_client_action .o_barcode_line',
        run: function () {
            helper.assertLinesCount(1);
            const $line = helper.getLine({barcode: 'product1'});
            helper.assertLineIsHighlighted($line, true);
            helper.assertLineQty($line, '1');
            helper.assertButtonIsVisible($line, 'add_quantity');
            helper.assertButtonIsVisible($line, 'remove_unit');
        }
    },
    // Clicks on -1 button: must have 0 quantity, -1 still visible but disabled.
    { trigger: '.o_remove_unit' },
    {
        trigger: '.o_barcode_line:contains("0")',
        run: function () {
            helper.assertLinesCount(1);
            const $line = helper.getLine({barcode: 'product1'});
            helper.assertLineIsHighlighted($line, true);
            helper.assertLineQty($line, '0');
            helper.assertButtonIsVisible($line, 'add_quantity');
            helper.assertButtonIsVisible($line, 'remove_unit');
            const decrementButton = document.querySelector('.o_line_button.o_remove_unit');
            helper.assert(decrementButton.hasAttribute('disabled'), true);
        }
    },
    // Clicks on +1 button: must have 1 quantity, -1 must be enabled now.
    { trigger: '.o_add_quantity' },
    {
        trigger: '.o_barcode_line .qty-done:contains("1")',
        run: function () {
            helper.assertLinesCount(1);
            const $line = helper.getLine({barcode: 'product1'});
            helper.assertLineIsHighlighted($line, true);
            helper.assertLineQty($line, '1');
            helper.assertButtonIsVisible($line, 'add_quantity');
            helper.assertButtonIsVisible($line, 'remove_unit');
            const decrementButton = document.querySelector('.o_line_button.o_remove_unit');
            helper.assert(decrementButton.hasAttribute('disabled'), false);
        }
    },

    // Scans productserial1: must have 0 quantity, buttons must be hidden (a
    // line for a product tracked by SN doesn't have -1/+1 buttons).
    { trigger: '.o_barcode_client_action', run: 'scan productserial1' },
    {
        trigger: '.o_barcode_client_action .o_barcode_line:nth-child(2)',
        run: function () {
            helper.assertLinesCount(2);
            const $line = helper.getLine({barcode: 'productserial1'});
            helper.assertLineIsHighlighted($line, true);
            helper.assertLineQty($line, '0');
            helper.assertButtonIsNotVisible($line, 'add_quantity');
            helper.assertButtonIsNotVisible($line, 'remove_unit');
            const setButton = document.querySelector('.o_selected .o_line_button.o_set > .fa-check');
            helper.assert(Boolean(setButton), true);
        }
    },
    // Scans a serial number: must have 1 quantity, check button must display a "X".
    { trigger: '.o_barcode_client_action', run: 'scan BNG-118' },
    {
        trigger: '.o_barcode_line:contains("BNG-118")',
        run: function () {
            helper.assertLinesCount(2);
            const $line = helper.getLine({barcode: 'productserial1'});
            helper.assertLineIsHighlighted($line, true);
            helper.assertLineQty($line, '1');
            helper.assertButtonIsNotVisible($line, 'add_quantity');
            helper.assertButtonIsNotVisible($line, 'remove_unit');
            const setButton = document.querySelector('.o_selected .o_line_button.o_set.o_difference');
            helper.assert(Boolean(setButton), true);
        }
    },
    // Clicks on set button: must set the inventory quantity equals to the quantity .
    { trigger: '.o_barcode_line:contains("productserial1") .o_line_button.o_set' },
    {
        trigger: '.o_barcode_line.o_selected .fa-check',
        run: function () {
            helper.assertLinesCount(2);
            const $line = helper.getLine({barcode: 'productserial1'});
            helper.assertLineIsHighlighted($line, true);
            helper.assertLineQty($line, '0');
            helper.assertButtonIsNotVisible($line, 'add_quantity');
            helper.assertButtonIsNotVisible($line, 'remove_unit');
            const goodQuantitySetButton = document.querySelector('.o_selected .o_line_button.o_set > .fa-check');
            helper.assert(Boolean(goodQuantitySetButton), true);
            const differenceSetButton = document.querySelector('.o_selected .o_line_button.o_set.o_difference');
            helper.assert(Boolean(differenceSetButton), false);
        }
    },
    // Clicks again on set button: must unset the quantity.
    { trigger: '.o_barcode_line:contains("productserial1") .o_line_button.o_set' },
    {
        trigger: '.o_barcode_line:contains("productserial1"):contains("?")',
        run: function () {
            helper.assertLinesCount(2);
            const $line = helper.getLine({barcode: 'productserial1'});
            helper.assertLineIsHighlighted($line, true);
            helper.assertLineQty($line, '?');
            helper.assertButtonIsNotVisible($line, 'add_quantity');
            helper.assertButtonIsNotVisible($line, 'remove_unit');
            const goodQuantitySetButton = document.querySelector('.o_selected .o_line_button.o_set > .fa-check');
            helper.assert(Boolean(goodQuantitySetButton), false);
            const differenceSetButton = document.querySelector('.o_selected .o_line_button.o_set.o_difference');
            helper.assert(Boolean(differenceSetButton), false);
            const emptySetButton = document.querySelector('.o_selected .o_line_button.o_set');
            helper.assert(Boolean(emptySetButton), true);
        }
    },

    // Scans productlot1: must have 0 quantity, buttons should be visible.
    { trigger: '.o_barcode_client_action', run: 'scan productlot1' },
    {
        trigger: '.o_barcode_client_action .o_barcode_line:nth-child(3)',
        run: function () {
            helper.assertLinesCount(3);
            const $line = helper.getLine({barcode: 'productlot1'});
            helper.assertLineIsHighlighted($line, true);
            helper.assertLineQty($line, '0');
            helper.assertButtonIsVisible($line, 'add_quantity');
            helper.assertButtonIsVisible($line, 'remove_unit');
            const decrementButton = document.querySelector('.o_line_button.o_remove_unit');
            helper.assert(decrementButton.hasAttribute('disabled'), true);
        }
    },
    // Scans a lot number: must have 1 quantity, buttons should still be visible.
    { trigger: '.o_barcode_client_action', run: 'scan toto-42' },
    {
        trigger: '.o_barcode_line:contains("toto-42")',
        run: function () {
            helper.assertLinesCount(3);
            const $line = helper.getLine({barcode: 'productlot1'});
            helper.assertLineIsHighlighted($line, true);
            helper.assertLineQty($line, '1');
            helper.assertButtonIsVisible($line, 'add_quantity');
            helper.assertButtonIsVisible($line, 'remove_unit');
            const decrementButton = document.querySelector('.o_line_button.o_remove_unit');
            helper.assert(decrementButton.hasAttribute('disabled'), false);
        }
    },
    // Clicks on -1 button: must have 0 quantity, button -1 must be disabled again.
    { trigger: '.o_barcode_line:contains("productlot1") .o_remove_unit' },
    {
        trigger: '.o_barcode_line:contains("productlot1") .qty-done:contains("0")',
        run: function () {
            helper.assertLinesCount(3);
            const $line = helper.getLine({barcode: 'productlot1'});
            helper.assertLineIsHighlighted($line, true);
            helper.assertLineQty($line, '0');
            helper.assertButtonIsVisible($line, 'add_quantity');
            helper.assertButtonIsVisible($line, 'remove_unit');
            const decrementButton = document.querySelector('.o_line_button.o_remove_unit');
            helper.assert(decrementButton.hasAttribute('disabled'), true);
        }
    },
    // Clicks on +1 button: must have 1 quantity, buttons must be visible.
    { trigger: '.o_barcode_line:contains("productlot1") .o_add_quantity' },
    {
        trigger: '.o_barcode_line:contains("productlot1") .qty-done:contains(1)',
        run: function () {
            helper.assertLinesCount(3);
            const $line = helper.getLine({barcode: 'productlot1'});
            helper.assertLineIsHighlighted($line, true);
            helper.assertLineQty($line, '1');
            helper.assertButtonIsVisible($line, 'add_quantity');
            helper.assertButtonIsVisible($line, 'remove_unit');
            const decrementButton = document.querySelector('.o_line_button.o_remove_unit');
            helper.assert(decrementButton.hasAttribute('disabled'), false);
        }
    },

    // Scans product2 => Should retrieve the quantity on hand and display 1/10.
    { trigger: '.o_barcode_client_action', run: 'scan product2' },
    {
        trigger: '.o_barcode_line:contains("product2")',
        run: function () {
            helper.assertLinesCount(4);
            const $line = helper.getLine({barcode: 'product2'});
            helper.assertLineIsHighlighted($line, true);
            helper.assertLineQuantityOnReservedQty(3, '1 / 10');
            helper.assertButtonIsVisible($line, 'add_quantity');
            helper.assertButtonIsVisible($line, 'remove_unit');
            const setButton = document.querySelector('.o_selected .o_line_button.o_set.o_difference');
            helper.assert(Boolean(setButton), true);
        }
    },
    // Clicks multiple time on the set quantity button and checks the save is rightly done.
    { trigger: '.o_selected .o_line_button.o_set.o_difference' },
    {
        trigger: '.o_barcode_line:contains("product2"):contains("?")',
        run: function () {
            const line = document.querySelector('.o_barcode_line[data-barcode=product2]');
            const qty = line.querySelector('.o_barcode_scanner_qty').textContent;
            helper.assert(qty, '?/ 10');
        }
    },
    // Goes to the quant form view to trigger a save then go back.
    { trigger: '.o_selected .o_line_button.o_edit' },
    { trigger: '.o_discard' },
    {
        trigger: '.o_barcode_line:contains("product2"):contains("?")',
        run: function () {
            const line = document.querySelector('.o_barcode_line[data-barcode=product2]');
            const qty = line.querySelector('.o_barcode_scanner_qty').textContent;
            helper.assert(qty, '?/ 10');
        }
    },

    // Clicks again, should pass from  "? / 10" to "10 / 10"
    { trigger: '.o_barcode_line:contains("product2") .o_line_button.o_set' },
    {
        trigger: '.o_barcode_line:contains("product2") .qty-done:contains("10")',
        run: function () {
            const line = document.querySelector('.o_barcode_line[data-barcode=product2]');
            const qty = line.querySelector('.o_barcode_scanner_qty').textContent;
            helper.assert(qty, '10/ 10');
        }
    },
    // Goes to the quant form view to trigger a save then go back.
    { trigger: '.o_barcode_line:contains("product2") .o_line_button.o_edit' },
    { trigger: '.o_discard' },
    {
        trigger: '.o_barcode_line:contains("product2") .qty-done:contains("10")',
        run: function () {
            const line = document.querySelector('.o_barcode_line[data-barcode=product2]');
            const qty = line.querySelector('.o_barcode_scanner_qty').textContent;
            helper.assert(qty, '10/ 10');
        }
    },

    // Clicks again, should pass from  "10 / 10" to "? / 10"
    { trigger: '.o_barcode_line:contains("product2") .o_line_button.o_set .fa-check' },
    {
        trigger: '.o_barcode_line:contains("product2"):contains("?")',
        run: function () {
            const line = document.querySelector('.o_barcode_line[data-barcode=product2]');
            const qty = line.querySelector('.o_barcode_scanner_qty').textContent;
            helper.assert(qty, '?/ 10');
        }
    },

    // Validates the inventory.
    { trigger: '.o_apply_page' },
    { trigger: '.o_notification.border-success' }
]);
