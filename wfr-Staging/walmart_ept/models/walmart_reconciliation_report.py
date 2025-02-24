import base64
import csv
import io
import logging
import os
import zipfile
from datetime import datetime
from io import StringIO, BytesIO

from dateutil.parser import parse
from odoo.exceptions import ValidationError

from odoo import models, fields, api, _

_logger = logging.getLogger("Walmart_Reconcilation")

class WalmartReconciliationReport(models.Model):
    _name = 'walmart.reconciliation.report.ept'
    _description = 'Walmart Reconciliation Report'
    _inherit = ['mail.thread']
    _rec_name = "available_report_date"


    name = fields.Char(size=256, default='CSV Settlement Report')
    available_report_date = fields.Date(string="Report Date")

    start_date = fields.Date()
    state = fields.Selection([('draft', 'Draft'), ('partially_processed', 'Partially Processed'),
                              ('processed', 'processed'), ('done', 'Done'),
                              ('closed', 'Closed')], string='Report Status', default='draft')
    attachment_id = fields.Many2one('ir.attachment', string="Attachment")
    marketplace_id = fields.Many2one('walmart.marketplace.ept', string='Walmart Marketplace',
                                     help='Walmart Marketplace')
    statement_id = fields.Many2one('account.bank.statement', string="Bank Statement")
    currency_id = fields.Many2one('res.currency', string="Currency")

    @api.model_create_multi
    def create(self, vals_list):
        walmart_markplace_obj = self.env['walmart.marketplace.ept']
        results = super(WalmartReconciliationReport, self).create(vals_list)
        record_name = "Settlement Report"
        for res in results:
            if res.marketplace_id and res.available_report_date:
                instance_id = walmart_markplace_obj.search([('id', '=', res.marketplace_id.id)],
                                                           limit=1)
                if instance_id:
                    name1 = '{}-{}'.format(instance_id.name, res.available_report_date)
                    res.update({'name': record_name + "-" + name1})
        return results

    def closed_statement(self):
        self.statement_id.button_confirm_bank()
        return True

    @api.onchange('marketplace_id')
    def on_change_instance(self):
        currency_id = False
        if self.marketplace_id and self.marketplace_id.settlement_report_journal_id:
            currency_id = self.marketplace_id.settlement_report_journal_id.currency_id.id
        self.currency_id = currency_id or False

    def unlink(self):
        for report in self:
            if report.state == 'processed':
                raise ValidationError(_('You cannot delete processed report.'))
        return super(WalmartReconciliationReport, self).unlink()

    def get_walmart_report_date(self, instance_id):
        """
        This method is use to get the Walmart Report Date Which was Available in the walmart.
        :param instance_id: Record of the marketplace.
        """
        is_auto_process = self._context.get('is_auto_process', False)
        accounting_module = self.env["product.product"].search_installed_module_ept('account_accountant')
        if is_auto_process and not accounting_module:
            message = ("You are not able to import settlement reports, because "
                       "Accounting module is not installed in the odoo.")
            self.create_walmart_settlement_report_mismatch_logs(instance_id, message)
            return True
        if instance_id.environment == 'sandbox':
            message = "Sorry! This feature is only available in Production Environment."
            if is_auto_process:
                self.create_walmart_settlement_report_mismatch_logs(instance_id, message)
                return True
            raise ValidationError(_(message))
        report_ids = self.browse()
        walmart_conn_obj = instance_id.get_walmart_connection()
        try:
            response = walmart_conn_obj.reconciliation.all(type='get_report_date')
        except Exception as err:
            _logger.exception(err)
            message = str(err)
            if is_auto_process:
                self.create_walmart_settlement_report_mismatch_logs(instance_id, message)
                return True
            raise ValidationError(message)

        if not response or not response.get('availableApReportDates', False):
            message = 'Reconciliation Report Dates not Available in Walmart...!'
            _logger.info(message)
            self.create_walmart_settlement_report_mismatch_logs(instance_id, message)
        else:
            date_report_list = [datetime.strptime(date, '%m%d%Y').strftime('%Y-%m-%d') for date
                                in response.get("availableApReportDates", [])]
            if date_report_list:
                existing_dates = self.search([
                    ('available_report_date', 'in', date_report_list),
                    ('marketplace_id', '=', instance_id.id)]).mapped('available_report_date')
                date_report_list = set(date_report_list) - set([str(d) for d in existing_dates])
                for date_report in date_report_list:
                    new_record = self.new({"available_report_date": date_report, "marketplace_id": instance_id.id})
                    new_record.on_change_instance()
                    vals = self._convert_to_write({name: new_record[name] for name in new_record._cache})
                    report_ids += self.create(vals)
        return report_ids

    def get_reconciliation_report_ept(self):
        """
        Get The Reconciliation Report from walmart and process it.
        Migration done by Haresh Mori @ Emipro on date 24 January 2022 .
        """
        self.ensure_one()
        is_auto_process = self._context.get('is_auto_process', False)
        product_sync_report_obj = self.env["walmart.product.sync.report.ept"]
        instance_id = self.marketplace_id
        if instance_id.environment == 'sandbox':
            message = "Sorry! This feature is only available in Production Environment."
            if is_auto_process:
                self.create_walmart_settlement_report_mismatch_logs(instance_id, message, self.name)
                return True
            raise ValidationError(_(message))
        walmart_conn_obj = instance_id.get_walmart_connection()
        report_date = datetime.strftime(self.available_report_date, '%m%d%Y')
        if not report_date:
            message = "There is Report Date Not available for the Reconciliation Report Process"
            if is_auto_process:
                self.create_walmart_settlement_report_mismatch_logs(instance_id, message, self.name)
                return True
            raise ValidationError(_(message))

        try:
            response = walmart_conn_obj.reconciliation.all(type='get_report',
                                                           report_date=report_date)
        except Exception as e:
            message = str(e)
            if is_auto_process:
                self.create_walmart_settlement_report_mismatch_logs(instance_id, message, self.name)
                return True
            raise ValidationError(message)
        if not response:
            message = 'Reconciliation Report not found for Report Date {}'.format(report_date)
            _logger.info(message)
            self.create_walmart_settlement_report_mismatch_logs(instance_id, message, self.name)
        else:
            path = "/tmp"
            zipres = zipfile.ZipFile(io.BytesIO(response))
            zipres.extractall(path=path)
            for filename in zipres.namelist():
                file_obj = open('/tmp/%s' % filename, 'rb')
                attachment = product_sync_report_obj._create_attachment(filename, 'walmart.reconciliation.report.ept',
                                                                        self.id, file_obj)
                file_obj.close()
                self.message_post(body=_("<b>Shipment Report Downloaded</b>"),
                                  attachment_ids=attachment.ids)
                self.write({'attachment_id': attachment.id, 'state': "done"})
                try:
                    os.remove('/tmp/%s' % filename)
                except:
                    _logger.info("Not Directory Found /tmp/%s " % filename)
        return True

    def process_settlement_report_file(self):
        """
        This method is use to process the report from the CSV file and create bank statement and it's bank
        statement line.
        """
        self.ensure_one()
        # Check for Instance set, Attachment, Currency Same
        # check mismatch in the report process then stop the process
        if self._validate_report():
            return True
        # Read CSV File
        import_file = BytesIO(base64.decodebytes(self.attachment_id.datas))
        csv_file = StringIO(import_file.read().decode())
        settlement_reports_data = csv.DictReader(csv_file, delimiter=',')
        instance_id = self.marketplace_id
        journal = instance_id.settlement_report_journal_id
        ctx = self._context.copy()
        ctx.update({'journal_type': 'bank'})
        if settlement_reports_data:
            # Create Bank Statement
            bank_statement_id = self._create_bank_statement(instance_id, journal)
            # Get Data in Dict
            order_dict, refund_dict, commission_dict = self._get_report_data(settlement_reports_data)
            # Processed order_dict
            _logger.info("Processing the Order data")
            self._process_order_data(order_dict, bank_statement_id)
            # Processed refund_dict
            _logger.info("Processing the refund data")
            self._process_refund_data(refund_dict, bank_statement_id)
            # Processed commission_dict
            _logger.info("Processing the commission data")
            self._process_commission_data(commission_dict, bank_statement_id)
            self.write({'statement_id': bank_statement_id.id})
            self._cr.commit()
            # Reconcile Bank Statement
            if bank_statement_id:
                if not bank_statement_id.line_ids:
                    bank_statement_id.unlink()
                    return False
                _logger.info("Processing of reconcile bank statement line")
                self._reconcile_statement_lines(bank_statement_id)
        return True

    def _validate_report(self):
        """
        This method is use to check require validation.
        """
        is_mismatch = False
        is_auto_process = self._context.get('is_auto_process', False)
        instance_id = self.marketplace_id
        if not instance_id:
            message = "There is no any MarketPlace Instance Configuration with this record."
            if is_auto_process:
                self.create_walmart_settlement_report_mismatch_logs(instance_id, message, self.name)
                is_mismatch = True
            else:
                raise ValidationError(_(message))
        if not self.attachment_id:
            message = "There is no any report are attached with this record."
            if is_auto_process:
                self.create_walmart_settlement_report_mismatch_logs(instance_id, message, self.name)
                is_mismatch = True
            else:
                raise ValidationError(_(message))
        if not instance_id.settlement_report_journal_id:
            message = ("You have not configured Settlement report Journal in Instance. Please "
                       "configured it first(Walmart > Configuration > Setting > Settlement Report Journal).")
            if is_auto_process:
                self.create_walmart_settlement_report_mismatch_logs(instance_id, message, self.name)
                is_mismatch = True
            else:
                raise ValidationError(_(message))
        currency_id = instance_id.settlement_report_journal_id.currency_id.id or False
        if currency_id and currency_id != self.currency_id.id:
            message = ("Report Currency and Currency in Instance Journal are different. "
                       "Make sure Report currency and Instance Journal currency must be same.")
            if is_auto_process:
                self.create_walmart_settlement_report_mismatch_logs(instance_id, message, self.name)
                is_mismatch = True
            else:
                raise ValidationError(_(message))
        default_account_id = instance_id.settlement_report_journal_id.default_account_id
        if not default_account_id:
            message = "You have not configured default account in Settlement Report Journal. Please Configure it first."
            if is_auto_process:
                self.create_walmart_settlement_report_mismatch_logs(instance_id, message, self.name)
                is_mismatch = True
            else:
                raise ValidationError(_(message))
        return is_mismatch

    def create_walmart_settlement_report_mismatch_logs(self, instance, message, report_ref=''):
        """
        Define this method for add mismatch log for settlement report process.
        :param instance: walmart.marketplace.ept()
        :param message: str
        :param report_ref: str
        :return: True
        """
        log_lines_obj = self.env['common.log.lines.ept']
        log_lines_obj.create_common_log_line_ept(message=message, module='walmart_ept', model_name=self._name,
                                                 res_id=self.id or False, order_ref=report_ref,
                                                 walmart_marketplace_id=instance.id or self.marketplace_id.id or False,
                                                 log_line_type='fail', mismatch_details=False,
                                                 operation_type="import")
        return True

    def _get_report_data(self, settlement_report_data):
        """
        This method is use to prepare a dictionary data from the CSV(report) file data.
        """
        log_line_obj = self.env['common.log.lines.ept']
        order_dict = {}
        sale_dict = {}
        refund_dict = {}
        commission_dict = {}
        instance_id = self.marketplace_id
        rows = list(settlement_report_data)
        total_rows = len(rows)
        for count, row in enumerate(rows, start=1):
            if row.get('Walmart.com Order #', '') == 'Walmart.com Order #':
                continue
            transaction_type = row.get('Transaction Type', '')
            walmart_order_id = row.get('Walmart.com Order #', '').strip()
            walmart_purchase_order_id = row.get('Walmart.com PO #', '').strip()
            _logger.info(
                    "Process row {} out of {} with order Reference:{} transaction type:{}".format(count, total_rows,
                                                                                                  walmart_purchase_order_id,
                                                                                                  transaction_type))

            sale_order = order_dict.get((walmart_order_id, walmart_purchase_order_id, instance_id.id))
            if not sale_order:
                sale_order = self.env['sale.order'].search(
                        [('walmart_seller_order_ref', '=', walmart_purchase_order_id),
                         ('walmart_marketplace_order_ref', '=', walmart_order_id),
                         ('walmart_marketplace_id', '=', instance_id.id)], limit=1)._ids
                order_dict.update(
                        {(walmart_order_id, walmart_purchase_order_id, instance_id.id): sale_order})
            if not sale_order:
                message = "Order not found with reference:{} while processing bank statement". \
                    format(walmart_purchase_order_id)
                _logger.info(message)
                log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept', model_name=self._name,
                                                        res_id=self.id, order_ref=walmart_purchase_order_id,
                                                        walmart_marketplace_id=instance_id.id, log_line_type='fail',
                                                        mismatch_details=True, operation_type="import")
                continue
            date = row.get('Transaction Date Time', {})
            date = parse(date)
            # try:
            #     date = datetime.strptime(date.replace("/", "-"), "%m-%d-%y").date()
            # except:
            #     date = datetime.strptime(date.replace("/", "-"), "%y-%m-%d").date()
            total_amount_customer_pay = str(row.get('Total tender to / from customer', '')) \
                if row.get('Total tender to / from customer') else ''
            total_amount_customer_pay = total_amount_customer_pay.strip()
            total_amount_customer_pay = total_amount_customer_pay and round(
                    float(total_amount_customer_pay), 10)

            total_commission_pay = row.get("Commission from Sale", '') and str(
                    row.get('Commission from Sale', ''))
            total_commission_pay = total_commission_pay and total_commission_pay.strip()
            total_commission_pay = total_commission_pay and round(float(total_commission_pay), 10)

            # Sale order Line Number
            line_number = row.get('Walmart.com Order Line #', '').strip()
            line_number = line_number and int(line_number)

            if transaction_type == 'SALE' and total_amount_customer_pay and \
                    total_amount_customer_pay > 0.0:
                key = (walmart_order_id, walmart_purchase_order_id, sale_order, date)
                if not sale_dict.get(key):
                    sale_dict.update({key: total_amount_customer_pay})
                else:
                    existing_amount = sale_dict.get(key, 0.0)
                    sale_dict.update({key: existing_amount + total_amount_customer_pay})

            if transaction_type == 'REFUNDED' and total_amount_customer_pay and \
                    total_amount_customer_pay <= 0.0:
                key = (walmart_order_id, walmart_purchase_order_id, sale_order, date)
                if not refund_dict.get(key):
                    refund_dict.update({key: {line_number: total_amount_customer_pay}})
                else:
                    if refund_dict.get(key, {}).get(line_number, 0.0):
                        existing_amount = refund_dict.get(key, {}).get(line_number, 0.0)
                        total_amount_customer_pay += existing_amount + total_amount_customer_pay

                    refund_dict.get(key).update({line_number: total_amount_customer_pay})

            if total_commission_pay and total_commission_pay != 0.0:
                key = (
                    walmart_order_id, walmart_purchase_order_id, sale_order, transaction_type, date)
                if not commission_dict.get(key):
                    commission_dict.update({key: {line_number: total_commission_pay}})
                else:
                    if commission_dict.get(key, {}).get(line_number, 0.0):
                        existing_amount = commission_dict.get(key, {}).get(line_number, 0.0)
                        total_commission_pay += existing_amount

                    commission_dict.get(key).update({line_number: total_commission_pay})

        return sale_dict, refund_dict, commission_dict

    def _process_refund_data(self, refund_dict, bank_statement_id):
        """
        This method is use to process the refund data as prepare refund dict.
        """
        inv_type = 'out_refund'
        sale_order_obj = self.env['sale.order']
        account_invoice_obj = self.env['account.move']

        for order_key, refund_key in refund_dict.items():
            sale_order = sale_order_obj.browse(order_key[2])
            sale_order = sale_order[0] if len(sale_order) > 1 else sale_order
            date = order_key[3]
            refund_amount = sum(refund_key.values())

            # Find Sale Order Invoices
            invoice_ids = self.create_find_sale_order_invoices(sale_order, account_invoice_obj, inv_type, refund_key,
                                                               date)

            invoice_ids = invoice_ids.filtered(lambda inv: inv.move_type == inv_type and inv.state != 'cancel')
            invoice_ids = invoice_ids or account_invoice_obj

            # Create Bank Statement Line
            self._create_bank_statement_line(sale_order, bank_statement_id, refund_amount, inv_type, date, "Refund",
                                             refund_invoice_id=invoice_ids)
        return True

    def _process_order_data(self, order_dict, bank_statement_id):
        """
        This method is use to process order data as prepared in order dict
        """
        inv_type = 'out_invoice'
        sale_order_obj = self.env['sale.order']
        account_invoice_obj = self.env['account.move']

        for order_key, total_amount_customer_pay in order_dict.items():
            sale_order = sale_order_obj.browse(order_key[2])
            date = order_key[3]

            if len(sale_order) > 1:
                search_orders = sale_order.filtered(
                        lambda l: round(l.amount_total, 10) == round(total_amount_customer_pay, 10))
                if search_orders:
                    sale_order = search_orders and search_orders[0]
                else:
                    sale_order = sale_order[0]

            # Find Sale Order Invoices
            invoice_ids = self.create_find_sale_order_invoices(sale_order, account_invoice_obj,
                                                               inv_type)

            # Create Bank Statement Line
            self._create_bank_statement_line(sale_order, bank_statement_id,
                                             total_amount_customer_pay,
                                             inv_type, date, "SALE")

        return True

    def _process_commission_data(self, commission_dict, bank_statement_id):
        """
        This method is use process the commission as prepared the commission data in the dict.
        """
        sale_order_obj = self.env['sale.order']

        for order_key, commission_info in commission_dict.items():
            sale_order = sale_order_obj.browse(order_key[2])
            sale_order = sale_order[0] if len(sale_order) > 1 else sale_order
            transaction_type = order_key[3]
            date = order_key[4]
            commission_amount = sum(commission_info.values())

            if transaction_type.lower() == 'sale':
                commission_amount = -abs(commission_amount)
            # Create Commission Bank Statement Line
            self._create_bank_statement_line(sale_order, bank_statement_id, commission_amount, inv_type=False,
                                             date=date, transaction_type=transaction_type)
        return True

    def _create_bank_statement(self, instance, journal):
        """
        This method is use to create a bank statement.
        """
        account_bank_statement_obj = self.env['account.bank.statement']

        name = '{}_{}'.format(instance.name, self.available_report_date.strftime('%Y%m%d'))
        vals = {'journal_id': journal.id, 'date': self.available_report_date, 'name': name}
        return account_bank_statement_obj.create(vals)

    def create_find_sale_order_invoices(self, sale_order, account_invoice_obj, inv_type, refund_items={}, date=''):
        """
        This method is use search invoice/credit note, it will create a create invoice if sale order state in sale.
        """
        invoice_ids = sale_order.invoice_ids.filtered(
                lambda inv: inv.move_type == 'out_invoice' and inv.state != 'cancel')

        # Create Out Invoice
        if not invoice_ids and sale_order and sale_order.state == 'sale' and \
                sale_order.invoice_status == 'to invoice':
            self.create_invoice(sale_order, account_invoice_obj)

        # Create Refund Invoice
        if inv_type == 'out_refund':
            self.create_find_refund_invoice(sale_order, refund_items, date)

        invoice_ids = sale_order.invoice_ids
        return invoice_ids

    def create_invoice(self, sale_order, account_invoice_obj):
        invoice_ids = []
        # Create Invoices if not Created
        try:
            invoice_ids = sale_order._create_invoices()
        except Exception as err:
            _logger.exception("Exception Occured while creating invoice for an order: {}" \
                              "error:{}".format(sale_order, err))
        # Validate Invoice
        for invoice_id in invoice_ids:
            # invoice = account_invoice_obj.browse(invoice_id)
            if invoice_id.state == 'draft' and invoice_id.move_type == 'out_invoice':
                # invoice_id.action_invoice_open()
                invoice_id.action_post()

        return True

    def create_find_refund_invoice(self, sale_order, refund_items, date_posted):

        product_amount = {}
        invoice_ids = sale_order.invoice_ids

        for line_number, amount in refund_items.items():
            product_id = sale_order.order_line.walmart_order_line_ids.filtered(
                    lambda line: line.line_number == line_number)   .mapped('order_line_id').product_id.id
            if product_id in product_amount:
                product_amount[product_id] += amount
            else:
                product_amount[product_id] = amount

        refund_invoice = invoice_ids.filtered(
                lambda inv: inv.move_type == 'out_refund' and inv.state != 'cancel')

        if not refund_invoice:
            product_ids = list(product_amount.keys())

            invoices = invoice_ids.filtered(
                    lambda inv: inv.move_type == 'out_invoice' and inv.state == 'open'). \
                mapped('invoice_line_ids').filtered(lambda l: l.product_id.id in product_ids). \
                mapped('move_id')

            if not invoices:
                invoices = invoice_ids.filtered(
                        lambda inv: inv.move_type == 'out_invoice').mapped('invoice_line_ids') \
                    .filtered(lambda l: l.product_id.id in product_ids).mapped('move_id')

                if not invoices:
                    return True

            move_reversal = self.env["account.move.reversal"].with_context(
                    {
                        "active_model": "account.move",
                        "active_ids": invoices.ids
                    }
            ).create({"refund_method": "refund", "reason": "Refunded from Walmart",
                      "date": str(date_posted), "date_mode": "custom", 'journal_id': invoices[0].journal_id.id})
            move_reversal.reverse_moves()
            refund_invoice = move_reversal.new_move_ids

            extra_invoice_lines = refund_invoice.invoice_line_ids. \
                filtered(lambda inv_line: inv_line.product_id.id not in product_ids)
            if extra_invoice_lines:
                line_to_delete = extra_invoice_lines.filtered(lambda line: line.product_id)
                line_to_delete and line_to_delete.with_context(check_move_validity=False,
                                                               dynamic_unlink=True).unlink()
        if refund_invoice.state == 'draft':
            refund_invoice.action_post()
        return True

    def _create_bank_statement_line(self, sale_order, bank_statement_id, amount, inv_type, date, transaction_type,
                                    refund_invoice_id=False):
        """
        This method is use to create a bank statement line.
        """
        partner_id = self.env['res.partner']._find_accounting_partner(sale_order.partner_id)
        walmart_order_id = sale_order.walmart_seller_order_ref
        if inv_type == 'out_invoice':
            name = walmart_order_id
            name = "{}-{}".format(walmart_order_id, sale_order.name) if sale_order else name
        elif inv_type == 'out_refund':
            name = "{}-{}".format('Refund', walmart_order_id)
            name = "Refund-{}-{}".format(walmart_order_id, sale_order.name) if sale_order else name
        else:
            transaction_type = "Commission" if transaction_type == 'SALE' else 'Refund Commission'
            name = "{}-{}-{}".format(transaction_type, walmart_order_id, sale_order.name)

        bank_statement_line = bank_statement_id.line_ids. \
            filtered(lambda line: not line.is_reconciled and line.partner_id.id == partner_id.id \
                                  and line.transaction_type == transaction_type and \
                                  line.sale_order_id.id == sale_order.id
                     )

        if bank_statement_line:
            bank_statement_line.write({"amount": bank_statement_line.amount + amount})
        else:
            ref = ", ".join(sale_order.mapped('name'))
            line_vals = {
                'ref': name,
                'amount': amount,
                'date': date,
                'partner_id': partner_id.id,
                'payment_ref': ref or sale_order.name,
                'statement_id': bank_statement_id.id,
                'transaction_type': transaction_type,
                'sale_order_id': sale_order.id,
                'journal_id': self.marketplace_id.settlement_report_journal_id.id,
            }
            if refund_invoice_id:
                line_vals.update({'refund_invoice_id': refund_invoice_id.id})
            bank_statement_line.create(line_vals)

        return True

    def view_bank_statement(self):
        self.ensure_one()
        res = self.statement_id.action_open_bank_reconcile_widget()
        return res

    @api.model
    def convert_move_amount_currency(self, bank_statement, moveline, amount, date):
        """
        This method converts amount of moveline to bank statement's currency.
        """
        amount_currency = 0.0
        if moveline.company_id.currency_id.id != bank_statement.currency_id.id:
            amount_currency = moveline.currency_id._convert(moveline.amount_currency,
                                                            bank_statement.currency_id,
                                                            bank_statement.company_id,
                                                            date)
        elif moveline.move_id.currency_id.id != bank_statement.currency_id.id:
            amount_currency = moveline.move_id.currency_id._convert(amount,
                                                                    bank_statement.currency_id,
                                                                    bank_statement.company_id,
                                                                    date)
        currency = moveline.currency_id.id
        return currency, amount_currency

    def reconcile_statement(self):
        self.ensure_one()
        self._reconcile_statement_lines(self.statement_id)
        return True

    def _reconcile_statement_lines(self, bank_statement):
        """
        This method is use to reconcile the bank statement line.
        """

        _logger.info("Processing Bank Statement: %s.", bank_statement.name)

        for statement_line in bank_statement.line_ids.filtered(lambda x: not x.is_reconciled):
            move_line_data = []
            move_line_total_amount = 0.0
            currency_ids = []
            paid_move_lines = []
            if statement_line.transaction_type in ["SALE", "Refund"]:
                invoices = self._get_invoices_for_reconcile(statement_line)
                if not invoices:
                    _logger.info("Invoice not found for bank statement line: %s", statement_line.name)
                    continue

                paid_invoices = invoices.filtered(lambda x: x.payment_state in ['paid', 'in_payment'])
                unpaid_invoices = invoices.filtered(lambda x: x.payment_state == 'not_paid')

                if paid_invoices:
                    move_line_total_amount, currency_ids, paid_move_lines = self._get_paid_move_line_amount(
                            statement_line, paid_invoices)

                if unpaid_invoices:
                    move_line_total_amount, currency_ids, move_line_data = self._get_unpaid_move_line_data(
                            statement_line, unpaid_invoices)

                self.reconcile_invoice_refund(statement_line, move_line_total_amount, currency_ids,
                                              move_line_data, paid_move_lines)
            else:
                self.reconcile_other_transactions(statement_line, move_line_data)

        if bank_statement.line_ids.filtered(lambda x: not x.is_reconciled) or not self.statement_id.is_complete:
            self.write({'state': 'partially_processed'})
        else:
            self.write({'state': 'processed'})

        return True

    def _get_invoices_for_reconcile(self, statement_line):
        """
        This method gets invoices for reconciling the bank statement.
        @param statement_line: Record of bank statement line.
        """
        order = statement_line.sale_order_id
        if statement_line.refund_invoice_id:
            invoices = statement_line.refund_invoice_id
        else:
            invoices = order.invoice_ids.filtered(
                    lambda x: x.move_type == 'out_invoice' and x.state in ['posted'])
        return invoices

    def _get_paid_move_line_amount(self, statement_line, paid_invoices):
        """
        This method is used to get the total paid amount of the Order for given statement line.
        @param statement_line: Record of the statement line.
        """
        move_line_total_amount = 0.0
        currency_ids = []
        if statement_line.refund_invoice_id:
            payment_id = paid_invoices.line_ids.matched_debit_ids.debit_move_id.payment_id
            paid_move_lines = payment_id.invoice_line_ids.filtered(lambda x: x.credit != 0.0)
        else:
            payment_id = paid_invoices.line_ids.matched_credit_ids.credit_move_id.payment_id
            paid_move_lines = payment_id.invoice_line_ids.filtered(lambda x: x.debit != 0.0)

        for moveline in paid_move_lines:
            amount = moveline.debit - moveline.credit
            amount_currency = 0.0
            if moveline.amount_currency:
                currency, amount_currency = self.convert_move_amount_currency(self.statement_id,
                                                                              moveline, amount,
                                                                              statement_line.date)
                if currency:
                    currency_ids.append(currency)

            if amount_currency:
                amount = amount_currency

            move_line_total_amount += amount
        return move_line_total_amount, currency_ids, paid_move_lines

    def _get_unpaid_move_line_data(self, statement_line, unpaid_invoices):
        """
        This method is used to gather the data of move lines that are remain to register payment.
        @param statement_line: Record of the statement line.
        @param unpaid_invoices: Recordset of Unpaid Invoices.
        """
        move_line_data = []
        move_line_total_amount = 0.0
        currency_ids = []
        move_lines = unpaid_invoices.line_ids.filtered(
                lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled)
        for moveline in move_lines:
            amount = moveline.debit - moveline.credit
            amount_currency = 0.0
            if moveline.amount_currency:
                currency, amount_currency = self.convert_move_amount_currency(self.statement_id,
                                                                              moveline, amount,
                                                                              statement_line.date)
                if currency:
                    currency_ids.append(currency)

            if amount_currency:
                amount = amount_currency
            move_line_data.append({
                'name': moveline.move_id.name,
                'id': moveline.id,
                'balance': -amount,
                'currency_id': moveline.currency_id.id,
            })
            move_line_total_amount += amount
        return move_line_total_amount, currency_ids, move_line_data

    def reconcile_invoice_refund(self, statement_line, move_line_total_amount, currency_ids, move_line_data,
                                 paid_move_lines):

        if round(statement_line.amount, 10) == round(move_line_total_amount, 10) and (
                not statement_line.currency_id or statement_line.currency_id.id ==
                self.statement_id.currency_id.id):
            if currency_ids:
                currency_ids = list(set(currency_ids))
                if len(currency_ids) == 1:
                    statement_currency = statement_line.journal_id.currency_id if \
                        statement_line.journal_id.currency_id else \
                        statement_line.company_id.currency_id
                    if not currency_ids[0] == statement_currency.id:
                        vals = {'currency_id': currency_ids[0]}
                        statement_line.write(vals)
            try:
                if move_line_data:
                    self.walmart_reconclie_bank_statement_line(statement_line, move_line_data[0].get('id'))
                for payment_line in paid_move_lines:
                    self.walmart_reconclie_bank_statement_line(statement_line, payment_line.id)

            except Exception as error:
                message = "Error occurred while reconciling statement line : {} \n {}".format(
                        statement_line.payment_ref, error)
                _logger.exception(message)
                statement_line.move_id.message_post(body=_(error))
        return True

    def walmart_reconclie_bank_statement_line(self, statement_id, move_line_id):
        wizard = self.env['bank.rec.widget'].with_context(default_st_line_id=statement_id).new({})
        wizard._action_add_new_amls(self.env['account.move.line'].browse(move_line_id))
        wizard.with_context(dynamic_unlink=True).button_validate(async_action=False)

    def reconcile_other_transactions(self, statement_line, move_line_data):
        wizard = self.env['bank.rec.widget'].with_context(default_st_line_id=statement_line).new({})
        wizard.form_account_id = self.marketplace_id.settlement_report_journal_id.default_account_id.id
        line = wizard.line_ids.filtered(lambda x: x.credit == 0.0)
        line = line[0] if len(line) > 1 else line
        wizard.form_index = line.index
        wizard.form_flag = line.flag
        wizard._onchange_form_account_id()
        try:
            wizard.with_context(dynamic_unlink=True).button_validate(async_action=False)
        except Exception as err:
            _logger.exception(err)
            statement_line.move_id.message_post(body=_(err))
        return True

    def reconcile_orders_refunds_statement_lines(self, bank_statement_id):

        statement_lines = bank_statement_id.line_ids.filtered(
                lambda line: line.line_ids.ids == [] and \
                             (line.walmart_seller_order_ref or line.walmart_marketplace_order_ref))

        for statement_line in statement_lines:
            if statement_line.amount < 0.0:
                invoice_type = 'out_refund'
            else:
                invoice_type = 'out_invoice'

            invoices = statement_line.line_ids.filtered(
                    lambda record: record.move_type == invoice_type and record.state != 'cancel')
            if not invoices:
                continue

            paid_invoices = invoices.filtered(
                    lambda invoice: invoice.payment_ids and invoice.residual == 0.0)
            unpaid_invoices = invoices.filtered(lambda invoice: not invoice.payment_ids)

            mv_line_dicts = []
            move_line_total_amount = 0.0
            currency_ids = []
            paid_move_lines = False

            if paid_invoices:
                payment_ids = paid_invoices.payment_ids
                for moveline in payment_ids.mapped('move_line_ids').filtered(
                        lambda x: x.debit != 0.0):
                    amount = moveline.debit - moveline.credit
                    amount_currency = 0.0
                    if moveline.amount_currency:
                        currency, amount_currency = self.convert_move_amount_currency(
                                bank_statement_id, moveline,
                                amount, statement_line.date)
                        if currency:
                            currency_ids.append(currency)

                    if amount_currency:
                        amount = amount_currency

                    move_line_total_amount += amount

            if unpaid_invoices:
                move_lines = unpaid_invoices.mapped('move_id').mapped('line_ids'). \
                    filtered(lambda l: l.account_id.user_type_id.type == 'receivable' \
                                       and not l.reconciled)

                for moveline in move_lines:
                    amount = moveline.debit - moveline.credit
                    amount_currency = 0.0
                    if moveline.amount_currency:
                        currency, amount_currency = self.convert_move_amount_currency(
                                bank_statement_id, moveline,
                                amount, statement_line.date)
                        if currency:
                            currency_ids.append(currency)

                    if amount_currency:
                        amount = amount_currency

                    mv_line_dicts.append({
                        'credit': abs(amount) if amount > 0.0 else 0.0,
                        'name': moveline.move_id.name,
                        'move_line': moveline,
                        'debit': abs(amount) if amount < 0.0 else 0.0
                    })

                    move_line_total_amount += amount

            if round(abs(statement_line.amount), 10) == round(move_line_total_amount, 10) and \
                    (not statement_line.currency_id or \
                     statement_line.currency_id.id == bank_statement_id.currency_id):

                if currency_ids:
                    currency_ids = list(set(currency_ids))
                    if len(currency_ids) == 1:
                        vals = {'amount_currency': move_line_total_amount}
                        if invoice_type == 'out_invoice':

                            statement_currency = statement_line.journal_id.currency_id.id or \
                                                 statement_line.company_id.currency_id.id

                            if not currency_ids[0] == statement_currency:
                                vals.update({'currency_id': currency_ids[0]})

                        else:
                            vals.update({'currency_id': currency_ids[0]})

                        statement_line.write(vals)

                statement_line.process_reconciliation(mv_line_dicts,
                                                      payment_aml_rec=paid_move_lines)

        return True
