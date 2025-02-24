from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _pos_data_process(self, loaded_data):
        # EXTENDS 'point_of_sale'
        super()._pos_data_process(loaded_data)
        if self.company_id.account_fiscal_country_id.code == 'PE':
            loaded_data['l10n_pe_edi_refund_reason'] = [
                {'value': s.value, 'name': s.name}
                for s in self.env['ir.model.fields']._get('account.move', 'l10n_pe_edi_refund_reason').selection_ids
            ]
