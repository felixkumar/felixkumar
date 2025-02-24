from odoo import fields, models


# Cash Ledger report model
class CashLedgerReport(models.Model):
    _name = "cash.report"
    _description = "Cash Ledger Report"
    
    date = fields.Date(string='Date', index=True, store=True, copy=False)
    account_id = fields.Many2one('account.account', string="Account Name") 
    amount = fields.Float(string='Payment Amount')
    balance = fields.Float(string='Balance')
    transaction_type = fields.Selection([('Receipt', 'Receipt'), ('Payment', 'Payment')])
    ref = fields.Char(string='Reference')
