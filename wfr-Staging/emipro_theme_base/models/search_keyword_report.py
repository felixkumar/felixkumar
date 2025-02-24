# -*- coding: utf-8 -*-
from odoo import fields, models


class SearchKeywordReport(models.Model):
    """This model is used to store details of searched keywords on website."""
    _name = "search.keyword.report"
    _description = "Search Keyword Report"
    _order = "id desc"

    search_term = fields.Char(string='Search Keyword', help='Search term used while searching on website.',
                              required=True)
    no_of_products_in_result = fields.Integer(string='Number of Products in Result', group_operator=False,
                                              help='Number of products which are returned in result of search using '
                                                   'this keyword')
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user,
                              help='User who searched performed this search operation.')
