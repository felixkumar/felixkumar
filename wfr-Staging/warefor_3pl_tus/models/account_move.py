# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import math
from base64 import b64encode
import base64

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError, UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    pallet_id = fields.Many2one(comodel_name="pallet.batch.tus", string="Pallet")
    edi_purchase_order = fields.Char(string='EDI Purchase Order')
    edi_po_date = fields.Date(string='EDI PO Date')
    edi_data_file = fields.Binary('EDI File')
    edi_data_file_name = fields.Char('EDI File Data')
    freight_id = fields.Many2one(comodel_name="freight.freight", string="Logistics Records",
                                 domain=lambda self: [('active', 'in', [False, True])])
    freight_id_obl = fields.Many2one(related="freight_id", string="Logistics Records")
    is_outbound_pl = fields.Boolean(related="freight_id.is_outbound", string="Is Outbound")
    active = fields.Boolean(default=True, help="Set active to false to hide the Account Tag without removing it.")
    asset_category_id = fields.Many2one('account.asset.category', string="Asset Category",
                                        compute='_compute_asset_category')
    amount_residual_signed = fields.Monetary(string='Open Balance', store=True,
                                             compute='_compute_amount', currency_field='company_currency_id')
    company_banking_info = fields.Text(related="partner_id.company_banking_info", string="Company Banking Info")
    company_banking_info_want = fields.Boolean(string="Include or not the Banking Details In Invoice")
    pl_purchase_id = fields.Many2one('purchase.order', string='Purchase Order')
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", compute='_compute_warehouse_id',
                                   readonly=False, store=True)
    logistic_source = fields.Selection([("inbound", "Inbound"), ("outbound", "Outbound")],
                                       compute='_compute_warehouse_id', readonly=False, store=True)
    is_auto_payment_method = fields.Boolean(related="partner_id.is_auto_payment_method", string="Auto Payment Method",
                                            store=True)
    is_online_payment_method = fields.Boolean(related="partner_id.is_online_payment_method",
                                              string="Online Payment Method", store=True)
    is_merged_invoice = fields.Boolean(string="Is Merged Invoice")

    sale_id = fields.Many2one("sale.order", "Sale Order", compute='_compute_origin_so_count', store=True)

    @api.depends('line_ids.sale_line_ids')
    def _compute_origin_so_count(self):
        res = super(AccountMove, self)._compute_origin_so_count()
        for move in self:
            order_id = move.line_ids.sale_line_ids.order_id
            if order_id:
                move.sale_id = order_id[0].id

    # def _compute_pl_purchase_order(self):
    #     for rec in self:
    #         po_ids = rec.line_ids.purchase_line_id.mapped("order_id")
    #         rec.pl_purchase_id = False
    #         if po_ids:
    #             rec.pl_purchase_id = po_ids.sorted()[0]
    @api.depends('freight_id', 'freight_id_obl')
    def _compute_warehouse_id(self):
        for rec in self:
            if rec.freight_id:
                freight_id = rec.freight_id or rec.freight_id_obl
                rec.warehouse_id = freight_id.warehouse_id.id
                rec.logistic_source = 'outbound' if freight_id.is_outbound else 'inbound'

    def action_invoice_print(self):
        # OVERRIDE
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        if any(not move.is_invoice(include_receipts=True) for move in self):
            raise UserError(_("Only invoices could be printed."))

        self.filtered(lambda inv: not inv.is_move_sent).write({'is_move_sent': True})
        return self.env.ref('invoice_template_tus.account_custom_customer_invoice').report_action(self)

    def _compute_asset_category(self):
        """ Method For Compute Asset Category"""
        for rec in self:
            depreciation_line = self.env['account.asset.depreciation.line'].search([('move_id', '=', rec.id)], limit=1)
            rec.asset_category_id = depreciation_line.asset_id.category_id.id

    def write(self, values):
        res = False
        for rec in self:
            state = rec.state == 'cancel' or values.get('state') == 'cancel'
            is_active = 'active' in values
            if not state and is_active and not values.get('active'):
                raise ValidationError('You can archive only canceled Entry!')
        res = super(AccountMove, self).write(values)
        for rec in self:
            if rec.pl_purchase_id:
                rec.pl_purchase_id._compute_invoice()
            if rec.freight_id:
                if rec.id not in rec.freight_id.account_move_ids.ids:
                    rec.freight_id.account_move_ids = [(4, rec.id)]
        return res

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        res.warehouse_id = res.asset_id.warehouse_id.id or res.warehouse_id.id
        return res

    # @api.model
    # def create(self, vals):
    #     if self.env.company.company_code and vals.get('move_type') == 'out_invoice':
    #         name = self.env['ir.sequence'].next_by_code('seq.account.move')
    #         name = "{}-INV{}".format(self.env.company.company_code, name)
    #         _logger.info(name)
    #         vals['name'] = name
    #     return super(AccountMove, self).create(vals)

    def send_edi_document(self):
        filename = 'EDI ' + self.name + '.edi'
        invoice_date = self.invoice_date and self.invoice_date.strftime('%Y%m%d') or ''
        due_date = self.invoice_date_due and self.invoice_date_due.strftime('%Y%m%d') or ''
        edi_po_date = self.edi_po_date and self.edi_po_date.strftime('%Y%m%d') or ''
        partner_id = self.company_id
        term_id = self.invoice_payment_term_id
        partner_shipping_id = self.partner_shipping_id or self.partner_id

        environment = self.env['edi.environment'].search([])
        if environment.mode == 'testing':
            code = 'T'
        else:
            code = 'P'
        if not self.edi_purchase_order:
            raise ValidationError(_('Purchase Number is not set.'))
        if not partner_id.street or partner_id.street2:
            raise ValidationError(_('Address is not set for vendor.'))

        file_data = 'ISA*00*          *00*          *12*8325684100     *01*176766905899   *210722*2245*U*00401*' \
                    '000275626*1*' + code + '*>~' \
                                            'GS*FA*76*6125404455*20040101*2245*274873*X*004010~' \
                                            'ST*810*275607~BIG*' + invoice_date + '*' + self.name + '*' + edi_po_date + '*' + \
                    (str(self.edi_purchase_order) or '') + '~'
        if partner_id:
            file_data = file_data + 'N1*VN*' + (partner_id.name or '') + '*91*~'
        if partner_id.street:
            file_data = file_data + 'N3*' + (partner_id.street or '') + '*' + (partner_id.street2 or '') + '~'
        if partner_id.city or partner_id.state_id or partner_id.country_id or partner_id.zip:
            file_data = file_data + 'N4*' + (partner_id.city or '') + '*' + (partner_id.state_id.code or '') + \
                        '*' + (partner_id.zip or '') + '*' + (partner_id.country_id.code or '') + '~'
        if partner_shipping_id:
            file_data = file_data + 'N1*ST*' + (partner_shipping_id.name or '') + '*91*' + (
                    partner_shipping_id.ref or '') + '~'
        if partner_shipping_id.street:
            file_data = file_data + 'N3*' + (partner_shipping_id.street or '') + '*' + (
                    partner_shipping_id.street2 or '') + '~'
        if partner_shipping_id.city or partner_shipping_id.state_id or partner_shipping_id.country_id \
                or partner_shipping_id.zip:
            file_data = file_data + 'N4*' + (partner_shipping_id.city or '') + '*' + (
                    partner_shipping_id.state_id.code or '') + \
                        '*' + (partner_shipping_id.zip or '') + '*' + (partner_shipping_id.country_id.code or '') + '~'
        payment = self.env['account.payment'].search([('reconciled_invoice_ids', 'in', self.id)])
        if payment[0]:
            payment_partner_id = payment[0].partner_id
            if payment_partner_id:
                file_data = file_data + 'N1*RI*' + (payment_partner_id.name or '') + '*91*' + (
                        payment_partner_id.ref or '') + '~'
            if payment_partner_id.street:
                file_data = file_data + 'N3*' + (payment_partner_id.street or '') + '*' + (
                        payment_partner_id.street or '') + '~'
            if payment_partner_id.city or payment_partner_id.state_id or payment_partner_id.country_id or \
                    payment_partner_id.zip:
                file_data = file_data + 'N4*' + (payment_partner_id.city or '') + '*' + (
                        payment_partner_id.state_id.code or '') + \
                            '*' + (payment_partner_id.zip or '') + '*' + (
                                    payment_partner_id.country_id.code or '') + '~'
        if term_id:
            if invoice_date:
                invoice_date_code = 3
            else:
                ValidationError(_('Please select Invoice Date.'))
            subtotals = self.invoice_line_ids.filtered(lambda x: x.price_subtotal < 0.0)
            subtotal_amt = sum(subtotals.mapped('price_subtotal')) if subtotals else 0
            total_with_discount = int((abs(subtotal_amt) * 100) / self.amount_total)

            # TODO: need to add field in payment term for payment term code

            file_data = file_data + 'ITD*01*' + (str(invoice_date_code) or '') + '*' + (
                    str(round(total_with_discount, 2)) or '') + '*' + (due_date or '') + '*'
            if term_id.line_ids:
                file_data = file_data + (str(term_id.line_ids[0].days) or '') + '**' + (
                        str(term_id.line_ids[0].day_of_the_month) or '') + '~'
            else:
                file_data = file_data + '**~'
        else:
            'ITD*******~'

        for rec in self.invoice_line_ids:
            file_data = file_data + 'IT1*' + (str(rec.sequence) or '') + '*' + (str(
                rec.quantity) or '') + '*' + (rec.product_uom_id.name[:2].upper() or '') + '*' + \
                        (str(rec.price_unit) or '') + '***' + (rec.product_id.name or '') + '**' + (str(
                rec.product_id.default_code) or '') + '**' + \
                        (str(rec.product_id.barcode) or '') + '~PID*F****' + (
                                str(rec.product_id.name or rec.name) or '') + '~'
        file_data = file_data + 'TDS*' + (str(int(round(self.amount_total, 0))) or '') + '*~AMT*GV' + '*' + (
                str(round(self.amount_total, 2)) or '') + '*~CTT*' + (str(len(self.invoice_line_ids)) or '')
        total_segment = file_data.count('~')
        file_data = file_data + '~SE*' + str(total_segment or 1) + '*275607~GE*1*274873~IEA*1*000275626~'

        file_data = file_data.encode('utf-8')
        file = b64encode(file_data)

        self.edi_data_file = file
        self.edi_data_file_name = filename

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """
            Add Default notes from customer's invoice notes.
        """
        result = super(AccountMove, self)._onchange_partner_id()
        if self.partner_id and self.move_type == 'out_invoice' and self.partner_id.default_invoice_text:
            self.narration = self.partner_id.default_invoice_text
        return result

    def action_post(self):
        """
            This method will directly print the invoice While confirming.
        """
        result = super(AccountMove, self).action_post()
        for res in self:
            if res.move_type == 'out_invoice':
                if not res.narration:
                    res._onchange_partner_id()
                action = res.action_invoice_print()
                if action.get('report_name'):
                    report = res.env['ir.actions.report']._get_report_from_name(action.get('report_name'))
                    # filename = "%s.%s" % (report.name, 'pdf')
                    filename = "%s.%s" % (self.name, 'pdf')
                    pdf = report._render_qweb_pdf(action.get('report_name'), res_ids=res.ids)
                    attachment = res.env['ir.attachment'].create({
                        'name': filename,
                        'type': 'binary',
                        'datas': base64.b64encode(pdf[0]),
                        'res_model': 'account.move',
                        'res_id': res.id,
                        'mimetype': 'application/x-pdf'
                    })
                    res.message_post(attachment_ids=[attachment.id])
                    return action
        return result

    def _get_freight_obl_data(self):
        self.ensure_one()
        if self:
            obl_records = self.env['freight.freight'].sudo().search(
                [('account_move_ids', 'in', [self.id]), ('active', 'in', [True, False, ''])])
            vals = {
                'freight_ids': False,
                'order_lines': [],
                'ship_date': '',
            }

            if obl_records:
                ship_date = ''
                ship_dates = obl_records.filtered(lambda x: x.out_date) and list(
                    set(obl_records.filtered(lambda x: x.out_date).mapped('out_date')))
                if ship_dates:
                    if len(ship_dates) >= 1:
                        min_date = min(ship_dates).date()
                        max_date = max(ship_dates).date()
                        if min_date == max_date:
                            ship_date = min_date.strftime('%m/%d/%y')
                        else:
                            ship_date = '%s to %s' % (min_date.strftime('%m/%d/%y'), max_date.strftime('%m/%d/%y'))

                vals.update({
                    'freight_ids': obl_records,
                    'ship_date': ship_date,
                })
                if obl_records.freight_order_line_ids:
                    order_lines = []
                    for line in obl_records.freight_order_line_ids:
                        # if line.lot_id:
                        obl_line = list(filter(
                            lambda order_line: order_line['goods'] == line.goods.id and order_line[
                                'base_cost'] == line.base_cost and order_line['lot_id'] == line.lot_id.id,
                            order_lines)) or []
                        # else:
                        #     obl_line = list(filter(
                        #         lambda order_line: order_line['goods'] == line.goods.id and order_line[
                        #             'base_cost'] == line.base_cost,
                        #         order_lines)) or []
                        if obl_line:
                            product_per_pallet = line.goods.product_per_pallet
                            total_quantity = obl_line[0].get('total_quantity') + line.total_quantity
                            qty = 0
                            if total_quantity > 0:
                                qty = total_quantity
                            if total_quantity > 0 and qty and product_per_pallet:
                                required_pallet = math.ceil(qty / product_per_pallet)
                            else:
                                required_pallet = 0
                            obl_line[0].update({
                                'total_quantity': total_quantity,
                                'required_pallet': required_pallet,
                            })

                        else:
                            order_lines.append({
                                'product_name': line.goods.name,
                                'goods': line.goods.id,
                                'default_code': line.goods.default_code,
                                'required_pallet': line.required_pallet,
                                'base_cost': line.base_cost,
                                'value': line.value,
                                'lot_id': line.lot_id and line.lot_id.id or False,
                                'lot_name': line.lot_id and line.lot_id.name or '',
                                'total_quantity': line.total_quantity or 0,

                            })
                    vals.update({'order_lines': order_lines})
            return vals
        return False

    # def action_invoice_sent(self):
    #     """
    #
    #     :return:
    #     """
    #     res = super(AccountMove, self).action_invoice_sent()
    #     res['context']['custom_layout'] = "remove_email_footer.mail_notification_paynow"
    #     return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    month_qty = fields.Float(string="Monthly Qty", help="Quantity per month")
    cost_uom = fields.Char(string="UOM")
    warehouse_id = fields.Many2one(related='move_id.warehouse_id', string="Warehouse", readonly=False, store=True)
    freight_uom_id = fields.Many2one('uom.uom', string='Bill Unit of Measure', readonly=True)
