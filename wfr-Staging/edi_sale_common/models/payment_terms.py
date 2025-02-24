from odoo import api, fields, models


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    edi_description = fields.Char(string='Description')
    edi_type = fields.Char(string='Type')
    edi_basis_date_code = fields.Char(string='Basis Date Code')
    edi_discount_percentage = fields.Char(string='Discount Percentage')
    edi_discount_date = fields.Char(string='Discount Date')
    edi_discount_due_days = fields.Char(string='Discount Due Days')
    edi_net_due_date = fields.Char(string='Net Due Date')
    edi_net_due_days = fields.Char(string='Net Due Days')
