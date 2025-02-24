# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def sh_import_ail(self):
        if self:
            action = self.env.ref(
                'sh_all_in_one_import.sh_import_ail_action').read()[0]
            return action
