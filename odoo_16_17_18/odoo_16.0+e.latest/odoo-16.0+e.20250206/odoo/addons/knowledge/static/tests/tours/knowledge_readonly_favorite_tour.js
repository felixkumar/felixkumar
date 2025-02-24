/** @odoo-module */

import { moveArticle } from './knowledge_main_flow_tour.js';
import tour from 'web_tour.tour';

// Checks that one can add an readonly article to its favorites

tour.register('knowledge_readonly_favorite_tour', {
    test: true,
}, [{
    // Make sure we are on the readonly article 1, that is not favorited, and
    // click on the toggle favorite button.
    trigger: 'a.o_toggle_favorite:has(.fa-star-o)',
    extra_trigger: '.o_article_active:contains("Readonly Article 1")',
}, {
    // Check that the article has been added to the favorites
    trigger: 'section.o_favorite_container:contains("Readonly Article 1")',
    extra_trigger: 'a.o_toggle_favorite:has(.fa-star)',
    run: () => {},
}, {
    // Open the other readonly article
    trigger: '.o_knowledge_aside .o_article_name:contains("Readonly Article 2")',
}, {
    // Make sure we are on the readonly article 1, that is not favorited, and
    // click on the toggle favorite button.
    trigger: 'a.o_toggle_favorite:has(.fa-star-o)',
    extra_trigger: '.o_article_active:contains("Readonly Article 2")',
}, {
    // Check that the article has been added to the favorites under the other
    // one and try to resquence the favorite articles
    trigger: 'section.o_favorite_container li:last:contains("Readonly Article 2")',
    run: () => moveArticle(
        $('section.o_favorite_container li:last .o_article_handle'),
        $('section.o_favorite_container li:first .o_article_handle')
    ),
}, {
    // Check that articles have been reordered correctly
    trigger: 'section.o_favorite_container li:last:contains("Readonly Article 1")',
    extra_trigger: 'section.o_favorite_container li:first:contains("Readonly Article 2")',
    run: () => {},
}]);
