odoo.define('test_mrp_barcode_flows.tour', function(require) {
'use strict';

var helper = require('stock_barcode.tourHelper');
var tour = require('web_tour.tour');

tour.register('test_immediate_receipt_kit_from_scratch_with_tracked_compo', {test: true}, [
    {
        trigger: '.o_barcode_client_action',
        run: 'scan kit_lot',
    },
    {
        trigger: '.o_barcode_line:contains("Kit Lot") .o_edit',
    },
    {
        trigger: '.o_digipad_button.o_increase',
    },
    {
        trigger: '.o_save',
    },
    {
        trigger: '.o_barcode_line:contains("Kit Lot") .o_add_quantity'
    },
    {
        trigger: '.o_barcode_line:contains("Kit Lot") .qty-done:contains("3")',
        run: 'scan simple_kit',
    },
    {
        extra_trigger: '.o_barcode_line:contains("Simple Kit")',
        trigger: '.btn.o_validate_page',
    },
    {
        extra_trigger: '.o_notification.border-danger',
        trigger: '.o_barcode_line:contains("Compo Lot")',
        run: function() {
            helper.assertLinesCount(4);
            const [ kit_lot_compo01, simple_kit_compo01, simple_kit_compo02, kit_lot_compo_lot ] = document.querySelectorAll('.o_barcode_line');
            helper.assertLineProduct(kit_lot_compo01, 'Compo 01');
            helper.assertLineProduct(kit_lot_compo_lot, 'Compo Lot');
            helper.assertLineProduct(simple_kit_compo01, 'Compo 01');
            helper.assertLineProduct(simple_kit_compo02, 'Compo 02');
        }
    },
    {
        trigger: '.o_barcode_line:contains("Compo Lot")',
        run: 'scan compo_lot',
    },
    {
        trigger: '.o_barcode_line.o_selected div[name="lot"] .o_next_expected',
        run: 'scan super_lot',
    },
    {
        extra_trigger: '.o_line_lot_name:contains("super_lot")',
        trigger: '.btn.o_validate_page',
    },
    {
        trigger: '.o_notification.border-success',
    },
]);

tour.register('test_planned_receipt_kit_from_scratch_with_tracked_compo', {test: true}, [
    {
        trigger: '.o_barcode_client_action',
        run: 'scan kit_lot',
    },
    tour.stepUtils.confirmAddingUnreservedProduct(),
    {
        trigger: '.o_barcode_line:contains("Kit Lot") .o_edit',
    },
    {
        trigger: '.o_digipad_button.o_increase',
    },
    {
        trigger: '.o_save',
    },
    {
        trigger: '.o_barcode_line:contains("Kit Lot") .o_add_quantity'
    },
    {
        trigger: '.o_barcode_line:contains("Kit Lot") .qty-done:contains("3")',
        run: 'scan simple_kit',
    },
    tour.stepUtils.confirmAddingUnreservedProduct(),
    {
        extra_trigger: '.o_barcode_line:contains("Simple Kit")',
        trigger: '.btn.o_validate_page',
    },
    {
        extra_trigger: '.o_notification.border-danger',
        trigger: '.o_barcode_line:contains("Compo Lot")',
        run: function() {
            helper.assertLinesCount(4);
            const [ kit_lot_compo01, simple_kit_compo01, simple_kit_compo02, kit_lot_compo_lot ] = document.querySelectorAll('.o_barcode_line');
            helper.assertLineProduct(kit_lot_compo01, 'Compo 01');
            helper.assertLineProduct(kit_lot_compo_lot, 'Compo Lot');
            helper.assertLineProduct(simple_kit_compo01, 'Compo 01');
            helper.assertLineProduct(simple_kit_compo02, 'Compo 02');
        }
    },
    {
        trigger: '.o_barcode_line:contains("Compo Lot")',
    },
    {
        trigger: '.o_selected:contains("Compo Lot")',
        run: 'scan super_lot',
    },
    {
        extra_trigger: '.o_line_lot_name:contains("super_lot")',
        trigger: '.btn.o_validate_page',
    },
    {
        trigger: '.o_notification.border-success',
    },
]);

tour.register('test_picking_product_with_kit_and_packaging', { test: true }, [
    { trigger: '.btn.o_validate_page', run: 'click' }
]);
});
