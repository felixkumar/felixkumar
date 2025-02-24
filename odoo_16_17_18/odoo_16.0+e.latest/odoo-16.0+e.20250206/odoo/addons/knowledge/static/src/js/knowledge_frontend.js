/** @odoo-module */
'use strict';

import { fetchValidHeadings } from './tools/knowledge_tools.js';
import KnowledgeTreePanelMixin from './tools/tree_panel_mixin.js';
import publicWidget from 'web.public.widget';
import session from 'web.session';
import { qweb as QWeb } from 'web.core';
import { debounce } from "@web/core/utils/timing";

publicWidget.registry.KnowledgeWidget = publicWidget.Widget.extend(KnowledgeTreePanelMixin, {
    selector: '.o_knowledge_form_view',
    events: {
        'keyup .knowledge_search_bar': '_searchArticles',
        'click .o_article_caret': '_onFold',
        'click .o_favorites_toggle_button': '_toggleFavorite',
        'click .o_knowledge_toc_link': '_onTocLinkClick',
        'click .o_knowledge_article_load_more': '_loadMoreArticles',
    },

    /**
     * @override
     * @returns {Promise}
     */
    start: function () {
        return this._super.apply(this, arguments).then(() => {
            this.$id = this.$el.data('article-id');
            this.resId = this.$id;  // necessary for the 'KnowledgeTreePanelMixin' extension
            this._renderTree(this.$id, '/knowledge/tree_panel/portal');
            this.renderViewLinks();
            this._setResizeListener();
            // Debounce the search articles method to reduce the number of rpcs
            this._searchArticles = debounce(this._searchArticles, 500);
            /**
             * The embedded views are currently not supported in the frontend due
             * to some technical limitations. Instead of showing an empty div, we
             * will render a placeholder inviting the user to log in. Once logged
             * in, the user will be redirected to the backend and should be able
             * to load the embedded view.
             */
            const $placeholder = $(QWeb.render('knowledge.embedded_view_placeholder', {
                url: `/knowledge/article/${this.$id}`,
                isLoggedIn: session.user_id !== false
            }));
            const $container = $('.o_knowledge_behavior_type_embedded_view');
            $container.empty();
            $container.append($placeholder);
        });
    },

    /**
     * Invite public users to log in as they are trying to access an internal view.
     * They will then be redirected to the current article and will be able to interact
     * with the link again.
     */
    renderViewLinks() {
        for (const viewLink of this.el.getElementsByClassName("o_knowledge_view_link")) {
            // Replace `span` elements by actual links.
            const link = document.createElement("A");
            link.classList.add("text-o-color-1");
            link.href = `/web/login?redirect=/knowledge/article/${this.resId}`;
            link.textContent = JSON.parse(decodeURIComponent(viewLink.dataset.behaviorProps)).name;
            viewLink.replaceWith(link);
        }
    },

    /**
     * @param {Event} event
     */
    _searchArticles: async function (ev) {
        ev.preventDefault();
        const searchTerm = this.$('.knowledge_search_bar').val();
        if (!searchTerm){
            // Renders the basic user article tree (with only its cached articles unfolded)
            await this._renderTree(this.$id, '/knowledge/tree_panel/portal');
            return;
        }
        // Renders articles based on search term in a flatenned tree (no sections nor child articles)
        const container = this.el.querySelector('.o_knowledge_tree');
        try {
            const htmlTree = await this._rpc({
                route: '/knowledge/tree_panel/portal/search',
                params: {
                    search_term: searchTerm,
                    active_article_id: this.$id,
                }
            });
            container.innerHTML = htmlTree;
        } catch {
            container.innerHTML = "";
        }
    },

    /**
     * Enables the user to resize the aside block.
     * Note: When the user grabs the resizer, a new listener will be attached
     * to the document. The listener will be removed as soon as the user releases
     * the resizer to free some resources.
     */
    _setResizeListener: function () {
        this.el.querySelector('.o_knowledge_article_form_resizer span').addEventListener(
            'pointerdown', () => this.resizeSidebar(this.el)
        );
    },

    /**
     * Helper function to traverse the dom hierarchy of the aside tree menu.
     * The function will call the given callback function with the article item
     * beeing visited (i.e: a JQuery dom element). The provided callback function
     * should return a boolean indicating whether the algorithm should explore
     * the children of the current article item.
     * @param {jQuery} $tree
     * @param {Function} callback
     */
    _traverse: function ($tree, callback) {
        const stack = $tree.children('li').toArray();
        while (stack.length > 0) {
            const $li = $(stack.shift());
            if (callback($li)) {
                const $ul = $li.children('ul');
                stack.unshift(...$ul.children('li').toArray());
            }
        }
    },

    /**
     * @param {Event} event
     */
    _toggleFavorite: async function (event) {
        const star = event.currentTarget;
        const id = parseInt(star.dataset.articleId);
        const result = await this._rpc({
            model: 'knowledge.article',
            method: 'action_toggle_favorite',
            args: [[id]]
        });
        const icon = star.querySelector('i');
        icon.classList.toggle('fa-star', result);
        icon.classList.toggle('fa-star-o', !result);

        // Add the article to the favorite tree if the favorite tree is visible
        if (!document.querySelector('.o_favorite_container')) {
            return;
        }
        let unfoldedFavoriteArticlesIds = localStorage.getItem('knowledge.unfolded.favorite.ids');
        unfoldedFavoriteArticlesIds = unfoldedFavoriteArticlesIds ? unfoldedFavoriteArticlesIds.split(";").map(Number) : [];
        // Add/Remove the article to/from the favorite in the sidebar
        const template = await this._rpc({
            route: '/knowledge/tree_panel/favorites',
            params: {
                active_article_id: id,
                unfolded_favorite_articles_ids: unfoldedFavoriteArticlesIds,
            }
        });
        document.querySelector('.o_favorite_container').innerHTML = template;
        this._setTreeFavoriteListener();
    },

    /**
     * Renders the tree listing all articles.
     * To minimize loading time, the function will initially load the root articles.
     * The other articles will be loaded lazily: The user will have to click on
     * the carret next to an article to load and see their children.
     * The id of the unfolded articles will be cached so that they will
     * automatically be displayed on page load.
     * @param {integer} active_article_id
     * @param {String} route
     */
    _renderTree: async function (active_article_id, route) {
        const container = this.el.querySelector('.o_knowledge_tree');
        let unfoldedArticlesIds = localStorage.getItem('knowledge.unfolded.ids');
        unfoldedArticlesIds = unfoldedArticlesIds ? unfoldedArticlesIds.split(";").map(Number) : [];
        let unfoldedFavoriteArticlesIds = localStorage.getItem('knowledge.unfolded.favorite.ids');
        unfoldedFavoriteArticlesIds = unfoldedFavoriteArticlesIds ? unfoldedFavoriteArticlesIds.split(";").map(Number) : [];
        const params = new URLSearchParams(document.location.search);
        if (Boolean(params.get('auto_unfold'))) {
            unfoldedArticlesIds.push(active_article_id);
            unfoldedFavoriteArticlesIds.push(active_article_id);
        }
        try {
            const htmlTree = await this._rpc({
                route: route,
                params: {
                    active_article_id: active_article_id,
                    unfolded_articles_ids: unfoldedArticlesIds,
                    unfolded_favorite_articles_ids: unfoldedFavoriteArticlesIds
                }
            });
            container.innerHTML = htmlTree;
            this._setTreeFavoriteListener();
        } catch {
            container.innerHTML = "";
        }
    },

    _resequenceFavorites: function (favoriteIds) {
        this._rpc({
            route: '/web/dataset/resequence',
            params: {
                model: "knowledge.article.favorite",
                ids: favoriteIds,
                offset: 1,
            }
        });
    },

    _fetchChildrenArticles: function (parentId) {
        return this._rpc({
            route: '/knowledge/tree_panel/children',
            params: {
                parent_id: parentId
            }
        });
    },

    /**
     * Scroll through the view to display the matching heading.
     * Adds a small highlight in/out animation using a class.
     *
     * @param {Event} event
     */
    _onTocLinkClick: function (event) {
        event.preventDefault();
        const headingIndex = parseInt(event.target.getAttribute('data-oe-nodeid'));
        const targetHeading = fetchValidHeadings(this.$el[0])[headingIndex];
        if (targetHeading) {
            targetHeading.scrollIntoView({
                behavior: 'smooth',
            });
            targetHeading.classList.add('o_knowledge_header_highlight');
            setTimeout(() => {
                targetHeading.classList.remove('o_knowledge_header_highlight');
            }, 2000);
        }
    },
});
