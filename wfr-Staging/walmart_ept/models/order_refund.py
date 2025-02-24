from odoo.exceptions import ValidationError

from odoo import models, fields, api, _

TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale_refund',
    'in_refund': 'purchase_refund',
}

class WalmartOrderRefundLine(models.Model):
    _name = "walmart.order.refund.lines.ept"
    _description = 'walmart.refund.order.lines'

    def get_total(self):
        """
                This method using for the Add Line in Lines.
                @param No Need Any Parameter.
                @return: True

        """
        for record in self:
            total = 0.0
            total = total + (record.order_line_amount * record.product_qty)
            record.total_refund = total

    walmart_line_number = fields.Char(copy=False)
    product_qty = fields.Float(digits="Product UoM")
    price_subtotal = fields.Float(string="Order Line SubTotal",
                                  digits="Price Subtotal")
    order_line_amount = fields.Float(string="Total",
                                     digits="Product Price")
    total_refund = fields.Float(digits="Product Price",
                                compute="get_total")
    price_tax = fields.Float("Tax")
    sale_orderline_id = fields.Many2one("sale.order.line", string="Sale Order Line")
    walmart_refund_id = fields.Many2one("walmart.order.refund.ept", string="Refund ID")
    product_id = fields.Many2one("product.product", string="Odoo Product")

