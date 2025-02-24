# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Import(models.TransientModel):

    _inherit = 'base_import.import'

    def get_file_data(self, options):
        return super(Import, self)._read_file(options)
