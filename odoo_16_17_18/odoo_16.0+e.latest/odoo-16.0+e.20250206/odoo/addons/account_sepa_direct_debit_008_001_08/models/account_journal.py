from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    debit_sepa_pain_version = fields.Selection(
        [
            ('pain.008.001.02', 'Default (Pain 008.001.02)'),
            ('pain.008.001.08', 'Updated 2023 (Pain 008.001.08)'),
        ],
        required=True,
        string='SEPA Direct Debit Pain Version',
        default='pain.008.001.02',
    )

    def _get_debit_sepa_pain_version(self):
        # OVERRIDE to return the selected DDS version rather than the default one
        self.ensure_one()
        return self.debit_sepa_pain_version
