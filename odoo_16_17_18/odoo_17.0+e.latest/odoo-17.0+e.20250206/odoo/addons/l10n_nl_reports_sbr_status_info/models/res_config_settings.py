# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_nl_reports_sbr_password = fields.Char(related="company_id.l10n_nl_reports_sbr_password", readonly=False)
