/** @odoo-module */

import { localization } from "@web/core/l10n/localization";

export default {
    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------
    /**
     * Resize the sidebar when the resizer is grabbed.
     * @param {DOM.Element} el - Element on which the sidebarSize style is set
     * @param {boolean} saveSize - Save new width in localStorage if True
     */
    resizeSidebar: function (el, saveSize) {
        const onPointerMove = _.throttle(event => {
            event.preventDefault();
            let width;
            if (localization.direction === "rtl") {
                // Sidebar is placed on the right
                width = window.innerWidth - event.pageX;
            } else {
                width = event.pageX;
            }
            el.style.setProperty('--knowledge-article-sidebar-size', `${width}px`);
            if (saveSize) {
                localStorage.setItem('knowledgeArticleSidebarSize', width);
            }
        }, 100);
        const onPointerUp = () => {
            el.removeEventListener('pointermove', onPointerMove);
            document.body.style.cursor = "auto";
            document.body.style.userSelect = "auto";
        };
        // Add style to root element because resizing has a transition delay,
        // meaning that the cursor is not always on top of the resizer.
        document.body.style.cursor = "col-resize";
        document.body.style.userSelect = "none";
        el.addEventListener('pointermove', onPointerMove);
        el.addEventListener('pointerup', onPointerUp, {once: true});
    },

    /**
     * Initializes the drag-and-drop behavior of the favorite.
     * Once this function is called, the user will be able to reorder their favorites.
     * When a favorite is reordered, `this.resequenceFavorites` will be called
     * and the drag-and-drop behavior will be deactivated while the request is pending.
     * - If the rpc call succeeds, the drag-and-drop behavior will be reactivated.
     * - If the rpc call fails, the change will be undo and the drag-and-drop
     *   behavior will be reactivated.
     * Unfortunately, `sortable` can only restore one transformation. Disabling
     * the drag-and-drop behavior will ensure that the list structure can be restored
     * if something went wrong.
     */
    _setTreeFavoriteListener: function () {
        const $sortable = $('.o_tree_favorite');
        $sortable.sortable({
            axis: 'y',
            handle: '.o_article_handle',
            items: 'li:not(.o_article_tree_child)',
            opacity: 0.6,
            placeholder: 'ui-sortable-placeholder',
            tolerance: 'intersect',
            helper: 'clone',
            cursor: 'grabbing',
            cancel: '.o_article_tree_child',
            scrollSpeed: 6,
            delay: 150,
            distance: 10,
            /**
             * @param {Event} event
             * @param {Object} ui
             */
            stop: async (event, ui) => {
                const favoriteIds = $sortable.find('.o_article:not(.o_article_tree_child)').map(function () {
                    return $(this).data('favorite-article-id');
                }).get();
                $sortable.sortable('disable');
                try {
                    await this._resequenceFavorites(favoriteIds);
                    $sortable.sortable('enable');
                } catch {
                    $sortable.sortable('cancel');
                    $sortable.sortable('enable');
                }
            },
        });
    },

    /**
     * Callback function called when the user clicks on the carret of an article
     * The function will load the children of the article and append them to the
     * dom. Then, the id of the unfolded article will be added to the cache.
     * (see: `_renderTree`).
     * @param {Event} event
     */
    _onFold: async function (event) {
        event.stopPropagation();
        const $button = $(event.currentTarget);
        const isFavoriteTree = $button.closest('section').hasClass('o_favorite_container');
        this._fold($button, isFavoriteTree);
    },
    _fold: async function ($button, isFavoriteTree) {
       const $icon = $button.find('i');
       const $li = $button.closest('li');
       const articleId = $li.data('articleId').toString();
       if ($icon.hasClass('fa-caret-down')) {
           // Hiding ul breaks nestedSortable, so move children
           // inside sibling to not lose its content
           const $ul = $li.find('> ul');
           $li.find('> div').append($ul.detach().hide());
           this._removeUnfolded(articleId, isFavoriteTree);
           $icon.removeClass('fa-caret-down');
           $icon.addClass('fa-caret-right');
       } else {
           const $ul = $li.find('> div > ul');
           if ($ul.length) {
               // Show children content stored in sibling
               $li.append($ul.detach().show());
           } else {
               let children;
               try {
                   children = await this._fetchChildrenArticles($li.data('articleId'));
               } catch (error) {
                   // Article is not accessible anymore, remove it from the sidebar
                   $li.remove();
                   throw error;
               }
               const $newUl = $('<ul/>').append(children);
               $li.append($newUl);
           }
           this._addUnfolded(articleId, isFavoriteTree);
           $icon.removeClass('fa-caret-right');
           $icon.addClass('fa-caret-down');  
       } 
    },

    /**
     * Add an article id to the list of unfolded articles ids in the cache
     * @param {string} articleId - Id of the article to add
     */
    _addUnfolded: function (articleId, isFavoriteTree) {
        const storageKey = isFavoriteTree ? 'knowledge.unfolded.favorite.ids' : 'knowledge.unfolded.ids';
        let unfoldedArticlesIds = localStorage.getItem(storageKey);
        unfoldedArticlesIds = unfoldedArticlesIds ? unfoldedArticlesIds.split(";") : [];
        if (unfoldedArticlesIds.indexOf(articleId) === -1) {
            unfoldedArticlesIds.push(articleId);
            localStorage.setItem(storageKey, unfoldedArticlesIds.join(";"));
        }
    },
    /**
     * Remove an article id from the list of unfolded articles ids in the cache
     * @param {string} articleId - Id of the article to remove
     */
     _removeUnfolded: function (articleId, isFavoriteTree) {
         const storageKey = isFavoriteTree ? 'knowledge.unfolded.favorite.ids' : 'knowledge.unfolded.ids';
         let unfoldedArticlesIds = localStorage.getItem(storageKey);
         unfoldedArticlesIds = unfoldedArticlesIds ? unfoldedArticlesIds.split(";") : [];
         if (unfoldedArticlesIds.indexOf(articleId) !== -1) {
             unfoldedArticlesIds.splice(unfoldedArticlesIds.indexOf(articleId), 1);
             localStorage.setItem(storageKey, unfoldedArticlesIds.join(";"));
         }
     },

    async _loadMoreArticles(ev) {
        ev.preventDefault();

        let addedArticles;
        const rpcParams = {
            active_article_id: this.resId || false,
            parent_id: ev.target.dataset['parentId'] || false,
            category: ev.target.dataset['category'] || false,
            limit: ev.target.dataset['limit'],
            offset: ev.target.dataset['offset'] || 0,
        };

        // backend / publicWidget compatibility
        if (this.rpc) {
            addedArticles = await this.rpc(
                '/knowledge/tree_panel/load_more',
                rpcParams
            );
        } else {
            addedArticles = await this._rpc({
                route: '/knowledge/tree_panel/load_more',
                params: rpcParams,
            });
        }

        const listRoot = ev.target.closest('ul');
        // remove existing "Load more" link
        ev.target.remove();
        // remove the 'forced' displayed active article
        const forcedDisplayedActiveArticle = listRoot.querySelector(
            '.o_knowledge_article_force_show_active_article');
        if (forcedDisplayedActiveArticle) {
            forcedDisplayedActiveArticle.remove();
        }
        // insert the returned template
        listRoot.insertAdjacentHTML('beforeend', addedArticles);
    }
};

