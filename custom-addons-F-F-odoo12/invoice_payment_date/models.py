from odoo import models, fields, api
#from datetime import datetime

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    payment_date = fields.Date(string='Last Payment Date', compute='_compute_payment_date')
    payment_days = fields.Integer(string='Payment Days', compute='_compute_payment_days')
    all_payment_dates = fields.Char(string='All Payment Dates', compute='_compute_all_payment_dates')
    #average_payment_days = fields.Float(string='Average Payment Days', compute='_compute_average_payment_days', digits=(6, 2))


    @api.depends('payment_ids')
    def _compute_payment_date(self):
        for invoice in self:
            payments = invoice.payment_ids.filtered(lambda p: p.state == 'posted' and p.payment_date)
            if payments:
                invoice.payment_date = max(payments.mapped('payment_date'))
            else:
                invoice.payment_date = False

    @api.depends('date_invoice', 'payment_date')
    def _compute_payment_days(self):
        for invoice in self:
            if invoice.date_invoice and invoice.payment_date:
                date_invoice = fields.Date.from_string(invoice.date_invoice)
                payment_date = fields.Date.from_string(invoice.payment_date)
                delta = (payment_date - date_invoice).days
                invoice.payment_days = delta
            else:
                invoice.payment_days = 0
                
                
    @api.depends('payment_ids')
    def _compute_all_payment_dates(self):
        for invoice in self:
            payments = invoice.payment_ids.filtered(lambda p: p.state == 'posted' and p.payment_date)
            payment_dates = [fields.Date.to_string(p.payment_date) for p in payments]
            formatted_dates = [f"{date.split('-')[1]}/{date.split('-')[2]}/{date.split('-')[0]}" for date in payment_dates]
            invoice.all_payment_dates = ', '.join(formatted_dates) if formatted_dates else ''
            
            
    #@api.depends('payment_days')
    #def _compute_average_payment_days(self):
        #for invoice in self:
            #total_days = invoice.payment_days
            #invoice_count = 1  # Since we are dealing with a single invoice in the loop

            # If you want to consider all selected invoices together, calculate outside the loop.
            #invoice.average_payment_days = round(total_days / invoice_count, 2) if invoice_count > 0 else 0.0

