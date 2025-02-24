from odoo import models


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    def _inverse_foreign_vat(self):
        # EXTENDS account
        super()._inverse_foreign_vat()
        for fpos in self:
            if fpos.foreign_vat:
                fpos._create_draft_closing_move_for_foreign_vat()

    def _create_draft_closing_move_for_foreign_vat(self):
        self.ensure_one()
        existing_draft_closings = self.env['account.move'].search([('tax_closing_end_date', '!=', False), ('state', '=', 'draft')])
        for closing_date in set(existing_draft_closings.mapped('date')):
            self.company_id._get_and_update_tax_closing_moves(closing_date, self)
