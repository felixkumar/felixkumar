from odoo import models, fields, api
from datetime import datetime as date
import calendar


#  cash ledger wizard model
class Cashledgerwizard(models.TransientModel):
    _name = 'cash.ledger.wizard'
    _description = "Cash Ledger Wizard"

    start_date = fields.Datetime(string="Start Date", required=True, default=fields.datetime.today())
    end_date = fields.Datetime(string="End Date")

# submit button method for cash ledger report
    @api.multi
    def submit_data(self):
        report_records = self.report_cash_data()
        self.env.cr.execute("""delete from cash_report""")
        for receipt_data in  report_records.get('receipt'):
            value = {'date' : receipt_data.get('date') ,
                    'account_id': receipt_data.get('account_id') ,
                    'amount':receipt_data.get('amount'),
                    'balance': receipt_data.get('balance'),
                    'transaction_type':'Receipt',
                    'ref' : receipt_data.get('ref'),
                    }
            self.env['cash.report'].create(value)
        for payment_data in  report_records.get('payment'):
            value = {'date' : payment_data.get('date') ,
                    'account_id': payment_data.get('account_id') ,
                    'amount':payment_data.get('amount'),
                    'balance': payment_data.get('balance'),
                    'transaction_type':'Payment',
                    'ref' : payment_data.get('ref'),
                    }
            self.env['cash.report'].create(value)
        return {
            'name': 'Cash Ledger Reports',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'cash.report',
            'help': '''This report gives analysis of cash ledger transactions.''',
        }

    @api.multi
    def submit_graph(self):
        report_records = self.report_cash_data()
        self.env.cr.execute("""delete from cash_report""")
        for receipt_data in  report_records.get('receipt'):
            value = {'date' : receipt_data.get('date') ,
                    'account_id': receipt_data.get('account_id') ,
                    'amount':receipt_data.get('amount'),
                    'balance': receipt_data.get('balance'),
                    'transaction_type':'Receipt',
                    'ref' : receipt_data.get('ref'),
                    }
            self.env['cash.report'].create(value)
        for payment_data in  report_records.get('payment'):
            value = {'date' : payment_data.get('date') ,
                    'account_id': payment_data.get('account_id') ,
                    'amount':payment_data.get('amount'),
                    'balance': payment_data.get('balance'),
                    'transaction_type':'Payment',
                    'ref' : payment_data.get('ref'),
                    }
            self.env['cash.report'].create(value)
        return {
            'name': 'Cash Ledger Reports',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'graph',
            'res_model': 'cash.report',
            'help': '''This report gives analysis of cash ledger transactions.''',
        }
    # common method for print pdf or xls file
    def report_cash_data(self):
        move_line_obj = self.env['account.move.line']
        total_payment = 0.0
        total_receipt = 0.0
        old_payment_ids = move_line_obj.search([('credit', '>', 0), ('date', '<', self.start_date), ('journal_id.type', '=', 'cash')])
        old_payments = move_line_obj.read_group([('credit', '>', 0), ('date', '<', self.start_date), ('user_type_id', '=', 3),('user_type_id', '=', 3), ('journal_id.type', '=', 'cash')], [ 'account_id', 'credit', 'debit'], [])
        old_receipt_ids = move_line_obj.search([('debit', '>', 0), ('date', '<', self.start_date), ('journal_id.type', '=', 'cash')])
        old_receipt = move_line_obj.read_group([('debit', '>', 0), ('date', '<', self.start_date), ('user_type_id', '=', 3), ('journal_id.type', '=', 'cash')], [ 'account_id', 'credit', 'debit'], [])
        opening_balance = (old_receipt_ids or old_payment_ids) and (old_receipt[0].get('debit') - old_payments[0].get('credit')) or 0.0
        current_receipts = move_line_obj.search([('debit', '>', 0), \
                                                 ('user_type_id', '=', 3), \
                                                 ('date', '>=', self.start_date), ('date', '<=', self.end_date), \
                                                 ('journal_id.type', '=', 'cash')])
        current_payment = move_line_obj.search([('credit', '>', 0), \
                                                 ('date', '>=', self.start_date), ('date', '<=', self.end_date), \
                                                 ('journal_id.type', '=', 'cash'),('user_type_id', '=', 3)])
        data = {'receipt':[], 'payment':[]}
        for receipt in current_receipts:
            total_receipt += receipt.debit
            data['receipt'].append({'date' : receipt.date,'account_id':receipt.account_id.id, 'amount' : receipt.debit, 'balance' : receipt.balance, 'ref':receipt.ref})
        for payment in current_payment:
            total_payment += payment.credit
            data['payment'].append({'date' : payment.date,'account_id':payment.account_id.id, 'amount' : payment.credit, 'balance' : payment.balance, 'ref' : payment.ref})
        
        closing_bal = opening_balance + (total_receipt - total_payment)
        data.update({
            'opening_balance_receipt' : opening_balance,
            'closing_bal_payment' :closing_bal})
        return data
