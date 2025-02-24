from odoo import models, _


class WalmartQueueProcessEpt(models.TransientModel):
    _name = 'walmart.queue.process.ept'
    _description = 'Walmart Queue Process'

    def manual_queue_process(self):
        """
        This method is used to call child methods while manually queue(product, order and customer) process.
        """
        queue_process = self._context.get('queue_process')
        if queue_process == "process_order_queue_manually":
            self.sudo().process_order_queue_manually()

    def process_order_queue_manually(self):
        """This method used to process the customer queue manually. You can call the method from here :
            walmart => Processes => Queues Logs => Orders => Action => Process Queue Manually.
            @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 11/01/2022.
        """
        walmart_order_queue_line_obj = self.env["walmart.order.queue.line.ept"]
        order_queue_ids = self._context.get('active_ids')

        for order_queue_id in order_queue_ids:
            order_queue_line_batch = walmart_order_queue_line_obj.search(
                [("walmart_order_queue_id", "=", order_queue_id),
                 ("state", "in", ('draft', 'failed'))])
            order_queue_line_batch.process_import_order_queue_data()
        return True

    def set_to_completed_queue(self):
        """
        This method used to change the queue(order) state as completed.
        Nikul Alagiya on date 11/01/2022
        """
        queue_process = self._context.get('queue_process')
        if queue_process == "set_to_completed_order_queue":
            self.set_to_completed_order_queue_manually()

    def set_to_completed_order_queue_manually(self):
        """This method used to set order queue as completed. You can call the method from here :
            walmart => Processes => Queues Logs => Orders => SET TO COMPLETED.
            @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 11/01/2022.
        """
        order_queue_ids = self._context.get('active_ids')
        order_queue_ids = self.env['walmart.order.queue.ept'].browse(order_queue_ids)
        for order_queue_id in order_queue_ids:
            queue_lines = order_queue_id.order_data_queue_line_ids.filtered(
                lambda line: line.state in ['draft', 'failed'])
            queue_lines.write({'state': 'cancel'})
            order_queue_id.message_post(
                body=_("Manually set to cancel queue lines %s - ") % (queue_lines.mapped('walmart_order_id')))
        return True

    def marketplace_active_archive(self):
        instances = self.env['walmart.marketplace.ept'].browse(self._context.get('active_ids'))
        for instance in instances:
            instance.walmart_action_archive_unarchive()
        return True
