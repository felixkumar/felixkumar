from odoo import models, fields

class CommonLogLineEpt(models.Model):
    _inherit = "common.log.lines.ept"

    walmart_order_queue_line_id = fields.Many2one("walmart.order.queue.line.ept",
                                                  "Walmart Order Queue Line")
    walmart_marketplace_id = fields.Many2one("walmart.marketplace.ept", "Marketplace")