#     cash ledger print pdf report method
    @api.multi
    def print_report(self):
        data = {}
        data['form'] = self.read(
            ['start_date', 'end_date'])[0]
        cash = self.report_cash_data()
        data['form']['opening_balance_receipt'] = cash['opening_balance_receipt']
        data['form']['closing_bal_payment'] = cash['closing_bal_payment']
        self.env.cr.execute("""delete from cash_report""")
        for receipt_data in  cash.get('receipt'):
            value = {'date' : receipt_data.get('date') ,
                     'account_id': receipt_data.get('account_id') ,
                    'amount':receipt_data.get('amount'),
                    'balance': receipt_data.get('balance'),
                    'transaction_type':'Receipt',
                    'ref' : receipt_data.get('ref')
                    }
            self.env['cash.report'].create(value)
        for payment_data in  cash.get('payment'):
            value = {'date' : payment_data.get('date') ,
                     'account_id': payment_data.get('account_id') ,
                    'amount':payment_data.get('amount'),
                    'balance': payment_data.get('balance'),
                    'transaction_type':'Payment',
                    'ref' : payment_data.get('ref')
                    }
            self.env['cash.report'].create(value)

        return self.env.ref('itmcs_statistical_reports.report_cashledger').report_action(self, data=data)
    
    #  method for xls download button
    @api.multi
    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        ctx = self.report_cash_data()
        user = self.env["res.users"].browse(self._uid)
        company_name = user.company_id.name
        header_bgcolor = user.company_id.company_header_bgcolor
        header_fontcolor = user.company_id.company_header_fontcolor
        report_header_bgcolor = user.company_id.report_header_bgcolor
        report_header_fontcolor = user.company_id.report_header_fontcolor
        title_bgcolor = user.company_id.title_bgcolor
        title_fontcolor = user.company_id.title_fontcolor
        subtitle_bgcolor = user.company_id.subtitle_bgcolor
        subtitle_fontcolor = user.company_id.subtitle_fontcolor
        text_bgcolor = user.company_id.text_bgcolor
        text_fontcolor = user.company_id.text_fontcolor
        datas['model'] = 'cash.wizard'
        datas['form'] = self.read(
            ['start_date', 'end_date'])[0]
        datas['form']['context'] = ctx
        datas['form']['company'] = company_name
        datas['form']['company_header_bgcolor'] = header_bgcolor
        datas['form']['company_header_fontcolor'] = header_fontcolor
        datas['form']['report_header_bgcolor'] = report_header_bgcolor
        datas['form']['report_header_fontcolor'] = report_header_fontcolor
        datas['form']['title_bgcolor'] = title_bgcolor
        datas['form']['title_fontcolor'] = title_fontcolor
        datas['form']['subtitle_bgcolor'] = subtitle_bgcolor
        datas['form']['subtitle_fontcolor'] = subtitle_fontcolor
        datas['form']['text_bgcolor'] = text_bgcolor
        datas['form']['text_fontcolor'] = text_fontcolor
        data = {
            'ids': self.ids,
            'model': self._name,
            'record': datas,
        }
        return self.env.ref('itmcs_statistical_reports.cash_xlsx').report_action(self, data=data)


