from odoo.exceptions import ValidationError

from odoo import models, fields, api, _

TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale_refund',
    'in_refund': 'purchase_refund',
}

class WalmartCancelRefundOrderWizard(models.TransientModel):
    _name = "walmart.refund.order.wizard"
    _description = 'Walmart Refund Order Wizard'

    @api.model
    def _default_journal(self):
        """
            This method using for Find Journal And Set the Journal.
            @param No Need Any Parameter.
            @return: Find the Journal and Get back Journal

        """
        inv_type = self._context.get('type', 'out_invoice')
        inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [('type', 'in', list(filter(None, list(map(TYPE2JOURNAL.get, inv_types))))),
                  ('company_id', '=', company_id)]
        return self.env['account.journal'].search(domain, limit=1)

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
             ("incorrectItemReceived", "IncorrectItemReceived"),
             ("cancelledYetShipped", "CancelledYetShipped"),
             ("itemNotReceivedByCustomer", "ItemNotReceivedByCustomer"),
             ("incorrectShippingPrice", "IncorrectShippingPrice"),
             ("damagedItem", "DamagedItem"),
             ("defectiveItem", "DefectiveItem"),
             ("customerChangedMind", "CustomerChangedMind"),
             ("customerReceivedItemLate", "CustomerReceivedItemLate"),
             ("missingPartsInstruction", "Missing Parts / Instructions"),
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

    # walmart_refund_line_ids = fields.One2many("walmart.order.refund.lines.ept", "walmart_refund_id",
    #                                           string="Refund IDS")

    def refund_in_walmart(self):
        """This method used to call the child method to create a refund in the walmart store.
            @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 27/01/2022.
            Task Id : 181522
        """
        common_log_line = self.env['common.log.lines.ept']
        active_id = self._context.get('active_id')
        credit_note_ids = self.env['account.move'].browse(active_id)
        for credit_note_id in credit_note_ids:
            if not credit_note_id.walmart_instance_id:
                continue
            order_lines = credit_note_id.invoice_line_ids.sale_line_ids

            model_id = common_log_line.get_model_id(self._name)
            order_line_lst = []
            instance_id, walmart_conn_obj, purchase_id = self.prepare_order_lines(order_lines, order_line_lst)
            log_book_id = self.env['common.log.book.ept'].create_common_log_book(
                    model_id=model_id,
                    module='walmart_ept',
                    process_type="import",
                    instance=instance_id,
                    instance_field='walmart_marketplace_id'
            )
            self.walmart_refund_process(model_id, order_line_lst, purchase_id, walmart_conn_obj, log_book_id,
                                        common_log_line, order_lines, credit_note_id)
        return True

    def prepare_order_lines(self, order_lines, order_line_lst):
        """
        This method used to prepare order lines.
        """
        for order_line in order_lines:
            instance_id = order_line.order_id.walmart_marketplace_id
            if instance_id:
                walmart_conn_obj = instance_id.get_walmart_connection()
                purchase_id = order_line.order_id.walmart_seller_order_ref or False
                for line in order_line.walmart_order_line_ids:
                    order_line_lst.extend([
                        {"Number": line.line_number,
                         "refunds": {
                             "refund": [
                                 {
                                     "refundReason": self.walmart_refund_reason,
                                     "charge": {
                                         "chargeType": "PRODUCT",
                                         "chargeName": "Item Price",
                                         "chargeAmount": {
                                             "currency": order_line.product_id.currency_id.name,
                                             "amount": str(-(order_line.price_unit + (
                                                     order_line.price_tax / order_line.product_uom_qty)))
                                         },
                                         "tax": {
                                             "taxName": "Item Price Tax",
                                             "taxAmount": {
                                                 "currency": order_line.product_id.currency_id.name,
                                                 "amount": str(-(order_line.price_tax))
                                             }
                                         },
                                     }
                                 }
                             ]
                         }
                         }])
            return instance_id, walmart_conn_obj, purchase_id

    def walmart_refund_process(self, model_id, order_line_lst, purchase_id, walmart_conn_obj, log_book_id,
                               common_log_line, order_lines, credit_note_id):
        if order_line_lst and purchase_id:
            try:
                response = walmart_conn_obj.orders.refund(purchase_id, order_line_lst)
                if response.status_code != 200:
                    message = '%d - %s .' % (
                        response.status_code, response.content.decode("utf-8"))
                    common_log_line.create_log_lines(
                            message=message, model_id=model_id, res_id=False,
                            log_book_id=log_book_id)

                else:
                    json_result = response
                    walmart_order_lines = json_result.get("ns3:order", {}).get(
                            "ns3:orderLines", {}).get("ns3:orderLine", {})
                    for walmart_line in walmart_order_lines:
                        if walmart_line.get("n3:refund", {}):
                            message = "%s." % (walmart_line.get("n3:refund"))
                            common_log_line.create_log_lines(
                                    message=message, model_id=model_id, res_id=False,
                                    log_book_id=log_book_id)

            except Exception as err:
                raise ValidationError(_(err))
        if order_lines.order_id.walmart_marketplace_id.auto_create_refund:
            self.create_refund(credit_note_id)

    def create_refund(self, credit_note_id):
        """
        This method create the refund invoice in Odoo
        :return:
        """
        invoices = credit_note_id.invoice_line_ids.sale_line_ids.order_id.invoice_ids.filtered(
                lambda inv: inv.move_type == 'out_invoice' and inv.state == 'posted')
        if not invoices:
            self.message_post(_("Refund Invoice creation failed due to no\
             invoices found for the selected order in Odoo"))
            return False
        move_reversal = self.env["account.move.reversal"].with_context(
                {"active_model": "account.move", "active_ids": invoices.ids}).create(
                {"refund_method": "refund", "reason": "Refunded in Walmart", "journal_id": self.journal_id.id})
        reversal = move_reversal.reverse_moves()
        reverse_move = self.env['account.move'].browse(reversal['res_id'])
        reverse_move.action_post()
        self.invoice_id = reverse_move.id
        return True
