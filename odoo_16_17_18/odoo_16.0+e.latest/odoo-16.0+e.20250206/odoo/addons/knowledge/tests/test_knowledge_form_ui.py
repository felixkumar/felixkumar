# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
import base64
import io
import os
from PIL import Image
from unittest import skipIf
from odoo import fields
from odoo.addons.base.tests.common import HttpCaseWithUserDemo
from odoo.tests.common import tagged


class TestKnowledgeUICommon(HttpCaseWithUserDemo):
    @classmethod
    def setUpClass(cls):
        super(TestKnowledgeUICommon, cls).setUpClass()
        # remove existing articles to ease tour management
        cls.env['knowledge.article'].with_context(active_test=False).search([]).unlink()

@tagged('post_install', '-at_install', 'knowledge', 'knowledge_tour')
class TestKnowledgeUI(TestKnowledgeUICommon):

    def test_knowledge_load_more(self):
        """ The goal of this tour is to test the behavior of the 'load more' feature.
        Sub-trees of the articles are loaded max 50 by 50.

        The parent articles are hand-picked with specific index because it allows testing
        that we force the display of the parents of the active article. """

        root_articles = self.env['knowledge.article'].create([{
            'name': 'Root Article %i' % index
        } for index in range(153)])

        children_articles = self.env['knowledge.article'].create([{
            'name': 'Child Article %i' % index,
            'parent_id': root_articles[103].id,
        } for index in range(254)])

        self.env['knowledge.article'].create([{
            'name': 'Grand-Child Article %i' % index,
            'parent_id': children_articles[203].id,
        } for index in range(344)])

        self.start_tour('/web', 'knowledge_load_more_tour', login='admin', step_delay=100)

    def test_knowledge_main_flow(self):

        # Patching 'now' to allow checking the order of trashed articles, as
        # they are sorted using their deletion date which is based on the
        # 'write_date' field
        self.patch(self.env.cr, 'now', lambda: fields.Datetime.now() - timedelta(days=1))
        article_1 = self.env['knowledge.article'].create({
            'name': 'Article 1',
            'active': False,
            'to_delete': True,
        })
        article_1.flush_recordset()

        # as the knowledge.article#_resequence method is based on write date
        # force the write_date to be correctly computed
        # otherwise it always returns the same value as we are in a single transaction
        self.patch(self.env.cr, 'now', fields.Datetime.now)
        self.env['knowledge.article'].create({
            'name': 'Article 2',
            'active': False,
            'to_delete': True,
        })

        self.start_tour('/web', 'knowledge_main_flow_tour', login='admin', step_delay=100)

        # check our articles were correctly created
        # with appropriate default values (section / internal_permission)
        private_article = self.env['knowledge.article'].search([('name', '=', 'My Private Article')])
        self.assertTrue(bool(private_article))
        self.assertEqual(private_article.category, 'private')
        self.assertEqual(private_article.internal_permission, 'none')

        workspace_article = self.env['knowledge.article'].search([('name', '=', 'My Workspace Article')])
        self.assertTrue(bool(workspace_article))
        self.assertEqual(workspace_article.category, 'workspace')
        self.assertEqual(workspace_article.internal_permission, 'write')

        children_workspace_articles = workspace_article.child_ids.sorted('sequence')
        self.assertEqual(len(children_workspace_articles), 2)

        child_article_1 = children_workspace_articles.filtered(
            lambda article: article.name == 'Child Article 1')
        child_article_2 = children_workspace_articles.filtered(
            lambda article: article.name == 'Child Article 2')

        # as we re-ordered children, article 2 should come first
        self.assertEqual(children_workspace_articles[0], child_article_2)
        self.assertEqual(children_workspace_articles[1], child_article_1)

        # workspace article should have one partner invited on it
        invited_member = workspace_article.article_member_ids
        self.assertEqual(len(invited_member), 1)
        invited_partner = invited_member.partner_id
        self.assertEqual(len(invited_partner), 1)
        self.assertEqual(invited_partner.name, 'micheline@knowledge.com')
        self.assertEqual(invited_partner.email, 'micheline@knowledge.com')
        # check that the partner received an invitation link
        invitation_message = self.env['mail.message'].search([
            ('partner_ids', 'in', invited_partner.id)
        ])
        self.assertEqual(len(invitation_message), 1)
        self.assertIn(
            workspace_article._get_invite_url(invited_partner),
            invitation_message.body
        )

        # as we re-ordered our favorites, private article should come first
        article_favorites = self.env['knowledge.article.favorite'].search([])
        self.assertEqual(len(article_favorites), 2)
        self.assertEqual(article_favorites[0].article_id, private_article)
        self.assertEqual(article_favorites[1].article_id, workspace_article)

    def test_knowledge_pick_emoji(self):
        """This tour will check that the emojis of the form view are properly updated
           when the user picks an emoji from an emoji picker."""
        self.start_tour('/web', 'knowledge_pick_emoji_tour', login='admin', step_delay=100)

    def test_knowledge_cover_selector(self):
        """Check the behaviour of the cover selector when unsplash credentials
        are not set.
        """
        with io.BytesIO() as f:
            Image.new('RGB', (50, 50)).save(f, 'PNG')
            f.seek(0)
            image = base64.b64encode(f.read())
        attachment = self.env['ir.attachment'].create({
            'name': 'odoo_logo.png',
            'datas': image,
            'res_model': 'knowledge.cover',
            'res_id': 0,
        })
        self.env['knowledge.cover'].create({'attachment_id': attachment.id})
        self.start_tour('/web', 'knowledge_cover_selector_tour', login='admin')

    def test_knowledge_readonly_favorite(self):
        """Make sure that a user can add readonly articles to its favorites and
        resequence them.
        """
        articles = self.env['knowledge.article'].create([{
            'name': 'Readonly Article 1',
            'internal_permission': 'read',
            'article_member_ids': [(0, 0, {
                'partner_id': self.env.ref('base.partner_admin').id,
                'permission': 'write',
            })]
        }, {
            'name': 'Readonly Article 2',
            'internal_permission': False,
            'article_member_ids': [(0, 0, {
                'partner_id': self.env.ref('base.partner_admin').id,
                'permission': 'write',
            }), (0, 0, {
                'partner_id': self.partner_demo.id,
                'permission': 'read',
            })]
        }])

        self.start_tour('/knowledge/article/%s' % articles[0].id, 'knowledge_readonly_favorite_tour', login='demo', step_delay=100)

        self.assertTrue(articles[0].with_user(self.user_demo.id).is_user_favorite)
        self.assertTrue(articles[1].with_user(self.user_demo.id).is_user_favorite)
        self.assertGreater(
            articles[0].with_user(self.user_demo.id).user_favorite_sequence,
            articles[1].with_user(self.user_demo.id).user_favorite_sequence,
        )

    def test_knowledge_resequence_children_of_readonly_parent_tour(self):
        """Make sure that a user can move children articles under a readonly
        parent.
        """
        parent = self.env['knowledge.article'].create({
            'name': 'Readonly Parent',
            'internal_permission': 'read',
            'article_member_ids': [(0, 0, {
                'partner_id': self.env.ref('base.partner_admin').id,
                'permission': 'write',
            })]
        })
        self.env['knowledge.article'].create([{
            'name': 'Child 1',
            'internal_permission': 'write',
            'sequence': 1,
            'parent_id': parent.id,
        }, {
            'name': 'Child 2',
            'internal_permission': 'write',
            'sequence': 2,
            'parent_id': parent.id,
        }])
        self.start_tour('/knowledge/article/%s' % parent.id, 'knowledge_resequence_children_of_readonly_parent_tour', login='demo')

    def test_knowledge_properties_tour(self):
        """Test article properties panel"""
        parent_article = self.env['knowledge.article'].create([{
            'name': 'ParentArticle',
            'sequence': 1,
        }, {
            'name': 'InheritPropertiesArticle',
            'sequence': 2,
        }])[0]
        self.env['knowledge.article'].create({
            'name': 'ChildArticle',
            'parent_id': parent_article.id
        })
        self.start_tour('/web', 'knowledge_properties_tour', login='admin')

@tagged('external', 'post_install', '-at_install')
@skipIf(not os.getenv("UNSPLASH_APP_ID") or not os.getenv("UNSPLASH_ACCESS_KEY"), "no unsplash credentials")
class TestKnowledgeUIWithUnsplash(TestKnowledgeUICommon):
    @classmethod
    def setUpClass(cls):
        super(TestKnowledgeUIWithUnsplash, cls).setUpClass()

        cls.UNSPLASH_APP_ID = os.getenv("UNSPLASH_APP_ID")
        cls.UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

        cls.env["ir.config_parameter"].set_param("unsplash.app_id", cls.UNSPLASH_APP_ID)
        cls.env["ir.config_parameter"].set_param("unsplash.access_key", cls.UNSPLASH_ACCESS_KEY)

    def test_knowledge_cover_selector_unsplash(self):
        """Check the behaviour of the cover selector when unsplash credentials
        are set.
        """
        self.start_tour('/web', 'knowledge_random_cover_tour', login='demo')
