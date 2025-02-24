# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.depends('amount')
    def _compute_unreconciled_amount(self):
        for rec in self:
            total = rec.amount - sum(rec.reconciled_invoice_ids.mapped('amount_total'))
            rec.unreconciled_amount = total >= 0 and total or 0

    pallet_id = fields.Many2one(comodel_name="pallet.batch.tus", string="Pallet")
    unreconciled_amount = fields.Float(string="Unreconciled Amount", compute=_compute_unreconciled_amount)
