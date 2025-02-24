/** @odoo-module */

import tour from 'web_tour.tour';
import { endKnowledgeTour } from './knowledge_tour_utils.js';
import { moveArticle } from './knowledge_main_flow_tour';

tour.register('knowledge_properties_tour', {
    test: true,
    url: '/web',
}, [tour.stepUtils.showAppsMenuItem(), {
    // open Knowledge App
    trigger: '.o_app[data-menu-xmlid="knowledge.knowledge_menu_root"]',
}, { // ensure display of ParentArticle child articles
    trigger: '.o_article_handle:contains("ParentArticle") .o_article_caret',
    run: function (actions) {
        const button = this.$anchor[0];
        if (button.querySelector('i.fa-caret-right')) {
            actions.click(this.$anchor);
        }
    }
}, { // go to ChildArticle
    trigger: '.o_article .o_article_name:contains("ChildArticle")',
    run: 'click',
}, { // wait ChildArticle loading
    trigger: '.breadcrumb-item.active:contains("ChildArticle")',
    run: () => {},
}, { // click on add properties
    trigger: 'a.o_knowledge_add_properties.o_knowledge_option_button',
    run: 'click',
}, { // modify property name
    trigger: '.o_field_property_definition_header input',
    run: 'text myproperty',
}, { // finish property edition
    trigger: '.o_knowledge_editor .odoo-editor-editable',
    run: 'click',
}, { // verify property
    trigger: '.o_field_property_label:contains("myproperty")',
    run: () => {},
}, { // go to InheritPropertiesArticle
    trigger: '.o_article .o_article_name:contains("InheritPropertiesArticle")',
    run: 'click',
}, { // wait InheritPropertiesArticle loading and move InheritPropertiesArticle under ParentArticle
    trigger: '.breadcrumb-item.active:contains("InheritPropertiesArticle")',
    run: () => {
        moveArticle(
            $('.o_article_handle:contains("InheritPropertiesArticle")'),
            $('.o_article_handle:contains("ChildArticle")'),
        );
    },
}, { // verify property
    trigger: '.o_knowledge_properties .o_field_property_label:contains("myproperty")',
    run: () => {},
}, ...endKnowledgeTour()
]);
