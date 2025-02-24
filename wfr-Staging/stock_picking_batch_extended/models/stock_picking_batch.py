# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from threading import Thread
import time
import logging

from odoo import api, fields, models, _, registry, SUPERUSER_ID
from odoo.tests import Form

_logger = logging.getLogger(__name__)


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    parent_batch_id = fields.Many2one('stock.picking.batch', 'Parent Batch')
    process_from_cron = fields.Boolean('Process From Schedule Action?')
    is_pick_batch = fields.Boolean('Is Pick Batch?')
    is_pack_batch = fields.Boolean('Is Pack Batch?')
    is_ship_batch = fields.Boolean('Is Ship Batch?')
    batch_group_id = fields.Many2one('stock.picking.batch.group', 'Batch Group')
    processed_time = fields.Char("Processed Time", compute="compute_restricted_weekdays")
    total_transfer = fields.Integer("Total Transfer", compute="_count_total_transfer", store=True)
    total_done_transfer = fields.Integer("Done Transfer", compute="_count_total_transfer", store=True)

    @api.depends('picking_ids', 'picking_ids.state')
    def _count_total_transfer(self):
        for rec in self:
            rec.total_transfer = len(rec.picking_ids)
            rec.total_done_transfer = len(rec.picking_ids.filtered(lambda l: l.state == 'done'))

    @api.depends("write_date")
    def compute_restricted_weekdays(self):
        for rec in self:
            start = rec.create_date
            end = rec.write_date
            duration = (end - start).total_seconds() / 3600  # Convert seconds to hours
            rec.processed_time = "{} Hours".format(round(duration, 2))

    def action_done(self):
        self = self.with_context(is_batch_process=True)
        res = super(StockPickingBatch, self).action_done()
        return res

    def auto_validate_batch_transfer(self, batch=[]):
        if batch:
            batch_ids = self.browse(batch)
        else:
            batch_ids = self.search([('state', 'not in', ['done', 'cancel']), ('parent_batch_id', '!=', False),
                                     ('parent_batch_id.state', '=', 'done'), ('process_from_cron', '=', True)], limit=3,
                                    order='id asc')
        for batch_id in batch_ids:
            t = Thread(target=self.process_batch_validation_process, args=batch_id)
            t.start()
            if not batch:
                time.sleep(5)
        return True

    def process_batch_validation_process(self, batch_id):
        if not batch_id:
            return False
        if batch_id.state == 'cancel':
            return False
        if batch_id.state == 'draft':
            batch_id.action_confirm()
        wiz = batch_id.action_done()
        if wiz and isinstance(wiz, dict) and wiz.get('res_model', False) == 'stock.immediate.transfer':
            try:
                if 'SHIP' in batch_id.name and batch_id.batch_group_id:
                    batch_id.batch_group_id.state = 'done'
                wiz = Form(self.env['stock.immediate.transfer'].with_context(wiz['context'])).save()
                wiz = wiz.process()
            except Exception as exception:
                _logger.info("stock.immediate.transfer : Error {}".format(exception))
