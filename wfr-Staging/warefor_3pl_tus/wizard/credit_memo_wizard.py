# -*- coding: utf-8 -*-

from odoo import _, api, models, fields
from odoo.exceptions import UserError


class CustomCreditMemoWizard(models.TransientModel):
    _name = 'custom.credit.memo.wizard'
    _description = 'Custom Credit Memo Wizard'

    invoice_id = fields.Many2one(comodel_name="account.move", string="Credit Memo")

    def create_credit_memo(self):
        credit_memo = self.invoice_id.action_reverse()
        return credit_memo
