# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class AccountBatchPayment(models.Model):
    _inherit = 'account.batch.payment'

    def _get_payment_vals(self, payment):
        res = super()._get_payment_vals(payment)
        if self.journal_id.sepa_pain_version == 'pain.001.001.09':
            res['sepa_uetr'] = payment.sepa_uetr

        return res
