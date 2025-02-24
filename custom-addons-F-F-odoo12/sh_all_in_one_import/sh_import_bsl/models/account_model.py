# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    def sh_import_bsl(self):
        if self:
            action = self.env.ref(
                'sh_all_in_one_import.sh_import_bsl_action').read()[0]
            return action
