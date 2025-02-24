# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import werkzeug

from odoo import http
from odoo.http import request
from odoo.addons.knowledge.controllers.main import KnowledgeController


class KnowledgeWebsiteController(KnowledgeController):

    # Override routes to display articles to public users
    @http.route('/knowledge/article/<int:article_id>', type='http', auth='public', website=True, sitemap=False)
    def redirect_to_article(self, **kwargs):
        if request.env.user._is_public():
            article = request.env['knowledge.article'].sudo().browse(kwargs['article_id'])
            if not article.exists():
                raise werkzeug.exceptions.NotFound()
            if not article.website_published:
                # public users can't access articles that are not published, let them login first
                return request.redirect('/web/login?redirect=/knowledge/article/%s' % kwargs['article_id'])
        return super().redirect_to_article(**kwargs)

    def _check_sidebar_display(self):
        """ With publish management, not all published articles should be
        displayed in the side panel.
        Only those should be available in the side panel:
          - Public articles = Published workspace article
          - Shared with you = Non-Published Workspace article you have access to
                              + shared articles you are member of

        Note: Here we need to split the check into 2 different requests as sudo
        is needed to access members, but sudo will grant access to workspace
        article user does not have access to.
        """
        accessible_workspace_roots = request.env["knowledge.article"].search_count(
            [("parent_id", "=", False), ("category", "=", "workspace")],
            limit=1,
        )
        if accessible_workspace_roots > 0:
            return True
        # Need sudo to access members
        displayable_shared_articles = request.env["knowledge.article"].sudo().search_count(
            [
                ("parent_id", "=", False),
                ("category", "=", "shared"),
                ("article_member_ids.partner_id", "=", request.env.user.partner_id.id),
                ("article_member_ids.permission", "!=", "none")
            ],
            limit=1,
        )
        return displayable_shared_articles > 0

    def _prepare_articles_tree_html_values(self, active_article_id=False, unfolded_articles_ids=False, unfolded_favorite_articles_ids=False):
        """ This override filters out the articles that should not be displayed
        in the tree panel once publish management is activated. """
        values = super()._prepare_articles_tree_html_values(
            active_article_id=active_article_id,
            unfolded_articles_ids=unfolded_articles_ids,
            unfolded_favorite_articles_ids=unfolded_favorite_articles_ids
        )
        # With website_published, published shared article are accessible for
        # everyone. We need to check if the user is member of the article.
        values.update({
            'shared_articles': values['shared_articles'].filtered(lambda a: a.user_has_access)
        })
        if request.env.user.has_group('base.group_user'):
            return values

        published_workspace_articles = values['workspace_articles'].filtered(lambda a: a.website_published)
        values.update({
            'shared_articles': values['workspace_articles'] - published_workspace_articles |
                               values['shared_articles'],
            'public_articles': published_workspace_articles
        })
        return values

    @http.route('/knowledge/tree_panel/load_more', type='json', auth='public', sitemap=False)
    def tree_panel_load_more(self, category, limit, offset, active_article_id=False, parent_id=False):
        return super().tree_panel_load_more(category, limit, offset, active_article_id, parent_id)

    def _get_load_more_roots_domain(self, category):
        """ Given the section (category), returns the domain used to load more
        root articles of this section.

        The returned domain should match the filtering done in "_prepare_articles_tree_html_values".
        In the website_knowledge module, we show 2 specific sections:
        - "portal_public"
           Which contains all published articles in the workspace category
        - "portal_shared"
           Which contains articles that are not published OR that are not part of
           the workspace category, but which you have direct access to. """
        if category == "portal_public":
            return [('parent_id', '=', False), ('category', '=', 'workspace'), ('website_published', '=', True)]
        elif category == "portal_shared":
            return [
            '&',
                '&',
                    ('parent_id', '=', False), ('user_has_access', '=', True),
                '|',
                    ('category', '!=', 'workspace'), ('website_published', '=', False)
            ]
        return super()._get_load_more_roots_domain(category)

    @http.route('/knowledge/home', type='http', auth='public', website=True, sitemap=False)
    def access_knowledge_home(self):
        return super().access_knowledge_home()

    @http.route('/knowledge/tree_panel/children', type='json', auth='public', website=True, sitemap=False)
    def get_tree_panel_children(self, parent_id):
        return super().get_tree_panel_children(parent_id)
