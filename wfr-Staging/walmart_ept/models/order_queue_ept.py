import logging
import time
from datetime import datetime, timedelta

import pytz
from odoo.exceptions import UserError

from odoo import models, fields, api

utc = pytz.utc

_logger = logging.getLogger("Walmart Order Queue")

class WalmartOrderQueueEpt(models.Model):
    _name = "walmart.order.queue.ept"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Walmart Order Data Queue"

    name = fields.Char(help="Sequential name of imported order.", copy=False)
    walmart_instance_id = fields.Many2one('walmart.marketplace.ept', string='Instance',
                                          help="Order imported from this Walmart Instance.")
    state = fields.Selection([('draft', 'Draft'), ('partially_completed', 'Partially Completed'),
                              ('completed', 'Completed'), ('failed', 'Failed')], tracking=True,
                             default='draft', copy=False, compute="_compute_queue_state",
                             store=True)
    # walmart_order_common_log_book_id = fields.Many2one("common.log.book.ept", help="""Related Log book which has
    #                                                                 all logs for current queue.""")
    walmart_order_common_log_lines_ids = fields.One2many(comodel_name="common.log.lines.ept",
                                                         compute="_compute_log_lines")

    order_data_queue_line_ids = fields.One2many("walmart.order.queue.line.ept",
                                                "walmart_order_queue_id")
    order_queue_line_total_record = fields.Integer(string='Total Records',
                                                   compute='_compute_order_queue_line_record')
    order_queue_line_draft_record = fields.Integer(string='Draft Records',
                                                   compute='_compute_order_queue_line_record')
    order_queue_line_fail_record = fields.Integer(string='Fail Records',
                                                  compute='_compute_order_queue_line_record')
    order_queue_line_done_record = fields.Integer(string='Done Records',
                                                  compute='_compute_order_queue_line_record')

    order_queue_line_cancel_record = fields.Integer(string='Cancel Records',
                                                    compute='_compute_order_queue_line_record')
    created_by = fields.Selection([("import", "By Manually Import Process"),
                                   ("scheduled_action", "By Scheduled Action")],
                                  help="Identify the process that generated a queue.", default="import")
    is_process_queue = fields.Boolean('Is Processing Queue', default=False)
    running_status = fields.Char(default="Running...")
    queue_process_count = fields.Integer(string="Queue Process Times",
                                         help="it is used know queue how many time processed")
    is_action_require = fields.Boolean(default=False, help="it is used  to find the action require queue")
    queue_type = fields.Selection([("Shipped", "Shipped Order Queue"), ("Created", "Released Order Queue"), ("WFSOrder", "WFS Order Queue")],
                                  help="Identify to queue for which type of order import.")

    @api.model_create_multi
    def create(self, vals_list):
        """This method used to create a sequence for Order Queue Data.
            @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 12/01/2022.
        """
        for vals in vals_list:
            sequence_id = self.env.ref('walmart_ept.seq_walmart_order_queue_data').ids
            if sequence_id:
                record_name = self.env['ir.sequence'].browse(sequence_id).next_by_id()
            else:
                record_name = '/'
            vals.update({'name': record_name or ''})
        return super(WalmartOrderQueueEpt, self).create(vals_list)

    @api.model
    def retrieve_dashboard(self, *args, **kwargs):
        dashboard = self.env['queue.line.dashboard']
        return dashboard.get_data(table='walmart.order.queue.line.ept')

    @api.depends('order_data_queue_line_ids.state')
    def _compute_order_queue_line_record(self):
        """This is used for the count of total records of order queue lines
            and display the count records in the form view order data queue.
            @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 11/01/2022.
        """
        for order_queue in self:
            queue_lines = order_queue.order_data_queue_line_ids
            order_queue.order_queue_line_total_record = len(queue_lines)
            order_queue.order_queue_line_draft_record = len(queue_lines.filtered(lambda x: x.state == "draft"))
            order_queue.order_queue_line_done_record = len(queue_lines.filtered(lambda x: x.state == "done"))
            order_queue.order_queue_line_fail_record = len(queue_lines.filtered(lambda x: x.state == "failed"))
            order_queue.order_queue_line_cancel_record = len(queue_lines.filtered(lambda x: x.state == "cancel"))

    @api.depends('order_data_queue_line_ids')
    def _compute_log_lines(self):
        self.walmart_order_common_log_lines_ids = False
        for rec in self:
            log_lines = rec.mapped('order_data_queue_line_ids.walmart_order_common_log_lines_ids')
            rec.walmart_order_common_log_lines_ids = log_lines

    def walmart_create_order_queues(self, instance, start_date, end_date, order_status, created_by="import", order_type=''):

        """
            This method is used to call walmart API for importing orders,
            If Last Sync Time is available then system will take those orders
            after last import time till the current time.Otherwise, System will
            take last 30 days orders.
            @param: Instance , Start/End Date, Order Status
            @return: True

            """
        if not start_date:
            if instance.last_sync_released_order_date:
                start_date = (instance.last_sync_released_order_date - timedelta(days=30))
                end_date = datetime.now()
            else:
                today = datetime.now()
                start_date = (today - timedelta(days=30))
                end_date = today
        conn_obj = instance.get_walmart_connection()

        order_data_queue_line_obj = self.env["walmart.order.queue.line.ept"]
        walmart_log_line_obj = self.env["common.log.lines.ept"]
        start = time.time()
        order_queues = []
        _logger.info("Importing Released Orders from Walmart for Dates %s to %s...", start_date,
                     end_date)
        ship_node_type = ""
        if order_type == 'wfs_order':
            ship_node_type = "WFSFulfilled"
        response = self.walmart_order_request(conn_obj, start_date, end_date, order_status, ship_node_type)

        orders_data = response.get('list', {}).get('elements', {}).get('order', [])
        if not orders_data:
            message = "Released Orders are not found between {} and {}.".format(start_date,
                                                                                end_date)
            _logger.info(message)
            walmart_log_line_obj.create_common_log_line_ept(message=message, module='walmart_ept',
                                                            model_name=self._name,
                                                            walmart_marketplace_id=instance.id,
                                                            log_line_type='fail', mismatch_details=False,
                                                            operation_type="import")
        else:
            order_queues = order_data_queue_line_obj.create_order_data_queue_line(orders_data,
                                                                                  instance,
                                                                                  order_status,
                                                                                  created_by)

            # more than 200 orders
            next_cursor = isinstance(response, dict) and \
                          response.get('list', {}).get('meta', {}).get('nextCursor', '')
            if next_cursor:
                order_queue_list = self.list_all_walmart_orders(instance, conn_obj, order_status, next_cursor)
                order_queues = order_queues + order_queue_list
        instance.last_sync_released_order_date = end_date
        end = time.time()
        _logger.info("Imported Orders in %s seconds.", str(end - start))

        return order_queues

    def walmart_order_request(self, conn_obj, from_date, to_date, order_status, ship_node_type):
        """ This method used to pull the orders from Walmart Store to Odoo.
            :param order_type: Which type of orders pull from Walmart to Odoo.
            Generally, they have two values 1) shipped 2) unshipped
            @return:order_ids
            @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 12/01/2022 .
        """
        start_date, end_date = self.convert_dates_by_timezone(from_date, to_date)
        try:
            response = conn_obj.orders.all(status=order_status, createdStartDate=start_date,
                                           createdEndDate=end_date,
                                           limit=100, shipNodeType=ship_node_type)
        except Exception as error:
            raise UserError(error)

        return response

    def list_all_walmart_orders(self, instance, conn_obj, order_status, next_cursor):
        order_data_queue_line_obj = self.env["walmart.order.queue.line.ept"]
        order_queue_list, cursors = [], []
        while next_cursor:
            response = conn_obj.orders.all(nextCursor=next_cursor, order_status=order_status, limit=100)
            _logger.info("Next cursor")
            _logger.info(next_cursor)
            if response and next_cursor not in cursors:
                orders_data = response.get('list', {}).get('elements', {}).get('order', [])
                next_cursor = response.get('list', {}).get('meta', {}).get('nextCursor', '')
                cursors.append(next_cursor)
                order_queues = order_data_queue_line_obj.create_order_data_queue_line(orders_data,
                                                                                      instance,
                                                                                      order_status)
                order_queue_list += order_queues
            else:
                break
        return order_queue_list

    def convert_dates_by_timezone(self, from_date, to_date):
        """
        This method converts the dates by timezone of the to import orders.
        @param from_date: From date for importing orders.
        @param to_date: To date for importing orders.
        @author: Nikul Alagiya on Date 12/01/2022.
        """
        from_date = pytz.utc.localize(from_date).astimezone(pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
        to_date = pytz.utc.localize(to_date).astimezone(pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
        return from_date, to_date

    @api.depends('order_data_queue_line_ids.state')
    def _compute_queue_state(self):
        """
        Computes state from different states of queue lines.
        @author: Nikul Alagiya on Date 13/01/2022.
        """
        for record in self:
            if record.order_queue_line_total_record == record.order_queue_line_done_record + \
                    record.order_queue_line_cancel_record:
                record.state = "completed"
            elif record.order_queue_line_draft_record == record.order_queue_line_total_record:
                record.state = "draft"
            elif record.order_queue_line_total_record == record.order_queue_line_fail_record:
                record.state = "failed"
            else:
                record.state = "partially_completed"

    def import_order_cron_action(self, ctx=False):
        """This method is used to import orders from the auto-import cron job.
        """
        if isinstance(ctx, dict):
            instance_id = ctx.get('walmart_instance_id')
            instance = self.env['walmart.marketplace.ept'].browse(instance_id)
            to_date = datetime.now()
            from_date = to_date - timedelta(3)
            self.walmart_create_order_queues(instance, from_date, to_date,'Created', created_by="scheduled_action", order_type='')
        return True

    def import_wfs_order_cron_action(self, ctx=False):
        """This method is used to import orders from the auto-import cron job.
        """
        if isinstance(ctx, dict):
            instance_id = ctx.get('walmart_instance_id')
            instance = self.env['walmart.marketplace.ept'].browse(instance_id)
            to_date = datetime.now()
            from_date = to_date - timedelta(3)
            self.walmart_create_order_queues(instance, from_date, to_date,'Delivered', created_by="scheduled_action", order_type='wfs_order')
        return True
