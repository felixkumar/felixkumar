# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class AccountFiscalPositionTemplate(models.Model):
    _inherit = 'account.fiscal.position.template'

    l10n_br_is_avatax = fields.Boolean('Use Avatax Brazil API')


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    l10n_br_is_avatax = fields.Boolean('Use Avatax Brazil API')
