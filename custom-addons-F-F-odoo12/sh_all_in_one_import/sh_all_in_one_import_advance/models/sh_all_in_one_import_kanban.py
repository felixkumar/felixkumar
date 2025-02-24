# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields


class ShAllInOneBasicKanban(models.Model):
    _name = 'sh.all.in.one.import.kanban'
    _description = 'All In One Import Kanban'

    name = fields.Char("Name")
