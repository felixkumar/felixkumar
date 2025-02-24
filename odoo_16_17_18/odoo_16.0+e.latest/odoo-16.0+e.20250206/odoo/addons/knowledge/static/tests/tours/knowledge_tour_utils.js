/** @odoo-module */

import tour from 'web_tour.tour';

/**
 * Steps to insert an articleLink for the given article, in the first editable
 * html_field found in the given container selector (should have a paragraph
 * as its last element, and the link will be inserted at the position at index
 * offset in the paragraph).
 *
 * @param {string} htmlFieldContainerSelector jquery selector for the container
 * @param {string} articleName name of the article to insert a link for
 * @param {integer} offset position of the command call in the paragraph
 * @returns {Array} tour steps
 */
export function appendArticleLink(htmlFieldContainerSelector, articleName, offset=0) {
    return [{ // open the command bar
        trigger: `${htmlFieldContainerSelector} .odoo-editor-editable > p:last-child`,
        run: function () {
            openCommandBar(this.$anchor[0], offset);
        },
    }, { // click on the /article command
        trigger: '.oe-powerbox-commandName:contains(Article)',
        run: 'click',
        in_modal: false,
    }, { // select an article in the list
        trigger: `.select2-results > .select2-result:contains(${articleName})`,
        run: 'click',
        in_modal: false,
    }, { // wait for the choice to be registered
        trigger: `.select2-chosen:contains(${articleName})`,
        run: () => {},
    }, { // click on the "Insert Link" button
        trigger: '.modal-dialog:contains(Link an Article) .modal-footer button.btn-primary',
        run: 'click'
    }];
}

/**
 * Ensure that the tour does not end on the Knowledge form view by returning to
 * the home menu.
 */
export function endKnowledgeTour() {
    return [
        tour.stepUtils.toggleHomeMenu(), {
            trigger: '.o_app[data-menu-xmlid="knowledge.knowledge_menu_root"]',
            run: () => {},
        }
    ];
}

export function makeVisible(selector) {
    const el = document.querySelector(selector);
    if (el) {
        el.style.setProperty('visibility', 'visible', 'important');
        el.style.setProperty('opacity', '1', 'important');
    }
}

/**
 * Opens the power box of the editor
 * @param {HTMLElement} paragraph
 * @param {integer} offset position of the command call in the paragraph
 */
export function openCommandBar(paragraph, offset=0) {
    const sel = document.getSelection();
    sel.removeAllRanges();
    const range = document.createRange();
    range.setStart(paragraph, offset);
    range.setEnd(paragraph, offset);
    sel.addRange(range);
    paragraph.dispatchEvent(new KeyboardEvent('keydown', {
        key: '/',
    }));
    const slash = document.createTextNode('/');
    paragraph.prepend(slash);
    sel.removeAllRanges();
    range.setStart(slash, 1);
    range.setEnd(slash, 1);
    sel.addRange(range);
    paragraph.dispatchEvent(new InputEvent('input', {
        inputType: 'insertText',
        data: '/',
        bubbles: true,
    }));
    paragraph.dispatchEvent(new KeyboardEvent('keyup', {
        key: '/',
    }));
}
