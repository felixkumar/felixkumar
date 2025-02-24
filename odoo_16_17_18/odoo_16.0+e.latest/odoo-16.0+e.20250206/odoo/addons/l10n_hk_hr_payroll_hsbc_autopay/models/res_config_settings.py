# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_hk_autopay = fields.Boolean(
        related='company_id.l10n_hk_autopay',
        string="Payroll with HSBC Autopay payment", readonly=False,
    )
    l10n_hk_autopay_type = fields.Selection(
        related='company_id.l10n_hk_autopay_type', readonly=False,
        string="Autopay Type", help="H2H Submission: Directly submit to HSBC. HSBCnet File Upload: Upload file to HSBCnet.",
    )
    l10n_hk_autopay_partner_bank_id = fields.Many2one(
        related='company_id.l10n_hk_autopay_partner_bank_id',
        comodel_name='res.partner.bank',
        string="Autopay Account", readonly=False,
    )
