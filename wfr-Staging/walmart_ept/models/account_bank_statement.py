from odoo import models

class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    def button_reopen(self):
        """
        Reopen statement
        :return: Super method.
        """
        statements = self.env['walmart.reconciliation.report.ept'].search([('statement_id', 'in', self.ids)])
        if statements:
            statements.write({'state': 'partially_processed'})
        return super(AccountBankStatement, self).button_reopen()
