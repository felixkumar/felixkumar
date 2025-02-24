# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests.common import tagged
from odoo.addons.base.tests.common import HttpCaseWithUserPortal


@tagged('post_install', '-at_install', 'knowledge_portal_search', 'knowledge_tour')
class TestKnowledgePortalSearch(HttpCaseWithUserPortal):
    """ Test portal search tree rendering. """

    def test_knowledge_search_flow_portal(self):
        """This tour will check that the portal search bar tree rendering is properly updated"""

        # Create articles to populate portal tree
        #
        # - My Article
        #       - Child Article
        # - Sibling Article
        portal_partner_id = self.partner_portal.id

        my_article = self.env['knowledge.article'].create([{
            'name': 'My Article',
            'parent_id': False,
            'internal_permission': 'write',
            'article_member_ids': [(0, 0, {
                'partner_id': portal_partner_id,
                'permission': 'read',
                })
             ],
        }])
        self.env['knowledge.article'].create([{
            'name': 'Child Article',
            'parent_id': my_article.id,
            'internal_permission': 'write',
            'article_member_ids': [(0, 0, {
                'partner_id': portal_partner_id,
                'permission': 'read',
                })
             ],
        }])
        self.env['knowledge.article'].create([{
            'name': 'Sibling Article',
            'parent_id': False,
            'internal_permission': 'write',
            'article_member_ids': [(0, 0, {
                'partner_id': portal_partner_id,
                'permission': 'read',
                })
             ],
        }])
        self.assertEqual(my_article.favorite_count, 0)
        self.start_tour('/knowledge/article/%s' % my_article.id, 'knowledge_portal_search_tour', login='portal', step_delay=100)

        # Check that 'My Article' has correctly been set as favorite by the user
        self.assertEqual(my_article.favorite_count, 1)