class WalmartOrderRefund(models.Model):
    _name = "walmart.order.refund.ept"
    _description = "Walmart Order Refund"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'order_id'
    _order = "id desc"

    @api.model
    def _default_journal(self):
        """
            This method using for Find Journal And Set the Jounral.
            @param No Need Any Parameter.
            @return: Find the Journal and Get back Jounral

        """
        inv_type = self._context.get('type', 'out_invoice')
        inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [('type', 'in', list(filter(None, list(map(TYPE2JOURNAL.get, inv_types))))),
                  ('company_id', '=', company_id)]
        return self.env['account.journal'].search(domain, limit=1)

    auto_create_picking = fields.Boolean(string="Create Picking", compute="get_picking",
                                         store=False)
    date_ept = fields.Date(string="Date")
    walmart_marketplace_order_ref = fields.Char(string='Walmart MarketplaceOrder Ref',
                                                help='The Customer OrderId')

    order_id = fields.Many2one("sale.order", string="Order Ref")
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 help='You can select here the journal to use for the credit note\
                                  that will be created. If you leave that field empty, it will use \
                                  the same journal as the current invoice.',
                                 default=_default_journal)
    invoice_id = fields.Many2one("account.move", string="Refund")
    instance_id = fields.Many2one('walmart.marketplace.ept', string='Walmart Instance')
    company_id = fields.Many2one("res.company", string="Company")

    walmart_refund_reason = fields.Selection(
            [("billingError", "BillingError"),
             ("taxExemptCustomer", "TaxExemptCustomer"),
             ("itemNotAdvertised", "ItemNotAsAdvertised"),
             ("incorrectItemRecevied", "IncorrectItemReceived"),
             ("cancelledYetShipped", "CancelledYetShipped"),
             ("itemNotReceivedByCustomer", "ItemNotReceivedByCustomer"),
             ("incorrectShippingPrice", "IncorrectShippingPrice"),
             ("damagedItem", "DamagedItem"),
             ("defectiveItem", "DefectiveItem"),
             ("customerChangedMind", "CustomerChangedMind"),
             ("customerReceivedItemLate", "CustomerReceivedItemLate"),
             ("missingPartsInstuction", "Missing Parts / Instructions"),
             ("financeGoodwill", "Finance -> Goodwill"),
             ("financeRollback", "Finance -> Rollback"),
             ("buyerCanceled", "Buyer canceled"),
             ("customerReturnedItem", "Customer returned item"),
             ("generalAdjustment", "General adjustment"),
             ("merchandiseNotReceived", "Merchandise not received"),
             ("qualityMissingPartsInstructions", "Quality -> Missing Parts / Instructions"),
             ("shippingDeliveryDamaged", "Shipping & Delivery -> Damaged"),
             ("shippingDeliveryShippingPriceDiscrepancy",
              "Shipping & Delivery -> Shipping Price Discrepancy"),
             ("others", "Others")
             ], string="Refund Reason", ondelete='cascade')
    walmart_refund_line_ids = fields.One2many("walmart.order.refund.lines.ept", "walmart_refund_id",
                                              string="Refund IDS")

    @api.onchange('order_id')
    def on_change_lines(self):
        """
            This method using for the Add Line in Lines.
            @param None
            @return: True
        """
        walmart_refund_lines_obj = self.env['walmart.order.refund.lines.ept']
        for record in self:
            record.instance_id = record.order_id.walmart_marketplace_id.id
            order = record.order_id
            vals = {}
            new_walmart_retrun_lines = []
            for line in order.order_line:
                for wline in line.walmart_order_line_ids:
                    info = {'product_id': line.product_id.id,
                            'product_qty': 1,
                            'price_subtotal': line.price_unit,
                            'price_tax': line.price_tax / line.product_uom_qty,
                            'order_line_amount': line.price_unit + (
                                    line.price_tax / line.product_uom_qty),
                            "walmart_line_number": wline.line_number}
                    vals.update(info)
                    temp_refund_lines = walmart_refund_lines_obj.new(vals)
                    retvals = walmart_refund_lines_obj._convert_to_write(temp_refund_lines._cache)
                    new_walmart_retrun_lines.append(walmart_refund_lines_obj.create(retvals).id)
            record.company_id = order.warehouse_id.company_id.id
            self.walmart_refund_line_ids = walmart_refund_lines_obj.browse(
                    new_walmart_retrun_lines)

    def refund_order_in_walmart(self):
        """
        This method is used to create a refund at walmart and also creates the refund invoice
        in Odoo
        :return:
        """
        # Fixme: Shipping Line refund is not implemented due to improper data
        model_id = self.env['common.log.lines.ept'].get_model_id(self._name)
        for record in self.filtered(lambda x: x.order_id.state == 'sale'):
            instance_id = record.instance_id
            if instance_id:
                log_book_id = self.env['common.log.book.ept'].create_common_log_book(
                        model_id=model_id,
                        module='walmart_ept',
                        process_type="import",
                        instance=instance_id,
                        instance_field='walmart_marketplace_id'
                )
                walmart_conn_obj = instance_id.get_walmart_connection()
                purchase_id = record.order_id.walmart_seller_order_ref or False
                order_line_lst = []
                for line in record.walmart_refund_line_ids:
                    message = False
                    if line.total_refund <= 0.0:
                        message = "Invalid line for %s product" % (line.product_id.name)
                    elif line.product_qty <= 0.0:
                        message = "Invalid Qty for %s product" % (line.product_id.name)
                    if message:
                        raise ValidationError(_(message))
                    order_line_lst.extend([
                        {"Number": line.walmart_line_number,
                         "refunds": {
                             "refund": [
                                 {
                                     "refundReason": record.walmart_refund_reason,
                                     "charge": {
                                         "chargeType": "PRODUCT",
                                         "chargeName": "Item Price",
                                         "chargeAmount": {
                                             "currency": line.product_id.currency_id.name,
                                             "amount": str(-(line.order_line_amount))
                                         },
                                         "tax": {
                                             "taxName": "Item Price Tax",
                                             "taxAmount": {
                                                 "currency": line.product_id.currency_id.name,
                                                 "amount": str(-(line.price_tax))
                                             }
                                         },
                                     }
                                 }
                             ]
                         }
                         }])
                if order_line_lst and purchase_id:
                    try:
                        response = walmart_conn_obj.orders.refund(purchase_id, order_line_lst)
                        if response.status_code != 200:
                            message = '%d - %s .' % (
                                response.status_code, response.content.decode("utf-8"))
                            self.env['common.log.lines.ept'].create_log_lines(
                                    message=message, model_id=model_id, res_id=False,
                                    log_book_id=log_book_id)

                        else:
                            json_result = response
                            walmart_order_lines = json_result.get("ns3:order", {}).get(
                                    "ns3:orderLines", {}).get("ns3:orderLine", {})
                            if walmart_order_lines:
                                for walmart_line in walmart_order_lines:
                                    if walmart_line.get("n3:refund", {}):
                                        message = "%s." % (walmart_line.get("n3:refund"))
                                        self.env['common.log.lines.ept'].create_log_lines(
                                                message=message, model_id=model_id, res_id=False,
                                                log_book_id=log_book_id)

                    except Exception as err:
                        raise ValidationError(_(err))

                if record.instance_id.auto_create_refund:
                    self.create_refund()

        return True

    def create_refund(self):
        """
        This method create the refund invoice in Odoo
        :return:
        """
        invoices = self.order_id.invoice_ids.filtered(
                lambda inv: inv.move_type == 'out_invoice' and inv.state == 'posted')
        if not invoices:
            self.message_post(_("Refund Invoice creation failed due to no\
             invoices found for the selected order in Odoo"))
            return False
        move_reversal = self.env["account.move.reversal"].with_context(
                {"active_model": "account.move", "active_ids": invoices.ids}).create(
                {"refund_method": "refund", "reason": "Refunded in Walmart"})
        reversal = move_reversal.reverse_moves()
        reverse_move = self.env['account.move'].browse(reversal['res_id'])
        reverse_move.action_post()
        self.invoice_id = reverse_move.id
        return True
