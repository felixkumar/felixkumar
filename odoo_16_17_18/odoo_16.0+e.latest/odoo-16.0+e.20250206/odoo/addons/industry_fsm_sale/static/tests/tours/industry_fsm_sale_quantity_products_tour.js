/** @odoo-module **/
import tour from 'web_tour.tour';

tour.register('industry_fsm_sale_quantity_products_tour', {
    test: true,
    url: "/web",
}, [{
    trigger: '.o_app[data-menu-xmlid="industry_fsm.fsm_menu_root"]',
    content: 'Go to industry FSM',
    position: 'bottom',
}, {
    trigger: '.o_kanban_record div[name="name"]:contains("Fsm task")',
    content: 'Open task',
}, {
    trigger: 'button[name="action_fsm_view_material"]',
    content: 'Open products kanban view',
}, {
    trigger: '.o_kanban_record:nth-child(2) .o_fsm_industry_product .o-dropdown .dropdown-toggle',
    content: 'Click the dropdown toggle in the second kanban-box',
}, {
    trigger: '.o_kanban_record:nth-child(2) .o_fsm_industry_product .o_dropdown_kanban .dropdown-item:contains("Edit")',
    content: 'Click the "Edit" dropdown item in the second kanban-box',
}, {
    trigger: '.breadcrumb-item.o_back_button:nth-of-type(3)',
    content: 'Back to the list of products',
    position: 'bottom',
}, {
    trigger: '.o_kanban_record:nth-child(2) div[name="fsm_quantity"]  span:contains("0")',
    content: 'Assert that the quantity has not been updated',
}]);
