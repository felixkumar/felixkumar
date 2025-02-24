# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields

class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    l10n_br_avatax_code = fields.Char('Avatax Code', help='Technical field containing the Avatax identifier for this tax.', readonly=True)

    def _get_tax_vals(self, company, tax_template_to_tax):
        vals = super()._get_tax_vals(company, tax_template_to_tax)
        if self.l10n_br_avatax_code:
            vals['l10n_br_avatax_code'] = self.l10n_br_avatax_code
        return vals


class AccountTax(models.Model):
    _inherit = 'account.tax'

    l10n_br_avatax_code = fields.Char('Avatax Code', help='Technical field containing the Avatax identifier for this tax.', readonly=True)
