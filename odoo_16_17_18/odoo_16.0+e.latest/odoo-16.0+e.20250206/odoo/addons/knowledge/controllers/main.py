# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import werkzeug

from odoo import http, tools, _
from odoo.exceptions import AccessError, ValidationError
from odoo.http import request
from odoo.osv import expression


class KnowledgeController(http.Controller):

    _KNOWLEDGE_TREE_ARTICLES_LIMIT = 50

    # ------------------------
    # Article Access Routes
    # ------------------------

    @http.route('/knowledge/home', type='http', auth='user')
    def access_knowledge_home(self):
        """ This route will redirect internal users to the backend view of the
        article and the share users to the frontend view instead. """
        article = request.env["knowledge.article"]._get_first_accessible_article()
        if request.env.user.has_group('base.group_user') and not article:
            return self._redirect_to_backend_view(article)
        if not article:
            return self._redirect_to_portal_view(False, hide_side_bar=True)
        return request.redirect("/knowledge/article/%s" % article.id)

    @http.route('/knowledge/article/<int:article_id>', type='http', auth='user')
    def redirect_to_article(self, article_id):
        """ This route will redirect internal users to the backend view of the
        article and the share users to the frontend view instead."""
        article = request.env['knowledge.article'].search([('id', '=', article_id)])
        if request.env.user.has_group('base.group_user'):
            if not article:
                return werkzeug.exceptions.Forbidden()
            return self._redirect_to_backend_view(article)
        return self._redirect_to_portal_view(article)

    @http.route('/knowledge/article/invite/<int:member_id>/<string:invitation_hash>', type='http', auth='public')
    def article_invite(self, member_id, invitation_hash):
        """ This route will check if the given parameter allows the client to access the article via the invite token.
        Then, if the partner has not registered yet, we will redirect the client to the signup page to finally redirect
        them to the article.
        If the partner already has registrered, we redirect them directly to the article.
        """
        member = request.env['knowledge.article.member'].sudo().browse(member_id).exists()
        correct_token = member._get_invitation_hash() if member else False
        if not correct_token or not tools.consteq(correct_token, invitation_hash):
            raise werkzeug.exceptions.NotFound()

        partner = member.partner_id
        article = member.article_id

        if not partner.user_ids:
            # Force the signup even if not enabled (as we explicitly invited the member).
            # They should still be able to create a user.
            signup_allowed = request.env['res.users']._get_signup_invitation_scope() == 'b2c'
            if not signup_allowed:
                partner.signup_prepare()
            partner.signup_get_auth_param()
            signup_url = partner._get_signup_url_for_action(url='/knowledge/article/%s' % article.id)[partner.id]
            return request.redirect(signup_url)

        return request.redirect('/web/login?redirect=/knowledge/article/%s' % article.id)

    def _redirect_to_backend_view(self, article):
        return request.redirect("/web#id=%s&model=knowledge.article&action=%s&menu_id=%s" % (
            article.id if article else '',
            request.env.ref("knowledge.knowledge_article_action_form").id,
            request.env.ref('knowledge.knowledge_menu_root').id
        ))

    def _check_sidebar_display(self):
        # exclude private articles as they are not used in the side panel.
        return request.env["knowledge.article"].search_count(
            [("parent_id", "=", False), ("category", "!=", "private")],
            limit=1,
        ) > 0

    def _redirect_to_portal_view(self, article, hide_side_bar=False):
        show_sidebar = False if hide_side_bar else self._check_sidebar_display()
        return request.render('knowledge.knowledge_article_view_frontend', {
            'article': article,
            'portal_readonly_mode': True,  # used to bypass access check (to speed up loading)
            'show_sidebar': show_sidebar
        })

    # ------------------------
    # Articles tree generation
    # ------------------------

    def _prepare_articles_tree_html_values(self, active_article_id, unfolded_articles_ids=False, unfolded_favorite_articles_ids=False):
        """ Prepares all the info needed to render the article tree view side panel
        and returns the rendered given template with those values.

        :param int active_article_id: used to highlight the given article_id in the template;
        :param unfolded_articles_ids: List of IDs used to display the children
          of the given article ids. Unfolded articles are saved into local storage.
          When reloading/opening the article page, previously unfolded articles
          nodes must be opened;
        :param unfolded_favorite_articles_ids: same as ``unfolded_articles_ids``
          but specific for 'Favorites' tree.
        """
        unfolded_articles_ids = set(unfolded_articles_ids or [])
        unfolded_favorite_articles_ids = set(unfolded_favorite_articles_ids or [])
        existing_ids = self._article_ids_exists(unfolded_articles_ids | unfolded_favorite_articles_ids)
        unfolded_articles_ids = unfolded_articles_ids & existing_ids
        unfolded_favorite_articles_ids = unfolded_favorite_articles_ids & existing_ids

        active_article_ancestor_ids = []
        if active_article_id:
            # determine the hierarchy to unfold based on parent_path and as sudo
            # this helps avoiding to actually fetch ancestors
            # this will not leak anything as it's just a set of IDS
            # displayed articles ACLs are correctly checked here below
            active_article = request.env['knowledge.article'].sudo().browse(active_article_id)
            active_article_ancestor_ids = active_article._get_ancestor_ids()
            unfolded_articles_ids |= active_article_ancestor_ids

        # fetch root article_ids as sudo, ACLs will be checked on next global call fetching 'all_visible_articles'
        # this helps avoiding 2 queries done for ACLs (and redundant with the global fetch)
        root_article_ids = request.env["knowledge.article"].sudo().search([("parent_id", "=", False)]).ids

        favorites_sudo = request.env['knowledge.article.favorite'].sudo()
        if not request.env.user._is_public():
            favorites_sudo = request.env['knowledge.article.favorite'].sudo().search([
                ("user_id", "=", request.env.user.id), ('is_article_active', '=', True)
            ])

        # Fetch all visible articles at once instead of going down the hierarchy in the template
        # using successive 'child_ids' field calls.
        # This allows to benefit from batch computation (ACLs, computes, ...).
        # We filter within the template based on the "parent_id" field to get the article children.
        all_visible_articles = request.env['knowledge.article']
        all_visible_articles_ids = unfolded_articles_ids | unfolded_favorite_articles_ids | set(root_article_ids)
        visible_favorite_article_ids = favorites_sudo.article_id.ids
        all_visible_article_domains = expression.OR([
            [
                ('id', 'child_of', all_visible_articles_ids),
                ('is_article_item', '=', False),
            ],
            [('id', 'in', visible_favorite_article_ids)],
        ])
        if all_visible_articles_ids:
            all_visible_articles = request.env['knowledge.article'].search(
                all_visible_article_domains,
                order='sequence, id',
            )
        root_articles = all_visible_articles.filtered(lambda article: not article.parent_id)

        user_write_access_by_article = {
            article.id: article.user_can_write
            for article in all_visible_articles
        }

        values = {
            "active_article_id": active_article_id,
            "active_article_ancestor_ids": active_article_ancestor_ids,
            "articles_displayed_limit": self._KNOWLEDGE_TREE_ARTICLES_LIMIT,
            "articles_displayed_offset": 0,
            "all_visible_articles": all_visible_articles,
            "user_write_access_by_article": user_write_access_by_article,
            "workspace_articles": root_articles.filtered(lambda article: article.category == 'workspace'),
            "shared_articles": root_articles.filtered(lambda article: article.category == 'shared'),
            "private_articles": root_articles.filtered(
                lambda article: article.category == "private" and article.user_has_write_access),
            "unfolded_articles_ids": unfolded_articles_ids,
            "unfolded_favorite_articles_ids": unfolded_favorite_articles_ids,
            'portal_readonly_mode': not request.env.user.has_group('base.group_user'),
            "favorites_sudo": favorites_sudo,
        }

        return values

    @http.route('/knowledge/tree_panel', type='json', auth='user')
    def get_tree_panel_all(self, active_article_id=False, unfolded_articles_ids=False, unfolded_favorite_articles_ids=False):
        template_values = self._prepare_articles_tree_html_values(
            active_article_id,
            unfolded_articles_ids=unfolded_articles_ids,
            unfolded_favorite_articles_ids=unfolded_favorite_articles_ids,
        )
        return request.env['ir.qweb']._render('knowledge.knowledge_article_tree', template_values)

    @http.route('/knowledge/tree_panel/portal', type='json', auth='public')
    def get_tree_panel_portal(self, active_article_id=False, unfolded_articles_ids=False, unfolded_favorite_articles_ids=False):
        """ Frontend access for left panel. """
        template_values = self._prepare_articles_tree_html_values(
            active_article_id,
            unfolded_articles_ids=unfolded_articles_ids,
            unfolded_favorite_articles_ids=unfolded_favorite_articles_ids
        )
        return request.env['ir.qweb']._render('knowledge.knowledge_article_tree_frontend', template_values)

    @http.route('/knowledge/tree_panel/portal/search', type='json', auth='public')
    def get_tree_panel_portal_search(self, search_term, active_article_id=False):
        """ Frontend access for left panel when making a search.
            Renders articles based on search term and ordered alphabetically.

            The tree is completely flattened (no sections nor child articles) to avoid noise
            (unnecessary parents display when children are matching) and redondancy (duplicated articles
            because of the favorite tree).

            :param int active_article_id: used to highlight the given article_id in the template;
            :param string search_term: user search term to filter the articles on;
        """

        # Get all the visible articles based on the search term
        all_visible_articles = request.env['knowledge.article'].search(
            expression.AND([[('is_article_item', '=', False)], [('name', 'ilike', search_term)]]),
            order='name',
            limit=self._KNOWLEDGE_TREE_ARTICLES_LIMIT,
        )

        values = {
            "search_tree": True, # Display the flatenned tree instead of the basic tree with sections
            "active_article_id": active_article_id,
            'portal_readonly_mode': not request.env.user.has_group('base.group_user'),
            'articles': all_visible_articles,
        }

        return request.env['ir.qweb']._render('knowledge.knowledge_article_tree_frontend', values)

    @http.route('/knowledge/tree_panel/children', type='json', auth='user')
    def get_tree_panel_children(self, parent_id):
        parent = request.env['knowledge.article'].search([('id', '=', parent_id)])
        if not parent:
            raise AccessError(_("This Article cannot be unfolded. Either you lost access to it or it has been deleted."))

        articles = parent.child_ids.filtered(
            lambda a: not a.is_article_item
        ).sorted("sequence") if parent.has_article_children else request.env['knowledge.article']
        return request.env['ir.qweb']._render('knowledge.articles_template', {
            'articles': articles,
            "articles_displayed_limit": self._KNOWLEDGE_TREE_ARTICLES_LIMIT,
            "articles_displayed_offset": 0,
            'portal_readonly_mode': not request.env.user.has_group('base.group_user'),  # used to bypass access check (to speed up loading)
            "user_write_access_by_article": {
                article.id: article.user_can_write
                for article in articles
            },
            "has_parent": True
        })

    @http.route('/knowledge/tree_panel/favorites', type='json', auth='user')
    def get_tree_panel_favorites(self, active_article_id=False, unfolded_favorite_articles_ids=False):
        unfolded_favorite_articles_ids = self._article_ids_exists(unfolded_favorite_articles_ids)

        favorites_sudo = request.env['knowledge.article.favorite'].sudo().search([
            ("user_id", "=", request.env.user.id), ('is_article_active', '=', True)
        ])

        all_visible_article_domains = expression.OR([
            [
                ('parent_id', 'child_of', favorites_sudo.article_id.ids),
                ('is_article_item', '=', False),
            ],
            [('id', 'in', favorites_sudo.article_id.ids)],
        ])

        all_visible_articles = request.env['knowledge.article'].search(all_visible_article_domains)

        return request.env['ir.qweb']._render('knowledge.knowledge_article_tree_favorites', {
            "favorites_sudo": favorites_sudo,
            "active_article_id": active_article_id,
            "all_visible_articles": all_visible_articles,
            "articles_displayed_limit": self._KNOWLEDGE_TREE_ARTICLES_LIMIT,
            "unfolded_favorite_articles_ids": unfolded_favorite_articles_ids,
            "portal_readonly_mode": not request.env.user.has_group('base.group_user'),  # used to bypass access check (to speed up loading)
            "user_write_access_by_article": {
                article.id: article.user_can_write
                for article in all_visible_articles
            },
        })

    @http.route('/knowledge/tree_panel/load_more', type='json', auth='user')
    def tree_panel_load_more(self, category, limit, offset, active_article_id=False, parent_id=False):
        """" Route called when loading more articles in a particular sub-tree.

        Fetching is done based either on a parent, either a category when no parent is given
        (in which case we retrieve the root articles of that category).
        "limit" and "offset" allow controlling the returned result size.

        In addition, if we receive an 'active_article_id', it is forcefully displayed even if not
        in the first 50 articles of its own subtree.
        (Subsequently, all his parents are also forcefully displayed).
        That allows the end-user to always see where he is situated within the articles hierarchy.

        See 'articles_template' template docstring for details. """

        if parent_id:
            parent_id = int(parent_id)
            articles_domain = [('parent_id', '=', parent_id)]
        elif category:
            # need to know in which category we are and filter accordingly
            articles_domain = self._get_load_more_roots_domain(category)
        else:
            raise werkzeug.exceptions.BadRequest()

        offset = int(offset)
        limit = int(limit)
        articles = request.env['knowledge.article'].search(
            articles_domain,
            limit=limit + 1,
            offset=offset,
            order='sequence, id',
        )

        if len(articles) < limit:
            articles_left_count = len(articles)
        else:
            articles_left_count = request.env['knowledge.article'].search_count(articles_domain) - offset

        active_article_ancestor_ids = []
        unfolded_articles_ids = []
        force_show_active_article = False
        if articles and active_article_id and active_article_id not in articles.ids:
            active_article_with_ancestors = request.env['knowledge.article'].search(
                [('id', 'parent_of', active_article_id)]
            )
            active_article = active_article_with_ancestors.filtered(
                lambda article: article.id == active_article_id)
            active_article_ancestors = active_article_with_ancestors - active_article
            unfolded_articles_ids = active_article_ancestors.ids

            # we only care about articles our current hierarchy (base domain)
            # and that are "next" (based on sequence of last article retrieved)
            force_show_domain = expression.AND([
                articles_domain,
                [('sequence', '>', articles[-1].sequence)]
            ])
            force_show_active_article = active_article.filtered_domain(force_show_domain)
            active_article_ancestors = active_article_ancestors.filtered_domain(force_show_domain)
            active_article_ancestor_ids = active_article_ancestors.ids

            if active_article_ancestors and not any(
                    ancestor_id in articles.ids for ancestor_id in active_article_ancestors.ids):
                articles |= active_article_ancestors

        return request.env['ir.qweb']._render('knowledge.articles_template', {
            "active_article_id": active_article_id,
            "active_article_ancestor_ids": active_article_ancestor_ids,
            "articles": articles,
            "articles_category": category,
            "articles_count": articles_left_count,
            "articles_displayed_limit": self._KNOWLEDGE_TREE_ARTICLES_LIMIT,
            "articles_displayed_offset": offset,
            "has_parent": bool(parent_id),
            "force_show_active_article": force_show_active_article,
            "portal_readonly_mode": not request.env.user.has_group('base.group_user'),  # used to bypass access check (to speed up loading)
            "unfolded_articles_ids": unfolded_articles_ids,
            "user_write_access_by_article": {
                article.id: article.user_can_write
                for article in articles
            },
        })

    def _get_load_more_roots_domain(self, category):
        """Given the section (category), returns the domain used to load more
        root articles of this section. In portal, we have both workspace and
        shared articles in the same section.
        """
        if category == "portal_shared":
            return [('parent_id', '=', False)]
        return [('parent_id', '=', False), ('category', '=', category)]

    @staticmethod
    def _article_ids_exists(articles_ids):
        if not articles_ids:
            return set()
        # we might get IDs from the localstorage that are not real records anymore (unlink, ...)
        # the 'child_of' operator using parent_path does not like that (will throw MissingRecord errors)
        # -> make sure we filter out children of existing articles
        return set(request.env['knowledge.article'].sudo().browse(articles_ids).exists().ids)

    # ------------------------
    # Article permission panel
    # ------------------------

    @http.route('/knowledge/get_article_permission_panel_data', type='json', auth='user')
    def get_article_permission_panel_data(self, article_id):
        """
        Returns a dictionary containing all values required to render the permission panel.
        :param article_id: (int) article id
        """
        article = request.env['knowledge.article'].search([('id', '=', article_id)])
        if not article:
            return werkzeug.exceptions.Forbidden()
        is_sync = not article.is_desynchronized
        # Get member permission info
        members_values = []
        members_permission = article._get_article_member_permissions(additional_fields={
            'res.partner': [
                ('name', 'partner_name'),
                ('email', 'partner_email'),
                ('partner_share', 'partner_share'),
            ],
            'knowledge.article': [
                ('icon', 'based_on_icon'),
                ('name', 'based_on_name'),
            ],
        })[article.id]

        based_on_articles = request.env['knowledge.article'].search([
            ('id', 'in', list(set(member['based_on'] for member in members_permission.values() if member['based_on'])))
        ])

        for partner_id, member in members_permission.items():
            # empty member added by '_get_article_member_permissions', don't show it in the panel
            if not member['member_id']:
                continue

            # if share partner and permission = none, don't show it in the permission panel.
            if member['permission'] == 'none' and member['partner_share']:
                continue

            # if article is desyncronized, don't show members based on parent articles.
            if not is_sync and member['based_on']:
                continue

            member_values = {
                'id': member['member_id'],
                'partner_id': partner_id,
                'partner_name': member['partner_name'],
                'partner_email': member['partner_email'] if not member['partner_share'] or partner_id == request.env.user.partner_id.id or request.env.user._is_internal() else False,
                'permission': member['permission'],
                'based_on': f'{member["based_on_icon"] or "📄"} {member["based_on_name"]}' if member['based_on_name'] else False,
                'based_on_id': member['based_on'] if member['based_on'] in based_on_articles.ids else False,
                'partner_share': member['partner_share'],
                'is_unique_writer': member['permission'] == "write" and article.inherited_permission != "write" and not any(
                    other_member['permission'] == 'write'
                    for partner_id, other_member in members_permission.items()
                    if other_member['member_id'] != member['member_id']
                ),
            }
            members_values.append(member_values)

        internal_permission_field = request.env['knowledge.article']._fields['internal_permission']
        permission_field = request.env['knowledge.article.member']._fields['permission']
        user_is_admin = request.env.user._is_admin()
        parent_article_sudo = article.parent_id.sudo()
        inherited_permission_parent_sudo = article.inherited_permission_parent_id.sudo()

        return {
            'internal_permission_options': internal_permission_field.get_description(request.env).get('selection', []),
            'internal_permission': article.inherited_permission,
            'category': article.category,
            'parent_permission': parent_article_sudo.inherited_permission,
            'based_on': inherited_permission_parent_sudo.display_name,
            'based_on_id': inherited_permission_parent_sudo.id if inherited_permission_parent_sudo.user_has_access else False,
            'members_options': permission_field.get_description(request.env).get('selection', []),
            'members': members_values,
            'is_sync': is_sync,
            'parent_id': parent_article_sudo.id if parent_article_sudo.user_has_access else False,
            'parent_name': parent_article_sudo.display_name,
            'user_is_admin': user_is_admin,
            'show_admin_tip': user_is_admin and article.user_permission != 'write',
        }

    @http.route('/knowledge/article/set_member_permission', type='json', auth='user')
    def article_set_member_permission(self, article_id, permission, member_id=False, inherited_member_id=False):
        """ Sets the permission of the given member for the given article.

        The returned result can also include a `reload_tree` entry that tells the
        caller that the aside block listing all articles should be reloaded. This
        happens when the article moves from one section to another.

        **Note**: The user needs "write" permission to change the permission of a user.

        :param int article_id: target article id;
        :param string permission: permission to set on member, one of 'none',
          'read' or 'write';
        :param int member_id: id of a member of the given article;
        :param int inherited_member_id: id of a member from one of the article's
          parent (indicates rights are inherited from parents);
        """
        article = request.env['knowledge.article'].search([('id', '=', article_id)])
        if not article:
            return werkzeug.exceptions.Forbidden()
        member = request.env['knowledge.article.member'].browse(member_id or inherited_member_id).exists()
        if not member:
            return {'error': _("The selected member does not exists or has been already deleted.")}

        previous_category = article.category

        try:
            article._set_member_permission(member, permission, bool(inherited_member_id))
        except (AccessError, ValidationError):
            return {'error': _("You cannot change the permission of this member.")}

        if article.category != previous_category:
            return {'reload_tree': True}

        return {}

    @http.route('/knowledge/article/remove_member', type='json', auth='user')
    def article_remove_member(self, article_id, member_id=False, inherited_member_id=False):
        """ Removes the given member from the given article.

        The returned result can also include a `reload_tree` entry that tells the
        caller that the aside block listing all articles should be reloaded. This
        happens when the article moves from one section to another.

        **Note**: The user needs "write" permission to remove another member from
        the list. The user can always remove themselves from the list.

        :param int article_id: target article id;
        :param int member_id: id of a member of the given article;
        :param int inherited_member_id: id of a member from one of the article's
          parent (indicates rights are inherited from parents);
        """
        article = request.env['knowledge.article'].search([('id', '=', article_id)])
        if not article:
            return werkzeug.exceptions.Forbidden()
        member = request.env['knowledge.article.member'].browse(member_id or inherited_member_id).exists()
        if not member:
            return {'error': _("The selected member does not exists or has been already deleted.")}

        previous_category = article.category
        partner = member.partner_id

        try:
            article._remove_member(member)
        except (AccessError, ValidationError) as e:
            return {'error': e}

        if partner == request.env.user.partner_id and article.category == 'private':
            # When leaving private article, the article will be archived instead
            # As a result, user won't see the article anymore and the home page
            # should be fully reloaded to open the first 'available' article.
            return {'reload_all': True}
        elif article.category != previous_category:
            return {'reload_tree': True}

        return {}

    @http.route('/knowledge/article/set_internal_permission', type='json', auth='user')
    def article_set_internal_permission(self, article_id, permission):
        """ Sets the internal permission of the given article.

        The returned result can also include a `reload_tree` entry that tells the
        caller that the aside block listing all articles should be reloaded. This
        happens when the article moves from one section to another.

        **Note**: The user needs "write" permission to update the internal permission
        of the article.

        :param int article_id: target article id;
        :param string permission: permission to set on member, one of 'none',
          'read' or 'write';
        """
        article = request.env['knowledge.article'].search([('id', '=', article_id)])
        if not article:
            return werkzeug.exceptions.Forbidden()

        previous_category = article.category

        try:
            article._set_internal_permission(permission)
        except (AccessError, ValidationError):
            return {'error': _("You cannot change the internal permission of this article.")}

        if article.category != previous_category:
            return {'reload_tree': True}
        return {}
