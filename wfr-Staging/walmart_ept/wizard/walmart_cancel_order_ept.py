import logging

from odoo.exceptions import ValidationError

from odoo import models, fields, _

_logger = logging.getLogger(__name__)

class WalmartCancelOrder(models.TransientModel):
    _name = "walmart.cancel.order.ept"
    _description = "Walmart Cancel Order Wizard"

    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    walmart_cancel_order_line_ids = fields.One2many('walmart.cancel.order.line.ept',
                                                    'walmart_cancel_order_id',
                                                    string="Sale Order Line")

    def action_cancel_order_in_walmart(self):
        """Cancel Oreder In Walmart Process to find the Walmart Order.
            @param None .
            @return: True
            @author: Harshit Trivedi on dated 01-MAR-2019
        """
        walmart_log_obj = self.env['common.log.book.ept']
        walmart_log_lines_obj = self.env['common.log.lines.ept']
        model_id = walmart_log_lines_obj.get_model_id(self._name)
        order_line_number_list = []
        order = self.sale_order_id
        if order.walmart_marketplace_id:
            purchase_order_id = order.walmart_seller_order_ref
            instance_id = order.walmart_marketplace_id
            walmart_conn_obj = instance_id.get_walmart_connection()
            log_book_id = walmart_log_obj.create_common_log_book(
                    model_id=model_id,
                    instance_field='walmart_marketplace_id',
                    instance=instance_id, process_type='export', module='walmart_ept'
            )
            for order_line in self.walmart_cancel_order_line_ids:
                if order_line.product_id.type == 'product':
                    for wline in order_line.walmart_line_number.split(','):
                        order_line_number_list.append(
                                {
                                    "number": wline,
                                })
            if purchase_order_id and order_line_number_list:
                try:
                    response = walmart_conn_obj.orders.cancel(purchase_order_id,
                                                              order_line_number_list)
                    if response.status_code != 200:
                        message = '%d - %s .' % (
                            response.status_code, response.content.decode("utf-8"))

                        walmart_log_lines_obj.create_log_lines(
                                log_book_id=log_book_id,
                                model_id=log_book_id.model_id.id,
                                message=message,
                                res_id=False,
                                order_ref=purchase_order_id
                        )

                    else:
                        json_result = response
                        status = json_result.get("ns4:errors", {}).get("ns4:rror", {}).get(
                                "ns4:severity", "")
                        if status == 'ERROR':
                            message = '%s .' % (json_result)
                            walmart_log_lines_obj.create_log_lines(
                                    log_book_id=log_book_id,
                                    model_id=log_book_id.model_id.id,
                                    message=message,
                                    res_id=False,
                                    order_ref=purchase_order_id
                            )
                except Exception as err:
                    _logger.exception(err)
                    raise ValidationError(_(err))

        return True

class WalmartCancelOrderLine(models.TransientModel):
    _name = "walmart.cancel.order.line.ept"
    _description = "Walmart Cancel Order Line Wizard"

    walmart_cancel_order_id = fields.Many2one("walmart.cancel.order.ept", string="Order Line")
    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float("Quantity", default=1.0)
    walmart_line_number = fields.Integer('Walmart Line No.')
