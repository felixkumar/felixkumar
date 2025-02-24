# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from uuid import uuid4

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    # needed to hide the UETR field conditionally depending on the version
    sepa_pain_version = fields.Selection(related='journal_id.sepa_pain_version')
    sepa_uetr = fields.Char(
        string='UETR',
        compute='_compute_sepa_uetr',
        store=True,
        help='Unique end-to-end transaction reference',
    )

    @api.depends('payment_method_id')
    def _compute_sepa_uetr(self):
        # don't make changes to the existing uetr even if the pain version changes
        # add uetr only on payments with a SEPA credit transfer
        payments = self.filtered(
            lambda p: not p.sepa_uetr and p.payment_method_id.code == 'sepa_ct'
        )
        for payment in payments:
            payment.sepa_uetr = uuid4() if payment.journal_id.sepa_pain_version == 'pain.001.001.09' else False
