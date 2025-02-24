# -*- coding: utf-8 -*-

from itertools import chain
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class SynonymGroup(models.Model):
    _name = "synonym.group"
    _description = "Synonym Group"
    _order = "id desc"

    name = fields.Char(string='Synonyms Group', required=True,
                       help='Synonyms Group with comma separated keywords(Eg., Mobile,Smartphone,Cellphone)')
    website_id = fields.Many2one(string="Website", comodel_name="website",
                                 help="This group will only accessible for specified website. "
                                      "Accessible for all websites if not specified!")

    @api.constrains("name")
    def check_group_name(self):
        """
        Constraint for name field for same synonym in same group or exist in other group.
        @author: Maulik Barad on Date 11-Nov-2022.
        """
        for group in self:
            synonym_list = [v.strip() for v in group.name.split(',')]
            if len(set(synonym_list)) != len(synonym_list):
                exist = {synonym for synonym in synonym_list if synonym_list.count(synonym) > 1}
                raise ValidationError("You have entered '%s' multiple times.\n "
                                      "\nMake sure that each synonym is entered only once!" % ', '.join(exist))
            groups = self.search_read([("id", "!=", group.id)], fields=['name'])
            for synonym in synonym_list:
                name_list = chain.from_iterable([g.get('name').split(',') for g in groups])
                if synonym in name_list:
                    raise ValidationError("%s, Synonym is exist in another group." % (synonym.capitalize()))
