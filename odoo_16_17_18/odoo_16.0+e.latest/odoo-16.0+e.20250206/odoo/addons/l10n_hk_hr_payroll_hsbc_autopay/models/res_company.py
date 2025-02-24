# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_hk_autopay = fields.Boolean(string="Payroll with HSBC Autopay payment")
    l10n_hk_autopay_type = fields.Selection(
        selection=[('h2h', "H2H Submission"), ('hsbcnet', "HSBCnet File Upload")],
        string="Autopay Type", help="H2H Submission: Directly submit to HSBC. HSBCnet File Upload: Upload file to HSBCnet.",
        default='h2h',
    )
    l10n_hk_autopay_partner_bank_id = fields.Many2one(string="Autopay Account", comodel_name='res.partner.bank', copy=False)
