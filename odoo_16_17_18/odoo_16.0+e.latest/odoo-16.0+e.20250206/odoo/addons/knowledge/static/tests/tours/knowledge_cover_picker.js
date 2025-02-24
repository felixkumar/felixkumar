/** @odoo-module */

import { endKnowledgeTour, makeVisible } from './knowledge_tour_utils.js';
import tour from 'web_tour.tour';

/**
 * Tests the cover picker feature when unsplash credentials are unset. In this
 * case, the "Add Cover" button should always open the cover selector.
 */
tour.register('knowledge_cover_selector_tour', {
    test: true,
    url: '/web',
}, [tour.stepUtils.showAppsMenuItem(), {
    // Open Knowledge App
    trigger: '.o_app[data-menu-xmlid="knowledge.knowledge_menu_root"]',
}, {
    // Click on the "Create" button
    trigger: '.o_knowledge_header .btn-create',
}, {
    // Set the name of the article
    trigger: '.o_breadcrumb_article_name > input',
    extra_trigger: '.o_article_active:contains("Untitled")',
    run: 'text Birds',
}, {
    // Make the add cover button visible (only visible on hover)
    trigger: '.o_article_active:contains("Birds")',
    run: () => makeVisible('.o_knowledge_add_cover'),
}, {
    // Click on add cover button
    trigger: '.o_knowledge_add_cover',
}, {
    // Check that the cover selector has been opened and that it shows
    // the form allowing to enter unsplash credentials, and click on the
    // add url button
    trigger: '.o_upload_media_url_button',
    extra_trigger: '.modal-body .unsplash_error',
    run: () => {},
}, {
    // Change the search query to find odoo_logo file
    trigger: '.modal-body input.o_we_search',
    extra_trigger: '.modal-body .o_nocontent_help',
    run: 'text odoo_logo',
}, {
    // Choose the odoo_logo cover
    trigger: '.o_existing_attachment_cell img[title*="odoo_logo"]',
    run: 'click',
}, {
    // Check cover has been added to the article, and make the change cover
    // button visible
    trigger: '.o_knowledge_cover .o_knowledge_cover_image',
    run: () => makeVisible('.o_knowledge_change_cover'),
}, {
    // Click on change cover button
    trigger: '.o_knowledge_change_cover',
}, {
    // Check that the cover selector has been opened, that no image is shown
    // since the search query (birds) do not match the name of the existing
    // cover, and close the cover selector
    trigger: '.modal-footer .btn-secondary',
    extra_trigger: '.modal-body .o_nocontent_help',
}, {
    // Make the remove cover button visible
    trigger: '.o_knowledge_edit_cover_buttons',
    run: () => makeVisible('.o_knowledge_remove_cover'),
}, {
    // Click on remove cover button
    trigger: '.o_knowledge_remove_cover',
}, {
    // Check cover has been removed from the article and create another article
    trigger: '.o_knowledge_header .btn-create',
    extra_trigger: '.o_knowledge_cover:not(:has(.o_knowledge_cover_image))',
}, {
    // Change the name of the article
    trigger: '.o_breadcrumb_article_name > input',
    extra_trigger: '.o_article_active:contains("Untitled")',
    run: 'text odoo',
}, {
    // Make the add cover button visible
    trigger: '.o_article_active:contains("odoo")',
    run: () => makeVisible('.o_knowledge_add_cover'),
}, {
    // Click on add cover button
    trigger: '.o_knowledge_add_cover',
}, {
    // Check that odoo logo previously uploaded is shown in the selector as the
    // search query, which is the article name, is "odoo" which is also in the
    // cover attachment's name, and that clicking on it sets it as cover of the
    // current article
    trigger: '.modal-body .o_existing_attachment_cell img[title="odoo_logo.png"]',
}, {
    // Check cover has been set, and open previous article again
    trigger: '.o_knowledge_aside .o_article_name:contains("Birds")',
    extra_trigger: '.o_knowledge_cover .o_knowledge_cover_image',
}, {
    // Make the add cover button visible
    trigger: '.o_knowledge_edit_cover_buttons',
    run: () => makeVisible('.o_knowledge_add_cover'),
}, {
    // Click on add cover button
    trigger: '.o_knowledge_add_cover',
}, {
    // Check odoo logo is not shown as the search query does not match its name
    // and remove search query
    trigger: '.modal-body input.o_we_search',
    extra_trigger: '.modal-body .o_nocontent_help',
    run: 'remove_text',
}, {
    // Check that odoo logo is now shown in the cover selector, and make the trash
    // button visible
    trigger: '.modal-body .o_existing_attachment_cell img[title="odoo_logo.png"]',
    run: () => makeVisible('.modal-body .o_existing_attachment_cell .o_existing_attachment_remove')
}, {
    // Click on delete cover button
    trigger: '.modal-body .o_existing_attachment_cell:has(img[title="odoo_logo.png"]) .o_existing_attachment_remove',
}, {
    // Confirm deletion of cover (should ask for confirmation)
    trigger: '.modal-footer .btn-primary',
    extra_trigger: '.modal-title:contains("Confirmation")'
}, {
    // Check that no cover is shown anymore in the cover selector, and close it
    trigger: '.modal-footer .btn-secondary',
    extra_trigger: '.modal-body .o_we_existing_attachments:not(:has(.o_existing_attachment_cell))',
}, {
    // Open other article to check that its cover has been removed since it has
    // been deleted
    trigger: '.o_knowledge_aside .o_article_name:contains("odoo")',
}, {
    trigger: '.o_knowledge_cover:not(:has(.o_knowledge_cover_image))',
    extra_trigger: '.o_article_active:contains("odoo")',
    allowInvisible: true,
}, ...endKnowledgeTour()
]);
