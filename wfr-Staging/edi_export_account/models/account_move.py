# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from math import ceil

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'edi.status.mixin']

    trading_partnerid = fields.Char(string='Trading Partner ID', related='partner_id.trading_partnerid')
    should_export = fields.Boolean(string='Should Export To EDI', related='partner_id.send_edi_inv')
    edi_po_number = fields.Char(string='EDI PO Number', compute='_compute_edi_so_values')
    edi_department = fields.Char(string='EDI Deparment', compute='_compute_edi_so_values')
    edi_vendor = fields.Char(string='EDI Vendor', compute='_compute_edi_so_values')
    edi_terms_type = fields.Char(string='EDI Terms Type', compute='_compute_edi_terms_values')
    edi_terms_basis_date_code = fields.Char(string='EDI Terms Basis Date Code', compute='_compute_edi_terms_values')
    edi_terms_discount_percentage = fields.Char(string='EDI Terms Discount Percentage', compute='_compute_edi_terms_values')
    edi_terms_discount_date = fields.Char(string='EDI Terms Discount Date', compute='_compute_edi_terms_values')
    edi_terms_discount_due_days = fields.Char(string='EDI Terms Discount Due Days', compute='_compute_edi_terms_values')
    edi_terms_net_due_date = fields.Char(string='EDI Terms Net Due Date', compute='_compute_edi_terms_values')
    edi_terms_net_due_days = fields.Char(string='EDI Terms Discount Date', compute='_compute_edi_terms_values')
    edi_terms_description = fields.Char(string='EDI Terms Description', compute='_compute_edi_terms_values')
    edi_fob_pay_code = fields.Char(string='EDI FOB Pay Code', compute='_compute_edi_terms_values')
    edi_fob_location_qualifier = fields.Char(string='EDI FOB Location Qualifier', compute='_compute_edi_terms_values')
    edi_fob_location_description = fields.Char(string='EDI FOB Location Description', compute='_compute_edi_terms_values')
    edi_invoice_quantity = fields.Char(string='EDI Invoice Quantity', compute='_compute_edi_invoice_quantity_values')
    edi_invoice_quantity_uom = fields.Char(string='EDI Invoice Quantity UoM', compute='_compute_edi_invoice_quantity_values')
    edi_partner_invoice_id = fields.Many2one(string='EDI Invoice Partner', comodel_name='res.partner', compute='_compute_edi_so_values')
    edi_partner_shipping_id = fields.Many2one(string='EDI Shipping Partner', comodel_name='res.partner', compute='_compute_edi_so_values')
    edi_company_partner_id = fields.Many2one(string='EDI Company Partner', comodel_name='res.partner', related='company_id.partner_id')
    edi_charge_allowance_ids = fields.Many2many(string='EDI Charge Allowances', comodel_name='charge.allowance', compute='_compute_edi_so_values')
    edi_line_count = fields.Integer(string='EDI Line Item Number', compute='_compute_line_count')
    edi_amount_total = fields.Monetary(string='EDI Sale Total Amount')
    edi_amount_discount = fields.Monetary(string='EDI Terms Discount')

    edi_quantity_totals_qualifier = fields.Selection(selection=[
                                    ('SQT', 'Summary Quantity Totals')
                                ], string='Quantity Totals Qualifier',
                                help='For EDI purposes. Qualifier used to define the related total amounts.')

    edi_tset_purpose_code = fields.Selection([
                        ('00', 'Original'),
                        ('06', 'Confirmation'),
                        ('NA', 'Unavailable')],
                        string='TSET Purpose Code',
                        help='Code identifying purpose or function of the transmission')
    edi_qualified_date = fields.Char(string='EDI Qualified Date', compute='_compute_edi_so_values')

    edi_customer_payment_terms = fields.Text(string='Payment Terms', compute='_compute_edi_customer_payment_terms', default='')

    edi_merch_type_code = fields.Char('Merchandise Type Code')

    def _compute_edi_customer_payment_terms(self):
        for move in self:
            line_ids = move.invoice_line_ids.sale_line_ids
            if len(line_ids) == 1:
                sale_id = line_ids.order_id
            else:
                sale_id = line_ids and line_ids[0].order_id or False
            move.edi_customer_payment_terms = sale_id and sale_id.edi_customer_payment_terms or ''

    def _compute_edi_so_values(self):
        for move in self:
            sale_order = self.env['sale.order'].search([('name', '=', move.invoice_origin)], limit=1)
            move.edi_po_number = sale_order.edi_po_number
            move.edi_department = sale_order.edi_department
            move.edi_partner_shipping_id = sale_order.partner_shipping_id
            move.edi_partner_invoice_id = sale_order.partner_invoice_id
            move.edi_charge_allowance_ids = sale_order.edi_charges_allowance_ids
            move.edi_qualified_date = sale_order.commitment_date and sale_order.commitment_date.strftime('%Y-%m-%d') or fields.datetime.now().strftime('%Y-%m-%d')
            move.edi_vendor = sale_order.edi_vendor


    def _compute_edi_terms_values(self):
        for move in self:
            default_date = (move.date + datetime.timedelta(days=30)).strftime('%Y-%m-%d')
            terms_dict = {key.strip(): value.strip() for lines in move.edi_customer_payment_terms.splitlines() for line in lines.split(',') for key, value in [line.split(':')]}
            move.edi_terms_type = terms_dict.get('Terms Type', '')
            move.edi_terms_basis_date_code = terms_dict.get('Basis Date Code', '')
            move.edi_terms_discount_percentage = terms_dict.get('Discount Percentage', '')
            move.edi_terms_discount_date = terms_dict.get('Discount Date', default_date)
            move.edi_terms_discount_due_days = terms_dict.get('edi_terms_discount_due_days', '')
            move.edi_terms_net_due_date = terms_dict.get('Net Due Date', '')
            move.edi_terms_net_due_days = terms_dict.get('Net Due Days', '')
            move.edi_terms_description = terms_dict.get('Terms Description', '')
            move.edi_fob_pay_code = terms_dict.get('Terms Description', '')
            move.edi_fob_location_qualifier = terms_dict.get('FOB Location Qualifier', '')
            move.edi_fob_location_description = terms_dict.get('FOB Location Description', '')

    def _compute_edi_invoice_quantity_values(self):
        for move in self:
            lines = move.invoice_line_ids.filtered(lambda r: r.display_type not in ['line_section', 'line_note'])
            uom_code = lines[0].product_uom_id.edi_code
            qty_field_name = 'edi_qty_cases' if uom_code == 'CA' else 'quantity' or '0'
            move.edi_invoice_quantity = str(float(ceil(sum(move.line_ids.mapped(qty_field_name))))) or '1'
            move.edi_invoice_quantity_uom = uom_code

    def _compute_line_count(self):
        for move in self:
            move.edi_line_count = len(move.invoice_line_ids.filtered(lambda r: r.display_type not in ['line_section', 'line_note']))

    def _check_edi_required_fields(self):
        """Checks that required fields are present before exporting invoice to EDI"""
        # NOTE: merchandise_type_code was required in the old EDI, the xsd show no reason it should be required
        return True

    def action_post(self):
        self._check_edi_required_fields()
        res = super(AccountMove, self).action_post()
        self.export_invoice_to_edi()
        return res


    def export_invoice_to_edi(self):
        base_edi = self.env['edi.sync.action']
        sync_action = base_edi.search([('doc_type_id.doc_code', '=', 'export_invoice_xml')], limit=1)
        if sync_action:
            invoices = self.filtered(lambda record: record.partner_id.send_edi_inv)
            invoices._check_edi_required_fields()
            base_edi._do_doc_sync_cron(sync_action_id=sync_action, records=invoices)
        return True

    @api.model
    def create(self, vals):
        """Transfer EDI information from the origin sale order to the invoice"""

        res = super(AccountMove, self).create(vals)
        for move in res:
            if move.move_type == 'out_invoice' and move.invoice_origin:
                order = self.env['sale.order'].search([('name', '=', move.invoice_origin)], limit=1)
                if order:
                    move.edi_tset_purpose_code = order and order.edi_tset_purpose_code
                    move.edi_customer_payment_terms = order and order.edi_customer_payment_terms
                    for line in move.invoice_line_ids:
                        if line.sale_line_ids:
                            line.edi_line_sequence_number = line.sale_line_ids[0].edi_line_sequence_number
                            line.edi_vendor_part_number = line.sale_line_ids[0].edi_vendor_part_number
                            line.edi_buyer_part_number = line.sale_line_ids[0].edi_buyer_part_number
                            line.edi_part_number = line.sale_line_ids[0].edi_part_number
        return res

    def _get_edi_partner(self):
        self.ensure_one()
        return self.partner_id

    def get_edi_name(self):
        self.ensure_one()
        return self.name.replace('/', '_')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Order Line
    edi_consumer_package_code = fields.Char(string='Consumer Package Code (EDI)',
                              help='Consumer Package Code passed from the EDI. We store it because sometime it contains leading or training zeros that we need to transmit outbound. When searching for a product sometimes we need to strip these zeros to find the match.',
                              compute="_compute_edi_consumer_package_code")

    edi_line_sequence_number = fields.Char(string='Line Sequence Number',
                              help='For an initiated document, this is a unique number for the line item[s]. For a return transaction, this number should be the same as what was received from the source transaction. Example: You received a Purchase Order with the first LineSequenceNumber of 10. You would then send back an Invoice with the first LineSequenceNumber of 10')

    edi_buyer_part_number = fields.Char(string='Buyer Part Number',
                              help='Buyer\'s primary product identifier')

    edi_vendor_part_number = fields.Char(string='Vendor Part Number',
                              help='Vendor\'s primary product identifier')

    edi_part_number = fields.Char(string='Part Number',
                              help='Vendor\'s part number. Belongs to the <ProductID> field on the EDI file.')

    edi_qty_cases = fields.Float(string='Qty (Cases)', compute='_compute_qty_cases')

    edi_case_price = fields.Float(string='Case Price', digits='Product Price', compute='_compute_case_price')

    product_uom_id = fields.Many2one(string='EDI UoM', comodel_name='uom.uom', copy=True, store=True)
    edi_ean = fields.Char(string='EAN', related='product_id.edi_ean')
    edi_gtin = fields.Char(string='GTIN', related='product_id.edi_gtin')
    edi_invoice_qty = fields.Float(string='Invoice Quantity', compute='_compute_invoice_qty_values')
    edi_invoice_qty_uom = fields.Char(string='Invoice Quantity UOM', compute='_compute_invoice_qty_values')
    edi_purchase_price = fields.Monetary(string='EDI Purchase Price', compute='_compute_edi_purchase_price')
    edi_pack_size = fields.Float(string='EDI Pack Size', compute='_compute_edi_pack_values')
    edi_tax_type_code = fields.Char(string='EDI Tax Type Code', compute='_compute_edi_tax_values')
    edi_tax_amount = fields.Monetary(string='EDI Tax Amount', compute='_compute_edi_tax_values')

    @api.depends('product_id')
    def _compute_edi_consumer_package_code(self):
        for line in self:
            line.edi_consumer_package_code = line.product_id.edi_consumer_package_code or line.product_id.barcode or ''

    @api.depends('quantity')
    def _compute_qty_cases(self):
        for record in self:
            if record.quantity and record.product_id and record.product_id.packaging_ids and record.product_id.packaging_ids[0].qty:
                record.edi_qty_cases = float(record.quantity / record.product_id.packaging_ids[0].qty)
            else:
                record.edi_qty_cases = record.quantity

    @api.depends('price_unit', 'partner_id', 'product_id')
    def _compute_case_price(self):
        for record in self:
            if record.move_id.move_type == 'out_invoice':
                if record.partner_id.edi_price_in_cases and record.product_id.packaging_ids and record.product_id.packaging_ids[0].qty:
                    record.edi_case_price = record.price_unit * record.product_id.packaging_ids[0].qty
                else:
                    record.edi_case_price = record.price_unit
            else:
                record.edi_case_price = 0

    @api.depends('edi_qty_cases', 'product_uom_id.edi_code', 'quantity')
    def _compute_invoice_qty_values(self):
        for line in self:
            line.edi_invoice_qty = str(float(ceil(line.edi_qty_cases))) if line.product_uom_id.edi_code == 'CA' else line.quantity or 0
            line.edi_invoice_qty_uom = line.product_uom_id.edi_code or 'EA'

    @api.depends('edi_qty_cases', 'partner_id.edi_price_in_cases', 'price_unit')
    def _compute_edi_purchase_price(self):
        for line in self:
            line.edi_purchase_price = line.edi_case_price if line.partner_id.edi_price_in_cases else line.price_unit

    @api.depends('product_id.packaging_ids.qty')
    def _compute_edi_pack_values(self):
        for line in self:
            line.edi_pack_size = line.product_id.packaging_ids[0].qty if line.product_id.packaging_ids else 1

    @api.depends()
    def _compute_edi_tax_values(self):
        for line in self:
            line.edi_tax_type_code = line.tax_ids[0].edi_taxcode if line.tax_ids else 'LS'
            line.edi_tax_amount = line.price_subtotal * sum(line.tax_ids.mapped('amount')) / 100

class AccountTax(models.Model):
    _inherit = 'account.tax'

    edi_taxcode = fields.Char(string='EDI Code', help='Two letter code that will identify the Tax Type on the EDI Invoice.\nBE: Harmonized Sales Tax (HST)\nGS: Goods and Services Tax (GST)')
    edi_line_sequence_number = fields.Char(string='EDI Sequence Number')
    edi_buyer_part_number = fields.Char(string='EDI Buyer Part Number')
    edi_vendor_part_number = fields.Char(string='EDI Vendor Part Number')
    edi_consumer_package_code = fields.Char(string='Consumer Package Code')
    edi_ean = fields.Char(string='EAN')
    edi_gtin = fields.Char(string='GTIN')
    edi_part_number = fields.Char(string='EDI Part Number')
    edi_invoice_qty = fields.Char(string='EDI Invoice Quantity')
    edi_invoice_qty_uom = fields.Char(string='EDI Invoice Quantity UoM')
    edi_purchase_price = fields.Char(string='EDI Purchase Price')
    edi_pack_size = fields.Char(string='EDI Pack Size')
    edi_pack_value = fields.Char(string='EDI Pack Value')
