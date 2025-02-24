/** @odoo-module */

/**
 * Portal Search Knowledge flow tour.
 * Features tested:
 * - Check that tree contains all articles
 * - Write search term in search bar
 * - Check that search tree renders the correct matching articles
 * - Set active article as favorite
 * - Clean search bar
 * - Check that the active article was correctly added to the favorite tree
 */

import tour from 'web_tour.tour';

tour.register('knowledge_portal_search_tour', {
    test: true,
}, [{ // Check that section tree contains all articles
    content: "Check that search tree contains 'My Article'",
    trigger: '.o_article_name:contains("My Article")',
    run() {},
}, {
    content: "Unfold 'My Article'", // Unfold because 'My Article' wasn't added to the unfolded articles
    trigger: '.o_article_active .o_article_caret',
}, {
    content: "Check that search tree contains 'Child Article'",
    trigger: '.o_article_name:contains("Child Article")',
    run() {},
}, {
    content: "Check that search tree contains 'Sibling Article'",
    trigger: '.o_article_name:contains("Sibling Article")',
    run() {},
}, { // Write search term in search bar
    content: "Write 'M' in the search bar",
    trigger: '.knowledge_search_bar',
    run: 'text My'
}, {
    content: "Trigger keyup event to start the search",
    trigger: '.knowledge_search_bar',
    run() {
        $('.knowledge_search_bar').trigger($.Event("keyup", { keyCode: 13 }));
    },
}, { // Check tree rendering with matching articles
    content: "Check that search tree contains 'My Article'",
    trigger: '.o_article_name:contains("My Article")',
    run() {},
}, {
    content: "Check that search tree doesn't contain 'Child Article'",
    trigger: '.o_knowledge_tree:not(:has(.o_article_name:contains("Child Article")))',
    run() {},
}, {
    content: "Check that search tree doesn't contain 'Sibling Article'",
    trigger: '.o_knowledge_tree:not(:has(.o_article_name:contains("Sibling Article")))',
    run() {},
}, { // Set active article as favorite
    content: 'Set active article (My Article) as favorite',
    trigger: '.o_favorites_toggle_button',
}, { // Clean search bar
    content: "Clean search bar",
    trigger: '.knowledge_search_bar',
    run: function (action) {
        action.remove_text("", ".knowledge_search_bar");
    },
}, { // Check that article was correctly added to the favorite tree
    content: "Check that 'My Article' was correctly added to the favorite tree",
    trigger: '.o_favorite_container .o_article .o_article_name:contains("My Article")',
    run() {},
}]);
