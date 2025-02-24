/** @odoo-module */

import { moveArticle } from './knowledge_main_flow_tour.js';
import { endKnowledgeTour } from './knowledge_tour_utils.js';
import tour from 'web_tour.tour';

// Checks that one can resequence children under a readonly parent

tour.register('knowledge_resequence_children_of_readonly_parent_tour', {
    test: true,
}, [{ // check presence of parent article and unfold it
    trigger: '.o_article_active:contains(Readonly Parent) > button.o_article_caret',
    run: 'click',
}, { // check existence and order of children, and reorder children
    trigger: '.o_article_active:contains(Readonly Parent)',
    extra_trigger: '.o_article_has_children:has(li:nth-child(1):contains(Child 1)):has(li:nth-child(2):contains(Child 2))',
    run: function () {
        const children = this.$anchor[0].parentElement.querySelectorAll(".o_article_handle");
        // move 2nd child above the first.
        moveArticle($(children[1]), $(children[0]));
    },
}, { // check that the children were correctly reordered, and try to make a root from one children
    trigger: '.o_article_active:contains(Readonly Parent)',
    extra_trigger: '.o_article_has_children:has(li:nth-child(1):contains(Child 2)):has(li:nth-child(2):contains(Child 1))',
    run: function () {
        const child1 = this.$anchor[0].parentElement.querySelectorAll(".o_article_handle")[1]
        // move 1st child above parent.
        moveArticle($(child1), this.$anchor);
    },
}, { // check that the 1st child move was effective
    trigger: '.o_section:contains(Workspace):has(li:nth-child(2):contains(Child 1)):has(li:nth-child(3):contains(Readonly Parent))',
    run: () => {},
}, ...endKnowledgeTour()
]);
