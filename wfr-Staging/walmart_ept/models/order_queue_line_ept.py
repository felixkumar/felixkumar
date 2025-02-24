import json
import logging
import time

from odoo import models, fields

_logger = logging.getLogger("Walmart Order Queue Line")

class WalmartOrderQueueLineEpt(models.Model):
    _name = "walmart.order.queue.line.ept"
    _description = "Walmart Order Queue Line"

    walmart_order_queue_id = fields.Many2one("walmart.order.queue.ept",
                                             ondelete="cascade")
    walmart_instance_id = fields.Many2one("walmart.marketplace.ept", string="Instance",
                                          help="Order imported from this Walmart Instance.")
    state = fields.Selection([("draft", "Draft"), ("failed", "Failed"), ("done", "Done"),
                              ("cancel", "Cancelled")], default="draft", copy=False)
    walmart_order_id = fields.Char(help="Id of imported order.", copy=False)
    sale_order_id = fields.Many2one("sale.order", copy=False,
                                    help="Order created in Odoo.")
    order_data = fields.Text(help="Data imported from Walmart of current order.", copy=False)

    customer_name = fields.Text(help="Walmart Customer Name", copy=False)

    customer_email = fields.Text(help="Walmart Customer Email", copy=False)

    processed_at = fields.Datetime(help="Shows Date and Time, When the data is processed",
                                   copy=False)
    walmart_order_common_log_lines_ids = fields.One2many("common.log.lines.ept",
                                                         "walmart_order_queue_line_id",
                                                         help="Log lines created against which line.")
    name = fields.Char(help="Order Name")

    def walmart_create_order_queue(self, instance, queue_type, created_by="import"):
        """
        This method is used to create a record of the order queue.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 12/01/2022.
        """
        if queue_type == 'Delivered':
            order_queue_vals = {
                "walmart_instance_id": instance and instance.id or False,
                "created_by": created_by,
                "queue_type": 'WFSOrder' if self.env.context.get('wfs_order') else 'Shipped',
            }
        else:
            order_queue_vals = {
                "walmart_instance_id": instance and instance.id or False,
                "created_by": created_by,
                "queue_type": queue_type,
            }

        return self.env["walmart.order.queue.ept"].create(order_queue_vals)

    def create_order_queue_line(self, order_dict, instance, order_data, order_queue_id):
        """
        Creates order data queue line from order data.
        :param order_dict: The response of order in the dictionary.
        :param instance : Walmart Instance
        :param order_data: The response of order in dump data.
        :param order_queue_id: Record of order queue.
        @author: Nikul Alagiya on Date 12/01/2022.
        """
        order_queue_line_vals = {"walmart_order_id": order_dict.get("customerOrderId", False),
                                 "walmart_instance_id": instance.id,
                                 "order_data": order_data,
                                 "name": order_dict.get("purchaseOrderId", ""),
                                 "customer_email": order_dict.get('customerEmailId', False),
                                 "walmart_order_queue_id": order_queue_id.id}
        return self.create(order_queue_line_vals)

    def create_order_data_queue_line(self, orders_data, instance, queue_type, created_by="import"):
        """
        This method used to create order data queue lines. It creates new queue after 50 order queue lines.
        @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 12/01/2022.
        """
        if isinstance(orders_data, dict):
            orders_data = [orders_data]
        count = 0
        need_to_create_queue = True
        orders_data.reverse()
        order_queue_list = []
        for order in orders_data:
            if need_to_create_queue:
                order_queue = self.walmart_create_order_queue(instance, queue_type, created_by)
                order_queue_list.append(order_queue.id)
                message = "Order Queue %s created." % order_queue.name
                self.generate_simple_notification(message)
                self._cr.commit()
                need_to_create_queue = False
                _logger.info(message)

            data = json.dumps(order)
            self.create_order_queue_line(order, instance, data, order_queue)

            count += 1
            if count == 50:
                count = 0
                need_to_create_queue = True
        if not order_queue.order_data_queue_line_ids:
            order_queue.unlink()
            order_queue_list.remove(order_queue.id)

        return order_queue_list

    def generate_simple_notification(self, message):
        """ This method is used to display simple notification while the opration wizard
            opration running in the backend.
            @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 12/01/2022 .
        """
        bus_bus_obj = self.env["bus.bus"]
        bus_bus_obj._sendone(self.env.user.partner_id, 'simple_notification',
                             {"title": "Walmart Connector",
                              "message": message, "sticky": False, "warning": True})

    def auto_import_order_queue_data(self):
        """
        This method is used to find order queue which queue lines have state in draft and is_action_require is False.
        If cronjob has tried more than 3 times to process any queue then it marks that queue has need process
        to manually. It will be called from auto queue process cron.
        @author: Haresh Mori @Emipro Technologies Pvt.Ltd on date 07/10/2019.
        """
        walmart_order_queue_obj = self.env["walmart.order.queue.ept"]
        order_queue_ids = []

        self.env.cr.execute(
                """update walmart_order_queue_ept set is_process_queue = False where is_process_queue = True""")
        self._cr.commit()

        query = """select queue.id
                from walmart_order_queue_line_ept as queue_line
                inner join walmart_order_queue_ept as queue on queue_line.walmart_order_queue_id = queue.id
                where queue_line.state='draft' and queue.is_action_require = 'False'
                ORDER BY queue_line.create_date ASC"""
        self._cr.execute(query)
        order_queue_list = self._cr.fetchall()
        if not order_queue_list:
            return True

        for result in order_queue_list:
            if result[0] not in order_queue_ids:
                order_queue_ids.append(result[0])

        queues = walmart_order_queue_obj.browse(order_queue_ids)
        self.filter_order_queue_lines_and_post_message(queues)

    def filter_order_queue_lines_and_post_message(self, queues):
        """
        This method is used to post a message if the queue is process more than 3 times otherwise
        it calls the child method to process the order queue line.
        :param queues: Record of the order queues.
        """
        start = time.time()
        order_queue_process_cron_time = queues.walmart_instance_id.get_walmart_cron_execution_time(
                "walmart_ept.process_walmart_order_queue")

        for queue in queues:
            order_data_queue_line_ids = queue.order_data_queue_line_ids.filtered(lambda x: x.state == "draft")

            # For counting the queue crashes and creating schedule activity for the queue.
            queue.queue_process_count += 1
            if queue.queue_process_count > 3:
                queue.is_action_require = True
                note = "<p>Need to process this order queue manually.There are 3 attempts been made by " \
                       "automated action to process this queue,<br/>- Ignore, if this queue is already processed.</p>"
                queue.message_post(body=note)
                continue

            self._cr.commit()
            order_data_queue_line_ids.process_import_order_queue_data()
            if time.time() - start > order_queue_process_cron_time - 60:
                return True

    def process_import_order_queue_data(self):
        """This method processes order queue lines.
        @author: Nikul Alagiya @Emipro Technologies Pvt.Ltd on date 13/01/2022.
        """
        sale_order_obj = self.env["sale.order"]

        queue_id = self.walmart_order_queue_id if len(self.walmart_order_queue_id) == 1 else False
        if queue_id:
            instance = queue_id.walmart_instance_id
            conn_obj = instance.get_walmart_connection()
            if not instance.active:
                _logger.info("Instance %s is not active.", instance.name)
                return True

            queue_id.is_process_queue = True
            sale_order_obj.create_walmart_sale_order(self, instance, conn_obj)
            queue_id.write({'is_process_queue': False})

            # if instance.is_walmart_create_schedule:
            #     queue_id.create_schedule_activity(queue_id)
